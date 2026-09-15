from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.dashboard import router as dashboard_router
from backend.api.transactions import router as transactions_router
from backend.api.users import router as users_router
from backend.api.merchants import router as merchants_router
from backend.api.investigations import router as investigations_router
from backend.api.networks import router as networks_router
from backend.api.agent import router as agent_router
from backend.api.upload import router as upload_router


app = FastAPI(
    title="UPI Sentinel API",
    description="AI-Powered UPI Fraud & Merchant Intelligence Platform",
    version="0.2.0",
)


# ----------------------------------------------------------------------
# CORS
# ----------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# ROUTERS
# ----------------------------------------------------------------------

app.include_router(
    dashboard_router,
    prefix="/api/dashboard",
    tags=["Dashboard"],
)

app.include_router(
    transactions_router,
    prefix="/api/transactions",
    tags=["Transactions"],
)

app.include_router(
    users_router,
    prefix="/api/users",
    tags=["Users"],
)

app.include_router(
    merchants_router,
    prefix="/api/merchants",
    tags=["Merchants"],
)

app.include_router(
    investigations_router,
    prefix="/api/investigations",
    tags=["Investigations"],
)

app.include_router(
    networks_router,
    prefix="/api/networks",
    tags=["Networks"],
)


# ----------------------------------------------------------------------
# ROOT / HEALTH
# ----------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "name": "UPI Sentinel",
        "description": "AI-Powered UPI Fraud & Merchant Intelligence Platform",
        "status": "running",
        "version": "0.2.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "upi-sentinel-api",
    }

app.include_router(agent_router, prefix="/api/agent", tags=["AI Investigator"])
app.include_router(upload_router, prefix="/api")
