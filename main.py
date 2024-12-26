from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from src.tags.routers import tag_router
from src.photos.routers import photo_router
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
# from src.auth.routers import router as auth_router

app = FastAPI()

app.include_router(tag_router, prefix='/tags', tags=['tags'])
app.include_router(photo_router, prefix='/photos', tags=['photo'])
# app.include_router(auth_router, prefix="/auth", tags=["auth"])

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Передаем данные в шаблон
    return templates.TemplateResponse("index.html", {"request": request, "title": "Home Page"})

