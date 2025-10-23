from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import test, preprocess

app = FastAPI(
    title="FASTAptameR3 Python",
    description="A Python web application for aptamer sequence analysis",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(test.router, prefix="/api/v1", tags=["test"])
app.include_router(preprocess.router, prefix="/api/v1", tags=["preprocess"])

@app.get("/")
async def root():
    return {"message": "Welcome to Fastaptamer3 Project"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
