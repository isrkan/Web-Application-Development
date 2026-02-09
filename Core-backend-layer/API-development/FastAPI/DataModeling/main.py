"""
Product API - Data Modeling with FastAPI and Pydantic

This application demonstrates data modeling using Pydantic:
- Type-safe data models
- Automatic validation
- Clear error messages
- Automatic OpenAPI documentation
- Request/response models

In Topic 2, we used plain dict for data.
In Topic 3, we use Pydantic models for type safety and validation.
"""

from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date
from decimal import Decimal

# Create FastAPI application
app = FastAPI(
    title="Product API - Data Modeling",
    description="Topic 3: Data Modeling with Pydantic models",
    version="1.0.0"
)

# In-memory storage
# Later, this will be replaced with database
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
next_id = 3


# ==================== Pydantic Models ====================

class ProductBase(BaseModel):
    """
    Base Product model with common fields

    Pydantic models provide:
    - Automatic type validation
    - Field constraints and validation
    - Clear error messages
    - Automatic documentation
    - IDE autocomplete

    Field() function adds:
    - Validation constraints (gt, ge, le, lt, min_length, max_length)
    - Default values
    - Description for documentation
    - Examples for API docs
    """

    name: str = Field(
        ...,  # ... means required
        min_length=2,
        max_length=200,
        description="Product name (2-200 characters)",
        examples=["Laptop", "Gaming Mouse"]
    )

    description: Optional[str] = Field(
        None,  # None means optional
        max_length=1000,
        description="Product description (optional)",
        examples=["High-performance laptop for developers"]
    )

    price: Decimal = Field(
        ...,  # Required
        gt=0,  # Greater than 0
        max_digits=10,
        decimal_places=2,
        description="Product price (must be positive)",
        examples=[999.99, 1299.99]
    )

    category: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Product category",
        examples=["Electronics", "Clothing", "Books"]
    )

    manufacturer: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Manufacturer name",
        examples=["TechCorp", "GamerTech"]
    )

    stock_quantity: Optional[int] = Field(
        None,
        ge=0,  # Greater than or equal to 0
        description="Stock quantity (optional, must be non-negative)",
        examples=[50, 100]
    )

    production_date: Optional[date] = Field(
        None,
        description="Production date in YYYY-MM-DD format (optional)",
        examples=["2024-01-15"]
    )

    # ==================== Field Validators ====================

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Custom validator for name field

        @field_validator decorator marks this as a validator
        Runs automatically when name is being set

        Args:
            value: The name value to validate

        Returns:
            The validated (possibly modified) value

        Raises:
            ValueError: If validation fails
        """
        # Strip whitespace
        value = value.strip()

        # Check if name starts with a digit
        if value[0].isdigit():
            raise ValueError("Product name cannot start with a number")

        return value

    @field_validator('price')
    @classmethod
    def validate_price(cls, value: Decimal) -> Decimal:
        """
        Custom validator for price field

        This is in addition to the gt=0 constraint.

        Args:
            value: The price to validate

        Returns:
            The validated price

        Raises:
            ValueError: If validation fails
        """
        # Check for suspiciously high prices
        if value > 1000000:
            raise ValueError("Price seems too high. Please verify.")

        return value

    @field_validator('production_date')
    @classmethod
    def validate_production_date(cls, value: Optional[date]) -> Optional[date]:
        """
        Custom validator for production_date field

        Args:
            value: The production date to validate

        Returns:
            The validated date

        Raises:
            ValueError: If validation fails
        """
        if value and value > date.today():
            raise ValueError("Production date cannot be in the future")

        return value

    # Model-level validator (validates across multiple fields)
    # Pydantic v2 uses @model_validator for this
    def model_post_init(self, __context) -> None:
        """
        Model-level validation after all fields are set

        This runs after field validators.
        Use for validation that depends on multiple fields.
        """
        # Example: Expensive products should have descriptions
        if self.price > 1000 and not self.description:
            raise ValueError("Products over $1000 must have a description")

        # Example: Electronics must have stock quantity
        if self.category == "Electronics" and self.stock_quantity is None:
            raise ValueError("Electronics must have stock quantity specified")


class Product(ProductBase):
    """
    Product model with ID (for responses)

    This extends ProductBase and adds the ID field.
    Used when returning products from the API.

    Separating models like this:
    - ProductBase: For creation (no ID yet)
    - Product: For responses (includes ID)
    - Keeps API contract clear
    """

    id: int = Field(
        ...,
        description="Unique product identifier",
        examples=[1, 2]
    )

    class Config:
        """
        Pydantic configuration

        json_schema_extra provides example for documentation
        """
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Laptop",
                "description": "High-performance laptop",
                "price": 1299.99,
                "category": "Electronics",
                "manufacturer": "TechCorp",
                "stock_quantity": 50,
                "production_date": "2024-01-15"
            }
        }


class ProductCreate(ProductBase):
    """
    Model for creating products (request body)

    Same as ProductBase but can be extended with create-specific validations
    """
    pass


class ProductUpdate(BaseModel):
    """
    Model for updating products (PUT)

    All fields from ProductBase, all required
    """
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    category: str = Field(..., min_length=2, max_length=100)
    manufacturer: str = Field(..., min_length=2, max_length=200)
    stock_quantity: Optional[int] = Field(None, ge=0)
    production_date: Optional[date] = None

    # Add same validators as ProductBase
    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if value[0].isdigit():
            raise ValueError("Product name cannot start with a number")
        return value

    @field_validator('price')
    @classmethod
    def validate_price(cls, value: Decimal) -> Decimal:
        if value > 1000000:
            raise ValueError("Price seems too high")
        return value

    @field_validator('production_date')
    @classmethod
    def validate_production_date(cls, value: Optional[date]) -> Optional[date]:
        if value and value > date.today():
            raise ValueError("Production date cannot be in the future")
        return value


class ProductPatch(BaseModel):
    """
    Model for partial updates (PATCH)

    All fields are optional for partial updates
    """
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    manufacturer: Optional[str] = Field(None, min_length=2, max_length=200)
    stock_quantity: Optional[int] = Field(None, ge=0)
    production_date: Optional[date] = None

    # Add same validators
    @field_validator('name')
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value:
            value = value.strip()
            if value[0].isdigit():
                raise ValueError("Product name cannot start with a number")
        return value

    @field_validator('price')
    @classmethod
    def validate_price(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value and value > 1000000:
            raise ValueError("Price seems too high")
        return value

    @field_validator('production_date')
    @classmethod
    def validate_production_date(cls, value: Optional[date]) -> Optional[date]:
        if value and value > date.today():
            raise ValueError("Production date cannot be in the future")
        return value


class ProductListResponse(BaseModel):
    """
    Model for list response with metadata
    """
    count: int
    data: List[Product]


# ==================== Endpoints ====================

@app.get(
    "/api/products",
    response_model=ProductListResponse,
    tags=["Products"]
)
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price")
):
    """
    List all products with optional filtering

    Demonstrates:
    - Returning Pydantic model (ProductListResponse)
    - FastAPI automatically serializes to JSON
    - Type-safe query parameters
    """
    # Start with all products
    filtered_products = list(products.values())

    # Apply filters
    if category:
        filtered_products = [p for p in filtered_products if p.get('category') == category]

    if min_price is not None:
        filtered_products = [
            p for p in filtered_products
            if p.get('price') and Decimal(str(p['price'])) >= min_price
        ]

    if max_price is not None:
        filtered_products = [
            p for p in filtered_products
            if p.get('price') and Decimal(str(p['price'])) <= max_price
        ]

    # Return using response model
    # FastAPI automatically validates response matches ProductListResponse
    return ProductListResponse(
        count=len(filtered_products),
        data=filtered_products
    )


@app.get(
    "/api/products/{product_id}",
    response_model=Product,
    tags=["Products"]
)
async def get_product(
    product_id: int = Path(..., gt=0, description="Product ID")
):
    """
    Get a specific product by ID

    Demonstrates:
    - Returning Pydantic model (Product)
    - Automatic serialization
    """
    if product_id not in products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    return products[product_id]


@app.post(
    "/api/products",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    tags=["Products"]
)
async def create_product(product: ProductCreate):
    """
    Create a new product

    Demonstrates:
    - Request body as Pydantic model (ProductCreate)
    - FastAPI automatically:
      - Parses JSON to ProductCreate object
      - Validates all fields
      - Runs field validators
      - Returns 422 if validation fails
    - No manual validation needed!

    Args:
        product: Product data (validated automatically)

    Returns:
        Created product with ID
    """
    global next_id

    # Convert Pydantic model to dict
    product_data = product.model_dump()

    # Add ID
    product_data['id'] = next_id

    # Store (convert Decimal to float for JSON)
    product_data['price'] = float(product_data['price'])
    if product_data.get('production_date'):
        product_data['production_date'] = str(product_data['production_date'])

    products[next_id] = product_data
    next_id += 1

    return product_data


@app.put(
    "/api/products/{product_id}",
    response_model=Product,
    tags=["Products"]
)
async def update_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    product: ProductUpdate = None
):
    """
    Full update of a product (PUT)

    Demonstrates:
    - ProductUpdate model with all fields required
    - Automatic validation of all fields
    """
    if product_id not in products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    # Convert to dict
    product_data = product.model_dump()

    # Add ID
    product_data['id'] = product_id

    # Convert for storage
    product_data['price'] = float(product_data['price'])
    if product_data.get('production_date'):
        product_data['production_date'] = str(product_data['production_date'])

    # Replace
    products[product_id] = product_data

    return product_data


@app.patch(
    "/api/products/{product_id}",
    response_model=Product,
    tags=["Products"]
)
async def patch_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    updates: ProductPatch = None
):
    """
    Partial update of a product (PATCH)

    Demonstrates:
    - ProductPatch model with all fields optional
    - Only provided fields are validated
    - exclude_unset=True to get only provided fields
    """
    if product_id not in products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )

    # Get existing product
    product = products[product_id]

    # Get only fields that were actually provided
    # exclude_unset=True means don't include fields not in request
    update_data = updates.model_dump(exclude_unset=True)

    # Apply updates
    for field, value in update_data.items():
        if field == 'price':
            product[field] = float(value)
        elif field == 'production_date' and value:
            product[field] = str(value)
        else:
            product[field] = value

    # Ensure ID doesn't change
    product['id'] = product_id

    return product


@app.delete(
    "/api/products/{product_id}",
    tags=["Products"]
)
async def delete_product(
    product_id: int = Path(..., gt=0, description="Product ID")
):
    """
    Delete a product

    Returns:
        Success message
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


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Product API - Topic 3: Data Modeling",
        "version": "1.0.0",
        "framework": "FastAPI with Pydantic",
        "topics_demonstrated": [
            "Pydantic models for type safety",
            "Automatic validation",
            "Field validators",
            "Model validators",
            "Separate models for request/response",
            "Automatic OpenAPI documentation"
        ],
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


@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts
    """
    print("========================================")
    print("Product API - Topic 3: Data Modeling")
    print("========================================")
    print("Using Pydantic models for validation")
    print("Swagger UI: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    print("API: http://localhost:8000/api/products")
    print("========================================")


# Run with: uvicorn main:app --reload --port 8000