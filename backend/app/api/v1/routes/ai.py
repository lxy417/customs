from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import call_deepseek_api

router = APIRouter()

class AISearchRequest(BaseModel):
    search_value: str
    export_countries: list[str]
    import_countries: list[str]

@router.post("/search")
async def search(request: AISearchRequest):
    try:
        result = await call_deepseek_api(
            request.search_value,
            request.export_countries,
            request.import_countries
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))