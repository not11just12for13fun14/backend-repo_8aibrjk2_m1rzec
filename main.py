import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# --- Polaroid Public Wall Endpoints ---
class ShareRequest(BaseModel):
    image_data: str  # data URL (base64) like "data:image/png;base64,..."
    instagram_url: str


@app.post("/api/polaroid/share")
def share_polaroid(payload: ShareRequest):
    if not payload.image_data.startswith("data:image"):
        raise HTTPException(status_code=400, detail="Invalid image data URL")

    doc_id = create_document("polaroidshare", {
        "image_data": payload.image_data,
        "instagram_url": payload.instagram_url,
    })
    return {"id": doc_id, "status": "ok"}


@app.get("/api/polaroid/public")
def list_public_polaroids(limit: Optional[int] = 100):
    items = get_documents("polaroidshare", {}, limit=limit)
    # Convert ObjectId to string
    for it in items:
        if it.get("_id"):
            it["id"] = str(it.pop("_id"))
    return {"items": items}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
