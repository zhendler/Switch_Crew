from fastapi import APIRouter

tag_router = APIRouter()

@tag_router.get("/tags/")
def get_tags():
    return {"message": "This is a placeholder route for tags"}
