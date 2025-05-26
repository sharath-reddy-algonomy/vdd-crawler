from fastapi import APIRouter

website_router = APIRouter(
    prefix="/websites",
    tags=["Websites"]
)


@website_router.get("/{path}")
def homepage(path: str, url: str):
    return f"We will start hitting {url}!!!"
