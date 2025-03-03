from datetime import datetime

from fastapi import FastAPI, Request
from starlette.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")

def get_response_format(request: Request):
    if "application/json" in request.headers.get("accept", ""):
        return "json"
    return "html"

def truncatechars(value: str = "1", length: int = 35):
    if len(value) > length:
        return value[:length] + "..."
    return value

def format_datetime(value: datetime, format_str: str = "%d %B %Y"):
    if isinstance(value, datetime):  # Проверяем, что это datetime
        return value.strftime(format_str)
    return value  # Если нет, возвращаем как есть