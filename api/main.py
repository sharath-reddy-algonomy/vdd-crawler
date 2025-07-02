import uvicorn
from fastapi import FastAPI

from api.handlers.s3_notification_handler import listen_to_s3_notifications
from api.routes.crawler import crawler_router
from api.routes.websites import website_router

app = FastAPI()

app.include_router(crawler_router)

