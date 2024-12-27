from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from src.tags.routers import tag_router, get_user
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.auth.routers import router as auth_router
from fastapi.security import OAuth2PasswordBearer
app = FastAPI()

app.include_router(tag_router, prefix='/tags', tags=['tags'])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/ping")
async def ping():
    return {"ping": "pong"}

@app.get("/", response_class=HTMLResponse)
async def read_root( request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



