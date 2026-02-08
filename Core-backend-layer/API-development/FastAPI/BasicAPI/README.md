# Basic API setup with FastAPI

This guide walks through setting up a basic FastAPI project with a health check endpoint and a root endpoint. We'll use `uv` as the package and environment manager. FastAPI is a modern, fast web framework for building APIs based on standard Python type hints.
- **Based on open standards**: Built on OpenAPI and JSON Schema standards.
- **Async/await support**: Native support for asynchronous programming:
  - Use `async def` for async endpoints (recommended for I/O-bound operations). Use this when the code spends most of its time waiting for something else to finish, like a database query, an external API call or reading a file. It allows the server to handle other requests while it waits.
  - Use `def` for synchronous endpoints (for CPU-bound operations). Use this when the code is doing heavy math or data processing that keeps the processor busy. FastAPI automatically runs these in a separate thread so they don't "freeze" the rest of the app.
  - Mix both in the same application.
- **Automatic documentation**: Without any extra configuration, FastAPI generates interactive UI to test our endpoints:
  - **Swagger UI** at `/docs` - interactive API documentation.
  - **ReDoc** at `/redoc` - alternative API documentation.
  - **OpenAPI schema** at `/openapi.json` - machine-readable API specification.
- **Pydantic for data validation**: FastAPI uses Pydantic for data validation (ensures incoming data matches our requirements), data serialization (converts Python objects into JSON automatically), and editor support with autocompletion.


## Step 1: Project structure
```
01_BasicAPI/
├── README.md
├── pyproject.toml       # Dependencies and project metadata
└── main.py              # Main application file
```

Note: For this basic example, we use a single file. In later topics, we will organize code into multiple modules.

## Step 2: Setting up the environment and installing dependencies
1. Open VS Code and navigate to the project directory in the terminal.
2. Run `uv sync` to create a virtual environment and install all dependencies defined in `pyproject.toml`:
   ```bash
   uv sync
   ```
   - `uv` reads `pyproject.toml`, creates a `.venv` directory, and installs `fastapi`, `uvicorn` and any other listed dependencies.

## Step 3: Creating the FastAPI application
1. Create a new file named `main.py` and start by importing the required modules and creating the FastAPI application instance:
   ```python
   from fastapi import FastAPI
   from datetime import datetime
   from typing import Dict

   app = FastAPI(
       title="Product API",
       description="A Product Catalog API built with FastAPI - demonstrating basic setup and endpoints",
       version="1.0.0",
       contact={
           "name": "API Support",
           "email": "support@example.com",
       },
       license_info={
           "name": "MIT",
           "url": "https://opensource.org/licenses/MIT",
       },
   )
   ```
   - `FastAPI()` creates an instance of the FastAPI class, which represents the entire application.
   - `title`, `description`, and `version` appear in the auto-generated documentation.
   - `contact` and `license_info` are optional metadata that provide additional context in the docs.

2. Add a root endpoint that returns a welcome message and links to the documentation:
   ```python
   @app.get("/", tags=["Root"])
   async def root() -> Dict[str, str]:
       """
       Root endpoint - Welcome message and API information.
       """
       return {
           "message": "Welcome to Product API",
           "version": "1.0.0",
           "docs": "/docs",
           "redoc": "/redoc",
           "health": "/api/health"
       }
   ```
   - `@app.get("/")` defines a GET endpoint at the root URL `/`. FastAPI provides decorators for all HTTP methods (`@app.get()`, `@app.post()`, `@app.put()`, `@app.patch()`, `@app.delete()`).
   - `tags=["Root"]` groups this endpoint under the "Root" tag in Swagger UI, helping organize endpoints by category.
   - `async def` declares an asynchronous function. FastAPI supports both `async def` (for I/O-bound) and regular `def` (for CPU-bound) endpoints.
   - `-> Dict[str, str]` is a return type annotation that appears in the generated documentation.
   - The returned dictionary is automatically serialized to JSON by FastAPI.

3. Add a health check endpoint to monitor whether the API is running:
   ```python
   @app.get("/api/health", tags=["Health"])
   async def health_check() -> Dict[str, str]:
       """
       Health check endpoint - API status monitoring.
       """
       return {
           "status": "healthy",
           "version": "1.0.0",
           "framework": "FastAPI",
           "timestamp": datetime.now().isoformat()
       }
   ```
   - Health check endpoints are commonly used by load balancers, monitoring tools, and deployment pipelines to verify the API is running and responsive.
   - The docstring (`"""..."""`) becomes the endpoint description in Swagger UI, making the documentation more informative.
   - FastAPI automatically converts `datetime` objects to ISO format strings when serializing to JSON.

4. Optionally, add startup and shutdown event handlers:
   ```python
   @app.on_event("startup")
   async def startup_event():
       """Runs when the application starts."""
       print("Product API is starting up!")
       print("Swagger UI available at: http://localhost:8000/docs")

   @app.on_event("shutdown")
   async def shutdown_event():
       """Runs when the application shuts down."""
       print("Product API is shutting down...")
   ```
   - `@app.on_event("startup")` runs once when the application starts. Use this for initializing database connections, loading configuration or warming up caches.
   - `@app.on_event("shutdown")` runs when the application stops. Use this for closing database connections, saving state or cleaning up resources.

## Step 4: Running the application
1. Start the FastAPI app using Uvicorn (an ASGI server):
   ```bash
   uv run uvicorn main:app --reload --port 8000
   ```
   - `uv run` executes the command within the virtual environment managed by `uv`.
   - `main` refers to the Python file name (without `.py`).
   - `app` refers to the FastAPI instance variable name inside `main.py`.
   - `--reload` enables auto-reloading when code changes are saved (for development only).
   - `--port 8000` specifies the port (default is 8000).

2. Open the web browser and navigate to `http://localhost:8000/` to see the root endpoint response.

3. For production, run without `--reload` and with multiple workers:
   ```bash
   uv run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
   - `--host 0.0.0.0` allows external connections.
   - `--workers 4` runs multiple worker processes for handling concurrent requests.

## Step 5: Exploring the interactive API documentation
FastAPI automatically generates interactive API documentation without any additional configuration.
1. **Swagger UI**: Open the web browser and navigate to `http://localhost:8000/docs` to see the Swagger UI documentation. It provides a graphical interface to test endpoints directly in the browser, visualize request and response models, and see available parameters. This is the recommended way to test our API during development.
2. **ReDoc**: Alternatively, navigate to `http://localhost:8000/redoc` for a clean, three-panel documentation layout with search functionality. ReDoc offers a schema-driven view, ideal for reading through the API structure.
3. **OpenAPI Schema**: Navigate to `http://localhost:8000/openapi.json` to access the machine-readable API specification. This JSON file can be used to generate client SDKs or integrate with other tools.