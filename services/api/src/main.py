"""
Manning Patrol Backend

Main FastAPI application.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.routers import events, positioning_simulator
from src.services.producer import EventValidationError

app = FastAPI(title="Manning Patrol Backend")


@app.exception_handler(EventValidationError)
async def event_validation_exception_handler(
    _: Request,
    error: EventValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(error)},
    )


# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(positioning_simulator.router)
app.include_router(events.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Manning Patrol Backend running"}


def dev():
    """Run development server with reload."""
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
