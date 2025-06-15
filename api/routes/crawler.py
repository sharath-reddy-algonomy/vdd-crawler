import json
import uuid

from pydantic import BaseModel, Field
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from typing import List, Literal

from api.handlers.web_event_handler import schedule_run

crawler_router = APIRouter(
    prefix="/crawler",
    tags=["Crawler"]
)

ALLOWED_CRAWLERS = Literal["GOOGLE", "NEWS", "REGULATORY_DATABASES", "OFFICIAL_WEBSITE"]

class CreateDueDiligenceArtifactsRequest(BaseModel):
    vendor_name: str
    directors: List[str] | None
    pages: int
    schedule_id: str | None
    crawlers: List[ALLOWED_CRAWLERS]


@crawler_router.get("", include_in_schema=False)
def hello():
    return RedirectResponse(url="/docs")


@crawler_router.get("/info", include_in_schema=False)
def hello():
    return "Welcome to the Crawler App!"


@crawler_router.post("/due-diligence",
                     summary="Start due diligence crawling",
                     description="""
                     Create due diligence artifacts for the given vendor.
                     
                     - `schedule_id` - folder by this name will hold all crawled artifacts
                     - `vendor_name` - name of the vendor/company  
                     - `directors` - optional; list of names of directors of a company/vendor 
                     - `pages` - number of google search results pages to crawl  
                     - `crawlers` - list of allowed crawlers supported by the system; 
                                    one of: `GOOGLE, NEWS, REGULATORY_DATABASES,OFFICIAL_WEBSITE` 
                     """)
async def create_vendor_artifacts(due_diligence_request: CreateDueDiligenceArtifactsRequest):
    if not due_diligence_request.schedule_id:
        due_diligence_request.schedule_id = uuid.uuid4()
    schedule_run(json.dumps({
        "vendor_name": due_diligence_request.vendor_name,
        "schedule_id": due_diligence_request.schedule_id,
        "directors": due_diligence_request.directors,
        "pages": due_diligence_request.pages,
        "crawlers": due_diligence_request.crawlers,
    }), f"Scheduling {due_diligence_request.schedule_id}!")
    return {
        "schedule_id": due_diligence_request.schedule_id,
        "message": f"Crawling for {due_diligence_request.vendor_name} started...",
    }
