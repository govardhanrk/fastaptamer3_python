from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import test

app = FastAPI(
    title="My FastAPI Project",
    description="A FastAPI project with organized routers",
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

@app.get("/")
async def root():
    return {"message": "Welcome to Fastaptamer3 Project"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
