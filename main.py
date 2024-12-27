from src.photos.routers import photo_router
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from src.tags.routers import tag_router, get_user
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.comments.routers import router as comment_router
from src.auth.routers import router as auth_router
from fastapi.security import OAuth2PasswordBearer
from src.photos.routers import photo_router
app = FastAPI()

app.include_router(tag_router, prefix='/tags', tags=['tags'])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(photo_router, prefix="/photos", tags=["photos"])
app.include_router(comment_router, prefix="/comments", tags=["comments"])

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/ping")
async def ping():
    return {"ping": "pong"}


@app.get("/", response_class=HTMLResponse)
async def read_root( request: Request):
    user = get_user(request)
    return templates.TemplateResponse("index.html", {"request": request, 'user': user})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



