# Request handling with FastAPI

This guide walks through handling HTTP requests in FastAPI, including path parameters, query parameters, request bodies and proper status codes. We will build a complete CRUD API for products using in-memory storage.

#### Understanding request handling in FastAPI
FastAPI uses function parameters to handle different types of request data:
- **Path parameters**: Dynamic segments in the URL (e.g., `/products/{product_id}`), validated using `Path()`.
- **Query parameters**: Optional key-value pairs appended to the URL (e.g., `?category=Electronics`), validated using `Query()`.
- **Request body**: JSON data sent in the request body, received as a function parameter with a type hint.
- **Automatic validation**: FastAPI validates all incoming data using type hints and returns `422 Unprocessable Entity` for invalid data.
- **HTTP method decorators**: FastAPI provides a decorator for each HTTP method: `@app.get()`, `@app.post()`, `@app.put()`, `@app.patch()`, `@app.delete()`.


## Step 1: Project structure
```
02_RequestHandling/
├── README.md
├── pyproject.toml       # Dependencies and project metadata
├── main.py              # Main application file
```

## Step 2: Setting up the environment and installing dependencies
1. Open VS Code and navigate to the project directory in the terminal.
2. Run `uv sync` to create a virtual environment and install all dependencies defined in `pyproject.toml`:
   ```bash
   uv sync
   ```

## Step 3: Creating the FastAPI application
1. Create a new file named `main.py` and start by importing the required modules and creating the FastAPI application instance:
   ```python
   from fastapi import FastAPI, HTTPException, Path, Query, status
   from typing import Optional, Dict, Any

   app = FastAPI(
       title="Product API - Request Handling",
       description="Complete CRUD API demonstrating request handling with FastAPI",
       version="1.0.0"
   )
   ```
   - `HTTPException` is used to return proper error responses (e.g., 404 Not Found).
   - `Path` and `Query` are used to add validation and documentation to path and query parameters.
   - `status` provides semantic constants for HTTP status codes (e.g., `status.HTTP_201_CREATED` instead of `201`).

2. Set up in-memory storage for products. In a real application, this would be replaced by a database (covered in later topics):
   ```python
   products: Dict[int, Dict[str, Any]] = {}
   next_id = 1
   ```

3. Add a `GET` endpoint to list all products with optional filtering via query parameters:
   ```python
   @app.get("/api/products", tags=["Products"])
   async def get_products(
       category: Optional[str] = Query(None, description="Filter by category"),
       min_price: Optional[float] = Query(None, ge=0, description="Minimum price (must be >= 0)"),
       max_price: Optional[float] = Query(None, ge=0, description="Maximum price (must be >= 0)")
   ):
       """
       List all products with optional filtering.
       """
       filtered_products = list(products.values())

       if category:
           filtered_products = [
               p for p in filtered_products
               if p.get('category') == category
           ]
       if min_price is not None:
           filtered_products = [
               p for p in filtered_products
               if p.get('price', 0) >= min_price
           ]
       if max_price is not None:
           filtered_products = [
               p for p in filtered_products
               if p.get('price', 0) <= max_price
           ]

       return {
           "count": len(filtered_products),
           "data": filtered_products
       }
   ```
   - The `Query()` function defines query parameters. While FastAPI can automatically detect query parameters, the `Query()` function provides three essential features:
        * Validation: Constraints like `ge=0` add a validation constraint meaning "greater than or equal to 0". FastAPI returns `422` if the constraint is violated.
        * Metadata: The `description` and `title` arguments appear automatically in the Swagger UI documentation for each parameter, creating instant documentation for our API users.
        * Default Values: Setting the first argument to `None` makes the parameter optional. We can also use `...` (Ellipsis) to make a query parameter required.
   - Multiple query parameters can be combined in a single request (e.g., `?category=Electronics&min_price=500`).

