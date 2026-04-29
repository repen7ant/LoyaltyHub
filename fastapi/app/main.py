from app.api.v1.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI

app = FastAPI(
    title="LoyaltyHub API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include(health_router)
