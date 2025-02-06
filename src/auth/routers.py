"""
This module provides a set of endpoints for user authentication and account management,
including user registration, email verification, login, token refresh, password reset,
and email resending functionalities. Each endpoint is designed to work asynchronously with FastAPI.
Dependencies include:
- FastAPI components for handling requests, forms, file uploads, and dependencies.
- SQLAlchemy for async database interactions.
- Jinja2 for rendering email templates.
- Utilities for password hashing, token generation, and email sending.
"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    UploadFile,
    status,
    Request,
    File,
    Form,
    Depends,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Environment, FileSystemLoader

from config.db import get_db
from src.auth.repos import UserRepository
from src.auth.schemas import UserCreate, UserResponse, Token
from src.auth.mail_utils import send_verification_grid
from src.auth.pass_utils import verify_password, get_password_hash
from src.auth.utils import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    create_verification_token,
    decode_verification_token,
    get_current_user_cookies,
)
from src.utils.front_end_utils import get_response_format


router = APIRouter()
env = Environment(loader=FileSystemLoader("src/templates"))
templates = Jinja2Templates(directory="templates")


@router.get(
    "/register_page",
    status_code=status.HTTP_200_OK,
)
async def register_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_cookies(request, db)
    if user is None:
        return templates.TemplateResponse(
            "/authentication/register.html", {"request": request, "user": user}
        )
    else:
        return templates.TemplateResponse(
            "index.html", {"request": request, "user": user}
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    avatar: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    response_format: str = Depends(get_response_format),
):
    """
    Register a new user.

    Args:
        request (Request): The HTTP request object.
        background_tasks (BackgroundTasks): Background task manager for sending verification email.
        username (str): The username of the new user.
        email (str): The email of the new user.
        password (str): The password of the new user.
        avatar (UploadFile, optional): The avatar file for the new user.
        db (AsyncSession): Database session dependency.
        response_format (str): The format of the response (JSON or HTML).

    Returns:
        UserResponse: A JSON response containing the new user's details if `response_format` is "json".
        TemplateResponse: An HTML template response with the verification link if `response_format` is "html".
    """
    user = await get_current_user_cookies(request, db)
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already register"
        )
    user_create = UserCreate(
        username=username, email=email, password=password, avatar=avatar
    )
    user = await user_repo.create_user(user_create)
    if avatar:
        avatar_url = await user_repo.upload_to_cloudinary(avatar)
        await user_repo.update_avatar(user.email, avatar_url)
    else:
        avatar_url = None
    verification_token = create_verification_token(user.email)
    verification_link = f"https://localhost:8000/auth/verify-email?token={verification_token}"
    template = env.get_template("email.html")
    email_body = template.render(verification_link=verification_link)
    background_tasks.add_task(send_verification_grid, user.email, email_body)
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    if response_format == "json":
        return UserResponse(
            username=user.username,
            email=user.email,
            id=user.id,
            avatar_url=user.avatar_url,
            detail=f"Please verify your email address. A verification link has been sent to your email.",
        )
    else:
        return response


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify a user's email using a token.

    Args:
        token (str): The verification token sent to the user's email.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Success message upon successful email verification.
    """
    email: str = decode_verification_token(token)
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await user_repo.activate_user(user)

    detail = "Email verified successfully"
    return RedirectResponse(f"/page/{user.username}?detail={detail}", status_code=302)



@router.post("/resend-verifi-email", status_code=status.HTTP_200_OK)
async def resend_verifi_email(
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Resend the email verification link to the user.

    Args:
        background_tasks (BackgroundTasks): Background task manager for sending verification email.
        email (str): The email address of the user to resend the verification link to.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Confirmation message indicating the email has been sent.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist.",
        )
    verification_token = create_verification_token(user.email)
    verification_link = f"http://127.0.0.1:8000/auth/verify-email?token={verification_token}"
    template = env.get_template("email.html")
    email_body = template.render(verification_link=verification_link)
    background_tasks.add_task(send_verification_grid, user.email, email_body)

    detail = "A new verification email has been sent. Please check your inbox."
    return RedirectResponse(f"/page/{user.username}?detail={detail}", status_code=302)


@router.get("/login_page", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "/authentication/login.html", {"request": request}
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    response_format: str = Depends(get_response_format),
):
    """
    Authenticate a user and issue access and refresh tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): Form containing the user's username and password.
        db (AsyncSession): Database session dependency.

    Returns:
        Token: The access and refresh tokens along with their type.
    """
    user = await get_current_user_cookies(request, db)
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    if response_format == "json":
        return Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )
    else:
        return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token", httponly=True)
    response.delete_cookie(key="refresh_token", httponly=True)
    return response


@router.post("/refresh_token", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access and refresh tokens using a valid refresh token.

    Args:
        refresh_token (str): The user's current refresh token.
        db (AsyncSession): Database session dependency.

    Returns:
        Token: The new access and refresh tokens along with their type.
    """
    token_data = decode_access_token(refresh_token)
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_username(token_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    return Token(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


@router.get("/forgot-password")
async def forgot_password(
    email: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """
    Send a password reset email to the user.

    Args:
        email (str): The email address of the user requesting the password reset.
        background_tasks (BackgroundTasks): Background task manager for sending the reset email.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Confirmation message indicating the reset email has been sent.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    reset_token = create_verification_token(user.email)
    reset_link = f"https://localhost:8000/auth/reset-password?token={reset_token}"
    template = env.get_template("reset_password_email.html")
    email_body = template.render(reset_link=reset_link)
    background_tasks.add_task(send_verification_grid, user.email, email_body)
    return {"detail": "Password reset email sent"}


@router.get("/reset-password")
async def reset_password_form(token: str):
    """
    Render the password reset form.

    Args:
        token (str): The password reset token.

    Returns:
        HTMLResponse: The HTML content for the password reset form.
    """
    try:
        email = decode_verification_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )
        template = env.get_template("reset_password_form.html")
        html_content = template.render(token=token)
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password")
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset the user's password.

    Args:
        token (str): The password reset token.
        new_password (str): The new password for the user.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: Success message indicating the password has been reset.
    """
    try:
        email = decode_verification_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token",
            )
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        hashed_password = get_password_hash(new_password)
        await user_repo.update_user_password(user, hashed_password)
        return {"detail": "Password reset successful!"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
