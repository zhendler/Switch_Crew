from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, status, File, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from jinja2 import Environment, FileSystemLoader

from src.models.models import User
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
    decode_verification_token, get_current_user,
)
from src.models.models import User

router = APIRouter()
env = Environment(loader=FileSystemLoader("src/templates"))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,)
async def register(
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    avatar: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),

):
    """
        Register a new user.

        Args:
            background_tasks (BackgroundTasks): Background task manager for sending verification email.
            username (str): The username of the new user.
            email (str): The email of the new user.
            password (str): The password of the new user.
            avatar (UploadFile, optional): The avatar file for the new user.
            db (AsyncSession): Database session dependency.

        Returns:
            UserResponse: Details of the newly created user along with a verification message.
        """
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(email)
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already register")
    user_create = UserCreate(username=username, email=email, password=password, avatar=avatar)
    user = await user_repo.create_user(user_create)
    if avatar:
        avatar_url = await user_repo.upload_to_cloudinary(avatar)
        await user_repo.update_avatar(user.email, avatar_url)
    verification_token = create_verification_token(user.email)
    verification_link = (f"http://localhost:8000/auth/verify-email?token={verification_token}")
    template = env.get_template("email.html")
    email_body = template.render(verification_link=verification_link)
    background_tasks.add_task(send_verification_grid, user.email, email_body)
    return UserResponse(
        username=user.username,
        email=user.email,
        id=user.id,
        avatar_url=user.avatar_url,
        detail=f"Please verify your email address. A verification link has been sent to your email."
    )

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
    return {"detail": "Email verified successfully"}


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
    verification_link = f"http://localhost:8000/auth/verify-email?token={verification_token}"
    template = env.get_template("email.html")
    email_body = template.render(verification_link=verification_link)
    background_tasks.add_task(send_verification_grid, user.email, email_body)
    return {"detail": "A new verification email has been sent. Please check your inbox."}


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate a user and issue access and refresh tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): Form containing the user's username and password.
        db (AsyncSession): Database session dependency.

    Returns:
        Token: The access and refresh tokens along with their type.
    """
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
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


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
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.get("/forgot-password")
async def forgot_password(
        email: str,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    reset_token = create_verification_token(user.email)
    reset_link = f"http://localhost:8000/auth/reset-password?token={reset_token}"
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
                detail="Invalid or expired token"
            )
        template = env.get_template("reset_password_form.html")
        html_content = template.render(token=token)
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/reset-password")
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
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
                detail="Invalid or expired token"
            )
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        hashed_password = get_password_hash(new_password)
        await user_repo.update_user_password(user, hashed_password)
        return {"detail": "Password reset successful!"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )