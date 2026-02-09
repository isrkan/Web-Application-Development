# Data modeling with FastAPI and Pydantic

This guide walks through using Pydantic models for data validation in FastAPI. We will replace the plain dictionaries used before with typed Pydantic models, gaining automatic validation, clear error messages and auto-generated documentation.

### Understanding Pydantic
Pydantic is a data validation library that uses Python type hints to validate data automatically, provide clear error messages, convert data to correct types, and generate JSON schemas. FastAPI uses Pydantic as its validation engine.

### What is an API contract?
An API contract is a formal agreement between the API and its consumers (frontend apps, mobile apps, other services). It defines:
* What data the client **must send** (request structure).
* What data the API **will return** (response structure).
* Which fields are required or optional.
* The data types, constraints, and validation rules.
* Possible error responses.

In FastAPI, **Pydantic models *are* the API contract**. By defining request and response models, we explicitly declare:
* “This is exactly what the client is allowed to send”
* “This is exactly what the client will receive back”

FastAPI enforces this contract automatically at runtime and documents it in Swagger UI.

Before, we used `dict` to accept request bodies:
```python
async def create_product(product: dict):
    # No validation - any JSON object is accepted
```

The problem with `dict` is that there is no type checking, no validation, no auto-completion, and poor documentation. With Pydantic models, FastAPI automatically validates all fields, converts types, returns `422` with detailed errors if validation fails, and documents the model schema in Swagger UI.


## Step 1: Project structure
```
DataModeling/
├── README.md
├── pyproject.toml       # Dependencies and project metadata
└── main.py              # Main application file
```

## Step 2: Setting up the environment and installing dependencies
1. Open VS Code and navigate to the project directory in the terminal.
2. Run `uv sync` to create a virtual environment and install all dependencies defined in `pyproject.toml`:
   ```bash
   uv sync
   ```

## Step 3: Defining Pydantic models
The key concept in this topic is model separation. We use different Pydantic models for different operations (Create, Update, Patch, and Response). This allows us to enforce different rules - for example, making a field "Required" when creating an item, but "Optional" when updating it. Each Pydantic model represents a specific API contract for a specific operation. Instead of having one loose data structure, we define multiple contracts:
- One contract for creating a product.
- One contract for updating a product.
- One contract for partial updates.
- One contract for responses.

This makes the API predictable, self-documented, and safe. Clients know exactly which fields are required, which are optional, and what rules apply in each situation.

1. Create a new file named `main.py` and start by importing the required modules:
   ```python
   from fastapi import FastAPI, HTTPException, Path, Query, status
   from pydantic import BaseModel, Field, field_validator
   from typing import Optional, List
   from datetime import date
   from decimal import Decimal
   ```
   - `BaseModel` is the base class for all Pydantic models.
   - `Field` adds validation constraints and documentation metadata to model fields.
   - `field_validator` is a decorator for custom validation logic on individual fields.
   - `Decimal` is used instead of `float` for price fields to avoid floating-point precision issues with monetary values.

2. Define the base product model with common fields, validation constraints, and field validators:
   ```python
   class ProductBase(BaseModel):
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
           ...,
           gt=0,
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
           ge=0,
           description="Stock quantity (optional, must be non-negative)",
           examples=[50, 100]
       )
       production_date: Optional[date] = Field(
           None,
           description="Production date in YYYY-MM-DD format (optional)",
           examples=["2024-01-15"]
       )
   ```
   - `Field(...)` marks a field as required. `Field(None)` makes it optional with a default of `None`.
   - Validation keywords: Constraints like `min_length`, `max_length`, `gt` (greater than), `ge` (greater than or equal) are validated automatically. FastAPI returns `422` if any constraint is violated.
   - `description` and `examples` appear in the Swagger UI documentation, making the API self-documenting.
   - `Decimal` with `max_digits` and `decimal_places` ensures precise monetary values.

3. Add field validators to the base model for custom validation logic. Sometimes simple constraints like `min_length` are not enough. For complex rules, we use `@field_validator`.
   ```python
   class ProductBase(BaseModel):
       # ... fields defined above ...

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
               raise ValueError("Price seems too high. Please verify.")
           return value

       @field_validator('production_date')
       @classmethod
       def validate_production_date(cls, value: Optional[date]) -> Optional[date]:
           if value and value > date.today():
               raise ValueError("Production date cannot be in the future")
           return value
   ```
   - `@field_validator('field_name')`: This marks a method as a validator for a specific field, such as `name`. It runs after the basic type validation (e.g., it ensures the value is a string before checking if it starts with a number).
   - `@classmethod`: Pydantic v2 requires validators to be class methods. This allows them to be called on the class itself during the data-parsing phase.
   - Validators can modify the value (e.g., `value.strip()` removes whitespace) and return the cleaned value.
   - The return value: We must return the value at the end of the validator. This allows us to "clean" the data (like using `.strip()` to remove accidental spaces) before it reaches our database.
   - `ValueError`: When we raise a `ValueError` inside a validator, FastAPI catches it and automatically translates it into a clean `422 Unprocessable Entity` JSON response for the client.

4. Add a model-level validator for validation that depends on multiple fields:
   ```python
   class ProductBase(BaseModel):
       # ... fields and field validators defined above ...

       def model_post_init(self, __context) -> None:
           if self.price > 1000 and not self.description:
               raise ValueError("Products over $1000 must have a description")
           if self.category == "Electronics" and self.stock_quantity is None:
               raise ValueError("Electronics must have stock quantity specified")
   ```
   - `model_post_init` runs after all individual field validators have passed.
   - It has access to all fields via `self`, allowing cross-field validation rules.

5. Define separate models for different operations by extending the base model:
   ```python
   class Product(ProductBase):
       """For responses - includes the ID field."""
       id: int = Field(..., description="Unique product identifier", examples=[1, 2])

       class Config:
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
       """For creation requests - same as base (no ID yet)."""
       pass


   class ProductUpdate(BaseModel):
       """For PUT requests - all fields required for full replacement."""
       name: str = Field(..., min_length=2, max_length=200)
       description: Optional[str] = Field(None, max_length=1000)
       price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
       category: str = Field(..., min_length=2, max_length=100)
       manufacturer: str = Field(..., min_length=2, max_length=200)
       stock_quantity: Optional[int] = Field(None, ge=0)
       production_date: Optional[date] = None

       # Same validators as ProductBase
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
       """For PATCH requests - all fields optional for partial updates."""
       name: Optional[str] = Field(None, min_length=2, max_length=200)
       description: Optional[str] = Field(None, max_length=1000)
       price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
       category: Optional[str] = Field(None, min_length=2, max_length=100)
       manufacturer: Optional[str] = Field(None, min_length=2, max_length=200)
       stock_quantity: Optional[int] = Field(None, ge=0)
       production_date: Optional[date] = None

       # Same validators, but handling Optional values
       @field_validator('name')
       @classmethod
       def validate_name(cls, value: Optional[str]) -> Optional[str]:
           if value:
               value = value.strip()
               if value[0].isdigit():
                   raise ValueError("Product name cannot start with a number")
           return value


   class ProductListResponse(BaseModel):
       """For list responses - wraps products with a count."""
       count: int
       data: List[Product]
   ```
   - `Product` extends `ProductBase` ("inherits" everything from it) and adds the `id` field. This is used for responses.
        - The `Config` class with `json_schema_extra` adds a complete example to the Swagger UI documentation.
   - `ProductCreate` inherits everything from `ProductBase` without changes. It is used for creation requests where the client doesn't provide an ID.
   - `ProductUpdate` redefines all fields as required for `PUT` requests, which replace the entire resource.
   - `ProductPatch` makes all fields optional for `PATCH` requests, which update only the provided fields.
   - `ProductListResponse` wraps a list of products with a count, providing a consistent list response structure.

## Step 4: Creating the API endpoints
1. Create the FastAPI application instance and in-memory storage:
   ```python
   app = FastAPI(
       title="Product API - Data Modeling",
       description="Topic 3: Data Modeling with Pydantic models",
       version="1.0.0"
   )

   products: dict[int, dict] = {}
   next_id = 1
   ```
   - We use a dictionary `products` where the key is the ID. In a real-world app, this would be replaced by a database

2. Add the list and get endpoints, using `response_model` to validate and document the response. The `response_model` parameter defines the response contract of an endpoint.
   ```python
   @app.get("/api/products", response_model=ProductListResponse, tags=["Products"])
   async def get_products(
       category: Optional[str] = Query(None, description="Filter by category"),
       min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price"),
       max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price")
   ):
       """List all products with optional filtering."""
       filtered_products = list(products.values())

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

       return ProductListResponse(count=len(filtered_products), data=filtered_products)


   @app.get("/api/products/{product_id}", response_model=Product, tags=["Products"])
   async def get_product(
       product_id: int = Path(..., gt=0, description="Product ID")
   ):
       """Get a specific product by ID."""
       if product_id not in products:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product with ID {product_id} not found"
           )
       return products[product_id]
   ```
   - `response_model=ProductListResponse` - This is a "contract" that tells FastAPI to validate the response against the model and document it in Swagger UI. This ensures the response always has the correct structure and that clients always receive responses that match the documented contract.
   - `response_model=Product` documents the single-product response and filters out any extra fields not defined in the model.

