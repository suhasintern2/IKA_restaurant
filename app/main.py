from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.api.entries import router as entries_router
from app.api.export import router as export_router

app = FastAPI(title="TIL SYSTEM Backend", version="0.1.0")

# Include routers
app.include_router(upload_router, prefix="/api")
app.include_router(entries_router, prefix="/api")
app.include_router(export_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "TIL SYSTEM Backend is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}