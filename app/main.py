import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.ai.exceptions import AIConfigurationError, AIServiceError
from app.api import auth, tasks

logger = logging.getLogger(__name__)

# Create the application object. Everything else (routes, error handlers) attaches to this.
app = FastAPI(
    title="AI Task Manager",
    description="Task management API with JWT auth, roles, and AI-generated descriptions.",
    version="1.0.0",
)

# Plug the route groups into the app.
app.include_router(auth.router)
app.include_router(tasks.router)


# ---------- Global error handlers ----------
# An exception handler says: "whenever this exception type escapes any route,
# run this function and send its return value as the response."
# FastAPI picks the MOST SPECIFIC matching handler, so registration order
# does not matter (AIConfigurationError beats its parent AIServiceError).

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """422: the request body, path or query failed validation."""
    errors = []
    for err in exc.errors():
        loc = err["loc"]  # e.g. ("body", "email"): where the problem is
        errors.append(
            {
                # Drop the leading "body"/"path"/"query"; keep the field name.
                "field": ".".join(str(part) for part in loc[1:]) or str(loc[0]),
                "message": err["msg"],
                # We deliberately do NOT include err["input"]: it would echo
                # the submitted value, which could be a password.
            }
        )
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed", "errors": errors},
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """500: any database failure. The session was already rolled back in get_db."""
    # Full details (including the traceback) go to the SERVER log only.
    logger.exception("Database error on %s %s", request.method, request.url.path)
    # The client gets a generic message: no SQL, no table names.
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred. Please try again later."},
    )


@app.exception_handler(AIConfigurationError)
async def ai_configuration_error_handler(request: Request, exc: AIConfigurationError):
    """503: the AI feature is not configured (for example, no API key)."""
    return JSONResponse(
        status_code=503,
        content={"detail": "AI service is not configured"},
    )


@app.exception_handler(AIServiceError)
async def ai_service_error_handler(request: Request, exc: AIServiceError):
    """502: the AI provider failed or returned something unusable."""
    # exc's message is logged by ai/client.py; the client gets a generic one.
    return JSONResponse(
        status_code=502,
        content={"detail": "AI service failed. Please try again later."},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    """500: last resort for any bug we did not anticipate."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Health check: lets monitors confirm the app is alive. No auth, no database.
@app.get("/health")
def health_check():
    return {"status": "ok"}