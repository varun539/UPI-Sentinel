from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="UPI Sentinel API",
    description="UPI Fraud & Merchant Intelligence Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "UPI Sentinel API is running 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }