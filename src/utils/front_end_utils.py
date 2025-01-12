from fastapi import FastAPI, Request

app = FastAPI()

def get_response_format(request: Request):
    if "application/json" in request.headers.get("accept", ""):
        return "json"
    return "html"
