import os
from sys import prefix

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
app.include_router(photo_router, prefix="/photos", tags=["photos"])
app.include_router(comment_router, prefix="/comments", tags=["comments"])
app.include_router(
    user_router,
    prefix="/user_profile",
    tags=["user_profile"],
)
app.include_router(web_router, prefix="")
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


