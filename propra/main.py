"""FastAPI application entrypoint for the Propra API."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from propra.api.assess import router as assess_router
from propra.api.intake import router as intake_router

load_dotenv()

app = FastAPI(
    title="Propra API",
    description="Regulatory assessment API for German homeowners.",
    version="0.1.0",
)

_frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake_router, prefix="/api")
app.include_router(assess_router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
