import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from bson.objectid import ObjectId

from database import create_document, get_documents, db
from schemas import Waitlist

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

@app.post("/api/waitlist")
def join_waitlist(item: Waitlist):
    """Add an email to the waitlist collection, preventing duplicates."""
    # Normalize email to lowercase to avoid duplicates
    email = item.email.lower()

    # Check if already exists
    existing = list(db["waitlist"].find({"email": email}).limit(1)) if db else []
    if existing:
        return {"status": "exists", "message": "You're already on the waitlist!"}

    # Create document
    data = {"email": email, "source": item.source or "website"}
    inserted_id = create_document("waitlist", data)
    return {"status": "ok", "id": inserted_id, "message": "You're in! We'll be in touch soon."}

@app.get("/api/waitlist")
def list_waitlist(limit: int = 10):
    """Return recent waitlist entries (for quick verification)."""
    docs = get_documents("waitlist", {}, limit)
    # Convert ObjectId to string
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["_id"] = str(d["_id"]) 
        # Convert datetime to isoformat strings
        if "created_at" in d and hasattr(d["created_at"], "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        if "updated_at" in d and hasattr(d["updated_at"], "isoformat"):
            d["updated_at"] = d["updated_at"].isoformat()
    return {"items": docs}

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
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
