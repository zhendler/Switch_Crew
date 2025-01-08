from src.photos.routers import photo_router
from fastapi import FastAPI
from src.tags.routers import tag_router
from src.comments.routers import router as comment_router
from src.auth.routers import router as auth_router

from src.user_profile.routers import router as user_router
from src.auth.utils import BANNED_CHECK, ACTIV_AND_BANNED


from src.web.routers import router as web_router
from fastapi.staticfiles import StaticFiles
import os


app = FastAPI()

app.include_router(tag_router, prefix='/tags', tags=['tags'], dependencies=BANNED_CHECK)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(photo_router, prefix="/photos", tags=["photos"], dependencies=BANNED_CHECK)
app.include_router(comment_router, prefix="/comments", tags=["comments"], dependencies=ACTIV_AND_BANNED)
app.include_router(user_router, prefix="/user_profile", tags=["user_profile"], dependencies=BANNED_CHECK)
app.include_router(web_router, prefix="/web", tags=["web"])

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")
