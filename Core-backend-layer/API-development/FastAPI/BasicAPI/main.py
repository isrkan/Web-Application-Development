"""
Product API - Basic Setup with FastAPI

This is a minimal FastAPI application demonstrating:
- Basic application setup
- Health check endpoint
- Root endpoint
- Automatic documentation

FastAPI automatically generates:
- Swagger UI at /docs
- ReDoc at /redoc
- OpenAPI schema at /openapi.json
"""

from fastapi import FastAPI
from datetime import datetime
from typing import Dict

# Create FastAPI application instance
# This instance represents the entire application
app = FastAPI(
    title="Product API",
    description="A Product Catalog API built with FastAPI - demonstrating basic setup and endpoints",
    version="1.0.0",
    # Optional metadata for documentation
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint - Welcome message and API information.

    This endpoint provides:
    - Welcome message
    - API version
    - Links to documentation
    - Link to health check

    **Tags**: Endpoints are organized by tags in the documentation.

    Returns:
        dict: Welcome information and links
    """
    return {
        "message": "Welcome to Product API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health"
    }


@app.get("/api/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint - API status monitoring.

    This endpoint is used to verify that the API is running and responsive.
    It's commonly used by:
    - Load balancers to check service health
    - Monitoring tools to track uptime
    - Deployment pipelines to verify successful deployment
    - Kubernetes liveness/readiness probes

    The `async def` keyword:
    - Defines an asynchronous function
    - Allows non-blocking I/O operations
    - Improves performance for I/O-bound tasks
    - Can be replaced with `def` for synchronous operations

    Type hints (`-> Dict[str, str]`):
    - Document the return type
    - Enable editor autocompletion
    - Appear in API documentation
    - Help catch errors during development

    Returns:
        dict: Health status information including:
            - status: Current API status
            - version: API version
            - framework: Framework name
            - timestamp: Current server time in ISO format
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "framework": "FastAPI",
        "timestamp": datetime.now().isoformat()
    }


# Optional: Startup and shutdown events
# These are useful for initializing and cleaning up resources
@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts.

    Use this for:
    - Initializing database connections
    - Loading configuration
    - Starting background tasks
    - Warming up caches
    """
    print("========================================")
    print("Product API is starting up!")
    print("Swagger UI available at: http://localhost:8000/docs")
    print("ReDoc available at: http://localhost:8000/redoc")
    print("Health check at: http://localhost:8000/api/health")
    print("========================================")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when the application shuts down.

    Use this for:
    - Closing database connections
    - Saving state
    - Cleaning up resources
    """
    print("========================================")
    print("Product API is shutting down...")
    print("========================================")


# How to run this application:
#
# Development mode (with auto-reload):
# uvicorn main:app --reload --port 8000
#
# Production mode:
# uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
#
# With custom settings:
# uvicorn main:app --reload --port 8001 --log-level debug

# Note: This file should not contain if __name__ == "__main__"
# because Uvicorn imports it as a module. The application is started via the uvicorn command, not by running this file directly.