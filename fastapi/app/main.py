from app.api.v1 import ai, auth, loyalty, offers, users
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
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(loyalty.router)
app.include_router(offers.router)
app.include_router(ai.router)
