from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from src.tags.routers import tag_router
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.auth.routers import router as auth_router
import logging
app = FastAPI()
logger = logging.getLogger("uvicorn")
app.include_router(tag_router, prefix='/tags', tags=['tags'])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.get("/", response_class=HTMLResponse)
async def read_root( request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