4. Add a `GET` endpoint to retrieve a specific product by its ID using a path parameter:
   ```python
   @app.get("/api/products/{product_id}", tags=["Products"])
   async def get_product(
       product_id: int = Path(..., gt=0, description="The ID of the product to retrieve")
   ):
       """
       Get a specific product by ID.
       """
       if product_id not in products:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product with ID {product_id} not found"
           )
       return products[product_id]
   ```
   - `{product_id}` in the route is a path parameter. FastAPI automatically converts the string from the URL to `int`.
   - `Path(...)` defines a path parameter.
        * The Required Ellipsis (`...`): Unlike query parameters which are often optional, path parameters are part of the URL structure. Using `...` signals that this value is mandatory.
        * `gt=0` adds a validation constraint meaning "greater than 0". FastAPI returns `422` if a user passes `0` or a negative number.
        * Automatic type conversion: FastAPI performs "casting." If a user visits `/api/products/123`, FastAPI converts the string `"123"` into a Python `int` automatically. If they visit `/api/products/abc`, FastAPI will immediately return a `422 Unprocessable Entity` error because "abc" is not an integer.
   - Validation vs. logic errors: It is helpful to distinguish the two error types:
        * `422 Unprocessable Entity`: Triggered by `Path()` if the user sends the wrong *format* (e.g., a string instead of an integer).
        * `404 Not Found`: Triggered by your `HTTPException` logic if the data is the right *format*, but the product doesn't exist.

5. Add a `POST` endpoint to create a new product:
   ```python
   @app.post("/api/products", status_code=status.HTTP_201_CREATED, tags=["Products"])
   async def create_product(product: dict):
       """
       Create a new product.
       """
       global next_id

       product_data = product.copy()
       product_data['id'] = next_id

       products[next_id] = product_data
       next_id += 1

       return product_data
   ```
   
   - Standardizing success (`201 Created`): By default, FastAPI returns `200 OK`. However, using `status_code=status.HTTP_201_CREATED` follows REST API best practices, explicitly informing the client that a new resource was successfully generated.
   - The request body: Unlike query and path parameters which live and visible in the URL, the `product: dict` parameter tells FastAPI to look inside the HTTP request body. The request body is data sent "under the hood" inside the HTTP packet. It is used for larger, structured data (like a JSON object) that should not clutter the URL. FastAPI automatically detects the `Content-Type: application/json` header, parses the JSON, and converts it into a Python dictionary.
   - The role of `dict`: Currently, we are using a generic `dict`, which is flexible but "blind" (it does not check if the name is a string or the price is a number).
        * In the next topic, we will replace `dict` with Pydantic models to enforce strict schema validation for the request body.

6. Add a `PUT` endpoint for full updates and a `PATCH` endpoint for partial updates:
   ```python
   @app.put("/api/products/{product_id}", tags=["Products"])
   async def update_product(
       product_id: int = Path(..., gt=0, description="Product ID to update"),
       product: dict = None
   ):
       """
       Perform a full update of a product.
       """
       if product_id not in products:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product with ID {product_id} not found"
           )

       product_data = product.copy()
       product_data['id'] = product_id
       products[product_id] = product_data

       return product_data


   @app.patch("/api/products/{product_id}", tags=["Products"])
   async def patch_product(
       product_id: int = Path(..., gt=0, description="Product ID to update"),
       updates: dict = None
   ):
       """
       Perform a partial update of a product.
       """
       if product_id not in products:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product with ID {product_id} not found"
           )

       product = products[product_id]
       product.update(updates)
       product['id'] = product_id

       return product
   ```

   - `PUT` replaces the entire resource with the provided data. All fields should be provided. It is idempotent, meaning calling it multiple times with the same data produces the same result.
   - `PATCH` updates only the provided fields, leaving others unchanged. For example, sending `{"price": 999.99}` only updates the price field.
   - Both endpoints combine a path parameter (`product_id`) with a request body (`product`/`updates`). FastAPI distinguishes them automatically based on the parameter source.

