import os
from datetime import datetime

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import get_db
from src.auth.repos import UserRepository
from src.photos.repos import PhotoRepository
from src.reactions.routers import reaction_router
from src.subscription.repos import SubscriptionRepository
from src.tags.repos import TagRepository
from src.tags.routers import tag_router
from src.comments.routers import router as comment_router
from src.auth.routers import router as auth_router
from src.auth.utils import BANNED_CHECK, ACTIV_AND_BANNED, get_current_user_cookies
from src.photos.routers import photo_router, mainrouter
from src.user_profile.repos import UserProfileRepository
from src.user_profile.routers import router as user_router
from src.utils.front_end_utils import truncatechars, format_datetime
from src.subscription.routers import router as subscription_router

app = FastAPI()

# app.include_router(tag_router, prefix="/tags", tags=["tags"], dependencies=BANNED_CHECK)
# app.include_router(auth_router, prefix="/auth", tags=["auth"])
# app.include_router(
#     photo_router, prefix="/photos", tags=["photos"], dependencies=BANNED_CHECK
# )
# app.include_router(
#     comment_router, prefix="/comments", tags=["comments"], dependencies=ACTIV_AND_BANNED
# )
# app.include_router(
#     user_router,
#     prefix="/user_profile",
#     tags=["user_profile"],
#     dependencies=BANNED_CHECK,
# )
# app.include_router(web_router, prefix="")

app.include_router(tag_router, prefix="/tags", tags=["tags"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(photo_router, prefix="/photos", tags=["photos"])
app.include_router(comment_router, prefix="/comments", tags=["comments"])
app.include_router(
    user_router,
    prefix="/user_profile",
    tags=["user_profile"],
)
app.include_router(reaction_router, prefix="/reaction", tags=["reactions"])
app.include_router(subscription_router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(mainrouter, prefix="")
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


templates = Jinja2Templates(directory="templates")
templates.env.filters["truncatechars"] = truncatechars


@app.get('/search/')
async def search(
    request: Request,
    query: str,
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserProfileRepository(db)
    tag_repo = TagRepository(db)

    query = query.strip()

    tags = await tag_repo.search_tags(query)
    searched_users = await user_repo.search_users(query)

    user = await get_current_user_cookies(request, db)
    return templates.TemplateResponse(
        "/main/search.html",
        {
            "request": request,
            "user": user,
            "query": query,
            "searched_users": searched_users,
            "tags": tags,
        },
    )


@app.get("/page/{username}")
async def page(request: Request,
               username: str,
               db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    photo_repo = PhotoRepository(db)

    user_page = await user_repo.get_user_by_username(username)
    user = await get_current_user_cookies(request, db)

    date_obj = datetime.fromisoformat(str(user_page.created_at))
    date_of_registration = date_obj.strftime("%Y-%m-%d")

    photos = await photo_repo.get_users_all_photos(user_page)
    amount_of_photos = len(photos)

    detail = request.query_params.get("detail")

    sub_repo = SubscriptionRepository(db)
    if user:
        subscribe = await sub_repo.check_is_subscribed(user.id, user_page.id)
    else:
        subscribe = False

    amount_of_subscribes = await sub_repo.amount_of_subscribes(user_page.id)

    return templates.TemplateResponse(
        "/user/page.html",
        {
            "request": request,
            "user_page": user_page,
            "user": user,
            "photos": photos,
            "Date_reg": date_of_registration,
            "amount_of_photos": amount_of_photos,
            "detail": detail,
            "subscribe": subscribe,
            "amount_of_subscribes": amount_of_subscribes,
        },
    )