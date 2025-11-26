import asyncio
import json
import logging
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from llm_json_streaming import create_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM JSON Streaming Example")

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StreamRequest(BaseModel):
    prompt: str
    api_key: str
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"

# --- Complex Schema Definition ---

class Location(BaseModel):
    lat: float
    lng: float
    address: str

class Review(BaseModel):
    author: str
    rating: float
    comment: str

class Attraction(BaseModel):
    name: str
    type: str  # e.g., "Museum", "Park", "Restaurant"
    description: str
    price_range: str # "$", "$$", "$$$"
    location: Optional[Location] = None
    reviews: List[Review] = []

class DayItinerary(BaseModel):
    day: int
    title: str
    activities: List[Attraction] = []
    summary: str

class CityGuide(BaseModel):
    city_name: str
    country: str
    description: str
    best_time_to_visit: str
    currency: str
    languages: List[str] = []
    itinerary: List[DayItinerary] = []
    top_tips: List[str] = []

# ---------------------------------

@app.post("/stream")
async def stream_json(request: StreamRequest):
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    try:
        # Initialize provider with the API key from request
        provider = create_provider(request.provider, api_key=request.api_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to initialize provider: {str(e)}")

    async def generate():
        try:
            # Stream the JSON response using the complex CityGuide schema
            async for chunk in provider.stream_json(request.prompt, CityGuide, model=request.model):
                
                data_to_send = {}
                if "partial_object" in chunk:
                    # Convert Pydantic model to dict
                    obj = chunk["partial_object"]
                    if isinstance(obj, BaseModel):
                        data_to_send["partial_object"] = obj.model_dump()
                    else:
                        data_to_send["partial_object"] = obj
                
                if "final_object" in chunk:
                    obj = chunk["final_object"]
                    if isinstance(obj, BaseModel):
                        data_to_send["final_object"] = obj.model_dump()
                    else:
                        data_to_send["final_object"] = obj

                # Also include any error if present
                if "error" in chunk:
                    data_to_send["error"] = chunk["error"]

                if data_to_send:
                    yield json.dumps(data_to_send) + "\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