7. Add a `DELETE` endpoint to remove a product:
   ```python
   @app.delete("/api/products/{product_id}", tags=["Products"])
   async def delete_product(
       product_id: int = Path(..., gt=0, description="Product ID to delete")
   ):
       """
       Delete a product by ID.
       """
       if product_id not in products:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product with ID {product_id} not found"
           )

       del products[product_id]

       return {
           "message": "Product deleted successfully",
           "id": product_id
       }
   ```
   - The `DELETE` method is used to remove resources permanently. Unlike `GET` or `POST`, it usually does not require a request body - it only needs to know which item to remove via a path parameter.
   - While some APIs return a `204 No Content` status (meaning the body is empty), returning a JSON message as shown above is a common practice. It provides the client with a clear confirmation and repeats the ID of the deleted resource for logging or UI updates.
   - Technically, `DELETE` is considered idempotent. If we delete ID `10`, it is gone. If we try to delete ID `10` again, the server state has not changed (it is still gone), though our specific code will raise a `404 Not Found` for the second attempt to inform the user the resource is already missing.

8. Add a root endpoint and a startup event:
   ```python
   @app.get("/", tags=["Root"])
   async def root():
       """Root endpoint providing API information."""
       return {
           "message": "Product API - Request Handling",
           "version": "1.0.0",
           "docs": "/docs",
           "endpoints": {
               "list_products": "GET /api/products",
               "get_product": "GET /api/products/{id}",
               "create_product": "POST /api/products",
               "update_product": "PUT /api/products/{id}",
               "patch_product": "PATCH /api/products/{id}",
               "delete_product": "DELETE /api/products/{id}"
           }
       }

   @app.on_event("startup")
   async def startup_event():
       """Runs when the application starts."""
       print("Product API - Request Handling")
       print("Swagger UI: http://localhost:8000/docs")
   ```
   - The root endpoint (`/`): While not strictly required, a root endpoint acts as a "landing page" for our API. It provides metadata (like versioning) and a map of available endpoints, which is helpful for health checks or developers who land on our URL without knowing the path.
   - By returning a `docs` link in the JSON, we make our API self-documenting and easy to navigate directly from a browser.
   - Note: While `@app.on_event` is widely used, modern FastAPI versions also support the `lifespan` context manager, which is the recommended way to handle both startup and shutdown logic in a single block.

### CRUD summary table
Now that we have implemented all endpoints, here is how they handle data:

| Method | Goal | Source of Data | Success Code |
| --- | --- | --- | --- |
| **GET** | Read | Query (filters) / Path (ID) | `200 OK` |
| **POST** | Create | Request Body (JSON) | `201 Created` |
| **PUT** | Replace | Path (ID) + Body (Full) | `200 OK` |
| **PATCH** | Update | Path (ID) + Body (Partial) | `200 OK` |
| **DELETE** | Remove | Path (ID) | `200 OK` |

## Step 4: Running the application

1. Start the FastAPI app using Uvicorn:
   ```bash
   uv run uvicorn main:app --reload --port 8000
   ```
   - `uv run` executes the command within the virtual environment managed by `uv`.
   - `main` refers to the Python file name (without `.py`), and `app` refers to the FastAPI instance variable name.
   - `--reload` enables auto-reloading when code changes are saved (for development only).
2. Open the web browser and navigate to `http://localhost:8000/` to see the root endpoint response with the list of available endpoints.

## Step 5: Testing the endpoints
Open Swagger UI at `http://localhost:8000/docs` to test all endpoints interactively. The endpoints available are:

| Method   | Endpoint                      | Description                       |
|----------|-------------------------------|-----------------------------------|
| `GET`    | `/api/products`               | List all products (with filtering)|
| `GET`    | `/api/products/{product_id}`  | Get a specific product            |
| `POST`   | `/api/products`               | Create a new product              |
| `PUT`    | `/api/products/{product_id}`  | Full update of a product          |
| `PATCH`  | `/api/products/{product_id}`  | Partial update of a product       |
| `DELETE` | `/api/products/{product_id}`  | Delete a product                  |

In Swagger UI, click on any endpoint, then click **Try it out** to fill in the parameters and request body, and click **Execute** to send the request and see the response.
