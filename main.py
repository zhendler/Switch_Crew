from src.photos.routers import photo_router
from fastapi import FastAPI
from src.tags.routers import tag_router
from src.comments.routers import router as comment_router
from src.auth.routers import router as auth_router
from src.web.routers import router as web_router
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.include_router(tag_router, prefix='/tags', tags=['tags'])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(photo_router, prefix="/photos", tags=["photos"])
app.include_router(comment_router, prefix="/comments", tags=["comments"])
# app.include_router(web_router, prefix="/web", tags=["web"], include_in_schema=False)

app.mount("/static", StaticFiles(directory="static"), name="static")
