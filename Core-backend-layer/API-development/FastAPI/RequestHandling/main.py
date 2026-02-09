"""
Product API - Request Handling with FastAPI

This application demonstrates comprehensive request handling:
- All HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Path parameters with validation
- Query parameters with filtering
- Request body handling
- Proper status codes
- Error handling with HTTPException
- Automatic validation and documentation
"""

from fastapi import FastAPI, HTTPException, Path, Query, status
from typing import Optional, Dict, Any

# Create FastAPI application instance
app = FastAPI(
    title="Product API - Request Handling",
    description="Complete CRUD API demonstrating request handling with FastAPI",
    version="1.0.0"
)

# In-memory storage for products - In a real application, this would be a database
# Change your empty dict to include some starting data
products: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "Smartphone",
        "description": "Latest model with great camera",
        "price": 699.99,
        "category": "Electronics",
        "manufacturer": "GadgetCorp",
        "stock_quantity": 100
    },
    2: {
        "id": 2,
        "name": "Coffee Mug",
        "description": "Ceramic 12oz mug",
        "price": 12.50,
        "category": "Kitchen",
        "manufacturer": "HomeStyle",
        "stock_quantity": 250
    }
}
next_id = 3  # Ensure this starts after our dummy IDs


@app.get("/api/products", tags=["Products"])
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price (must be >= 0)"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price (must be >= 0)")
):
    """
    List all products with optional filtering.

    Query parameters (all optional):
    - **category**: Filter products by category
    - **min_price**: Filter products with price >= this value
    - **max_price**: Filter products with price <= this value

    Multiple filters can be combined.

    The Query() function:
    - Makes parameters optional with default None
    - Adds validation (ge=0 means >= 0)
    - Provides description for documentation
    - Automatically validates types

    Returns:
        dict: Object containing count and filtered products
    """
    # Start with all products
    filtered_products = list(products.values())

    # Apply category filter if provided
    if category:
        filtered_products = [
            p for p in filtered_products
            if p.get('category') == category
        ]

    # Apply minimum price filter if provided
    if min_price is not None:
        filtered_products = [
            p for p in filtered_products
            if p.get('price', 0) >= min_price
        ]

    # Apply maximum price filter if provided
    if max_price is not None:
        filtered_products = [
            p for p in filtered_products
            if p.get('price', 0) <= max_price
        ]

    return {
        "count": len(filtered_products),
        "data": filtered_products
    }


@app.get("/api/products/{product_id}", tags=["Products"])
async def get_product(
    product_id: int = Path(..., gt=0, description="The ID of the product to retrieve")
):
    """
    Get a specific product by ID.

    Path parameters:
    - **product_id**: The unique identifier of the product (must be > 0)

    The Path() function:
    - ... means the parameter is required
    - gt=0 means greater than 0 (validation)
    - Provides description for documentation
    - Automatically validates type and constraints

    FastAPI automatically:
    - Converts string from URL to int
    - Validates product_id > 0
    - Returns 422 if validation fails
    - Documents in OpenAPI

    Raises:
        HTTPException: 404 if product not found

    Returns:
        dict: Product data
    """
    if product_id not in products:
        # HTTPException provides proper error responses
        # Automatically documented in OpenAPI
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    return products[product_id]


@app.post("/api/products", status_code=status.HTTP_201_CREATED, tags=["Products"])
async def create_product(product: dict):
    """
    Create a new product.

    Request body should be JSON with product fields:
    - **name** (string, required): Product name
    - **description** (string, optional): Product description
    - **price** (number, required): Product price
    - **category** (string, required): Product category
    - **manufacturer** (string, required): Manufacturer name
    - **stock_quantity** (integer, optional): Stock quantity

    The request body is automatically parsed from JSON.
    Type hint `dict` accepts any JSON object.
    We will cover later Pydantic models for validation.

    The status_code parameter sets the success status code.
    Using status.HTTP_201_CREATED is more semantic than 201.

    Returns:
        dict: Created product with ID
    """
    global next_id

    # Add ID to product data
    product_data = product.copy()
    product_data['id'] = next_id

    # Store product
    products[next_id] = product_data
    next_id += 1

    return product_data


@app.put("/api/products/{product_id}", tags=["Products"])
async def update_product(
    product_id: int = Path(..., gt=0, description="Product ID to update"),
    product: dict = None
):
    """
    Perform a full update of a product.

    PUT replaces the entire resource with the provided data.
    All fields should be provided.

    Path parameters:
    - **product_id**: ID of the product to update

    Request body:
    - Complete product data (all fields)

    PUT is idempotent - calling it multiple times with the same data produces the same result.
    For partial updates, use PATCH instead.

    Raises:
        HTTPException: 404 if product not found

    Returns:
        dict: Updated product data
    """
    if product_id not in products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    # Update product data
    product_data = product.copy()
    product_data['id'] = product_id  # Ensure ID doesn't change
    products[product_id] = product_data

    return product_data


@app.patch("/api/products/{product_id}", tags=["Products"])
async def patch_product(
    product_id: int = Path(..., gt=0, description="Product ID to update"),
    updates: dict = None
):
    """
    Perform a partial update of a product.

    PATCH updates only the provided fields, leaving others unchanged.
    This is different from PUT which replaces the entire resource.

    Path parameters:
    - **product_id**: ID of the product to update

    Request body:
    - Fields to update (partial data)

    Example:
    PATCH with {"price": 999.99} only updates the price field.

    Raises:
        HTTPException: 404 if product not found

    Returns:
        dict: Updated product data
    """
    if product_id not in products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    # Get existing product
    product = products[product_id]

    # Apply updates
    product.update(updates)

    # Ensure ID doesn't change
    product['id'] = product_id

    return product


@app.delete("/api/products/{product_id}", tags=["Products"])
async def delete_product(
    product_id: int = Path(..., gt=0, description="Product ID to delete")
):
    """
    Delete a product by ID.

    Path parameters:
    - **product_id**: ID of the product to delete

    DELETE is idempotent - deleting a non-existent resource
    can return 404 or 204 (both are acceptable).

    We return 404 if the product doesn't exist for clarity.

    Raises:
        HTTPException: 404 if product not found

    Returns:
        dict: Success message with deleted product ID
    """
    if product_id not in products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    # Delete product
    del products[product_id]

    return {
        "message": "Product deleted successfully",
        "id": product_id
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information.

    Returns links to documentation and available endpoints.
    """
    return {
        "message": "Product API - Request Handling",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "list_products": "GET /api/products",
            "get_product": "GET /api/products/{id}",
            "create_product": "POST /api/products",
            "update_product": "PUT /api/products/{id}",
            "patch_product": "PATCH /api/products/{id}",
            "delete_product": "DELETE /api/products/{id}"
        }
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts.

    Useful for:
    - Initializing database connections
    - Loading configuration
    - Warming up caches
    """
    print("========================================")
    print("Product API - Request Handling")
    print("========================================")
    print("Swagger UI: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("API Endpoints: http://localhost:8000/api/products")
    print("========================================")


# Run with: uvicorn main:app --reload --port 8000