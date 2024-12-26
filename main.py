from fastapi import FastAPI

from src.tags.routers import tag_router
from src.auth.routers import router as auth_router
from src.comments.routers import router as comment_router

app = FastAPI()

app.include_router(tag_router, prefix='/tags', tags=['tags'])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(comment_router, prefix="/comments", tags=["comments"])



@app.get("/ping")
async def ping():
    return {"ping": "pong"}

