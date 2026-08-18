from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from app.services.knots_data import KNOTS_DATA

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
router = APIRouter(tags=["Knots"])

@router.get("/knots", response_class=HTMLResponse)
def knots_list(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="knots.html",
        context={
            "knots": KNOTS_DATA
        }
    )
