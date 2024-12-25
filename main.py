from fastapi import FastAPI

# from src.tags.routers import tag_router
from src.auth.routers import router as auth_router

app = FastAPI()

# app.include_router(tag_router, prefix='/tags', tags=['tags'])
app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/ping")
async def ping():
    return {"ping": "pong"}