3. Add the create endpoint, using `ProductCreate` as the request body type:
   ```python
   @app.post(
       "/api/products",
       response_model=Product,
       status_code=status.HTTP_201_CREATED,
       tags=["Products"]
   )
   async def create_product(product: ProductCreate):
       """Create a new product."""
       global next_id

       product_data = product.model_dump()
       product_data['id'] = next_id

       product_data['price'] = float(product_data['price'])
       if product_data.get('production_date'):
           product_data['production_date'] = str(product_data['production_date'])

       products[next_id] = product_data
       next_id += 1

       return product_data
   ```
   - The `product: ProductCreate` parameter tells FastAPI to parse the JSON body into a `ProductCreate` instance. FastAPI automatically validates all fields, runs field validators, runs the model validator, and returns `422` if any check fails.
   - `product.model_dump()` converts the Pydantic model to a dictionary for storage.

4. Add the update and patch endpoints, using `ProductUpdate` and `ProductPatch` respectively:
   ```python
   @app.put("/api/products/{product_id}", response_model=Product, tags=["Products"])
   async def update_product(
       product_id: int = Path(..., gt=0, description="Product ID"),
       product: ProductUpdate = None
   ):
       """Full update of a product (PUT)."""
       if product_id not in products:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product with ID {product_id} not found"
           )

       product_data = product.model_dump()
       product_data['id'] = product_id
       product_data['price'] = float(product_data['price'])
       if product_data.get('production_date'):
           product_data['production_date'] = str(product_data['production_date'])

       products[product_id] = product_data
       return product_data


   @app.patch("/api/products/{product_id}", response_model=Product, tags=["Products"])
   async def patch_product(
       product_id: int = Path(..., gt=0, description="Product ID"),
       updates: ProductPatch = None
   ):
       """Partial update of a product (PATCH)."""
       if product_id not in products:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product with ID {product_id} not found"
           )

       product = products[product_id]
       update_data = updates.model_dump(exclude_unset=True)

       for field, value in update_data.items():
           if field == 'price':
               product[field] = float(value)
           elif field == 'production_date' and value:
               product[field] = str(value)
           else:
               product[field] = value

       product['id'] = product_id
       return product
   ```
   - `ProductUpdate` requires all fields for a full replacement (`PUT`), while `ProductPatch` makes all fields optional for partial updates (`PATCH`).
   - `updates.model_dump(exclude_unset=True)` returns only the fields that were explicitly provided in the request. This is critical for `PATCH` - it distinguishes between a field set to `None` and a field not included at all.

5. Add the delete, root, and startup endpoints:
   ```python
   @app.delete("/api/products/{product_id}", tags=["Products"])
   async def delete_product(
       product_id: int = Path(..., gt=0, description="Product ID")
   ):
       """Delete a product."""
       if product_id not in products:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product with ID {product_id} not found"
           )
       del products[product_id]
       return {"message": "Product deleted successfully", "id": product_id}


   @app.get("/", tags=["Root"])
   async def root():
       """Root endpoint with API information."""
       return {
           "message": "Product API - Topic 3: Data Modeling",
           "version": "1.0.0",
           "docs": "/docs",
       }

   @app.on_event("startup")
   async def startup_event():
       """Runs when the application starts."""
       print("Product API - Topic 3: Data Modeling")
       print("Swagger UI: http://localhost:8000/docs")
   ```

## Step 5: Running the application
1. Start the FastAPI app using Uvicorn:
   ```bash
   uv run uvicorn main:app --reload --port 8000
   ```
   - `uv run` executes the command within the virtual environment managed by `uv`.
   - `--reload` enables auto-reloading when code changes are saved (for development only).

2. Open the web browser and navigate to `http://localhost:8000/` to see the root endpoint response.

## Step 6: Testing the endpoints
Open Swagger UI at `http://localhost:8000/docs` to test all endpoints interactively. The Pydantic models are displayed as schemas in the documentation, showing all fields, types, constraints, and examples.

| Method   | Endpoint                      | Request Model     | Response Model        |
|----------|-------------------------------|-------------------|-----------------------|
| `GET`    | `/api/products`               | Query parameters  | `ProductListResponse` |
| `GET`    | `/api/products/{product_id}`  | Path parameter    | `Product`             |
| `POST`   | `/api/products`               | `ProductCreate`   | `Product`             |
| `PUT`    | `/api/products/{product_id}`  | `ProductUpdate`   | `Product`             |
| `PATCH`  | `/api/products/{product_id}`  | `ProductPatch`    | `Product`             |
| `DELETE` | `/api/products/{product_id}`  | Path parameter    | —                     |

In Swagger UI, click on any endpoint, then click **Try it out** to fill in the parameters and request body, and click **Execute** to send the request and see the response. The validation rules (field constraints, field validators, model validators) are all applied automatically - try sending invalid data to see the detailed `422` error responses.

Swagger UI is not just documentation - it is a live representation of the API contracts. Every schema shown in Swagger UI is generated directly from the Pydantic models.