from fastapi import FastAPI, Request
from starlette.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")

def get_response_format(request: Request):
    if "application/json" in request.headers.get("accept", ""):
        return "json"
    return "html"
