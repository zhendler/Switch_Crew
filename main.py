from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles 
import logging

from src.photos.routers import photo_router
from src.tags.routers import tag_router
from src.comments.routers import router as comment_router
from src.auth.routers import router as auth_router
from src.user_profile.routers import router as user_router
from src.auth.utils import BANNED_CHECK


app = FastAPI()
logger = logging.getLogger("uvicorn")


app.include_router(tag_router, prefix='/tags', tags=['tags'], dependencies=BANNED_CHECK)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(photo_router, prefix="/photos", tags=["photos"])
app.include_router(comment_router, prefix="/comments", tags=["comments"])
# app.include_router(web_router, prefix="/web", tags=["web"], include_in_schema=False)

app.mount("/static", StaticFiles(directory="static"), name="static")