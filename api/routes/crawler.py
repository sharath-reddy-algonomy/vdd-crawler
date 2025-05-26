import json
import uuid

from pydantic import BaseModel
from fastapi import APIRouter
from typing import List

from api.config import MSG_PUBLISHER
from api.handlers.web_event_handler import schedule_run

crawler_router = APIRouter(
    prefix="/crawler",
    tags=["Crawler"]
)


class CreateDueDiligenceArtifactsRequest(BaseModel):
    vendor_name: str
    #directors: List[str]
    pages: int
    schedule_id: str | None


@crawler_router.get("")
def hello():
    return "Welcome!"


@crawler_router.get("/info")
def hello():
    return "Welcome to the Crawler App!"


@crawler_router.post("/due-diligence")
async def create_vendor_artifacts(due_diligence_request: CreateDueDiligenceArtifactsRequest):
    if not due_diligence_request.schedule_id:
        due_diligence_request.schedule_id = uuid.uuid4()
    schedule_run(json.dumps({
        "vendor_name": due_diligence_request.vendor_name,
        "schedule_id": due_diligence_request.schedule_id,
        "pages": due_diligence_request.pages,
    }), f"Scheduling {due_diligence_request.schedule_id}!")
    return {
        "schedule_id": due_diligence_request.schedule_id,
        "message": f"Crawling for {due_diligence_request.vendor_name} started...",
    }
