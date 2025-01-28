import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.tags.routers import tag_router
from src.comments.routers import router as comment_router
from src.auth.routers import router as auth_router
from src.auth.utils import BANNED_CHECK, ACTIV_AND_BANNED
from src.photos.routers import photo_router, mainrouter
from src.user_profile.routers import router as user_router
from src.web.routers import router as web_router

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
app.include_router(mainrouter, prefix="")
app.include_router(tag_router, prefix="/tags", tags=["tags"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(
    photo_router, prefix="/photos", tags=["photos"]
)
app.include_router(
    comment_router, prefix="/comments", tags=["comments"]
)
app.include_router(
    user_router,
    prefix="/user_profile",
    tags=["user_profile"],
)
app.include_router(web_router, prefix="")
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


# templates = Jinja2Templates(directory="templates")
# @app.get('/search/')
# async def search(
#     request: Request,
#     query: str,
#     db: AsyncSession = Depends(get_db),
# ):
#     user_repo = UserProfileRepository(db)
#     tag_repo = TagRepository(db)
#
#     tags = await tag_repo.search_tags(query)
#     searched_users = await user_repo.search_users(query)
#
#     user = await get_current_user_cookies(request, db)
#     return templates.TemplateResponse(
#             "/main/search.html",
#             {"request": request,
#             "user": user,
#             'query': query,
#             'searched_users': searched_users,
#              'tags': tags}
#         )
