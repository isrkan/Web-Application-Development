# Database integration with FastAPI and SQLAlchemy

This guide walks through integrating a database into the FastAPI application using async SQLAlchemy. We will replace the in-memory dictionary storage with a MySQL database, separate database models (SQLAlchemy) from API schemas (Pydantic), and use dependency injection for database session management.

#### Understanding the architecture
Before, we stored products in a Python dictionary that was lost on every restart. Now we introduce a proper database layer with a clear separation of concerns:
- **Database models (SQLAlchemy)** define the database table structure and handle database operations (how data is stored).
- **Pydantic schemas** define the API request/response validation (how data enters and leaves the API).
- **Database sessions** are injected into endpoints using FastAPI's dependency injection system, ensuring each request gets its own session that is automatically closed afterward.
- **Async SQLAlchemy** provides non-blocking database operations using `async`/`await`, matching FastAPI's async nature.


## Step 1: Project structure
This topic introduces a multi-file structure to separate concerns:
```
DatabaseIntegration/
├── README.md
├── pyproject.toml       # Dependencies and project metadata
└── DatabaseIntegrationApp/
    ├── __init__.py          # Makes this directory a Python package
    ├── database.py          # Database engine, session and initialization
    ├── models.py            # SQLAlchemy models (database tables)
    ├── schemas.py           # Pydantic schemas (API validation)
    └── main.py              # FastAPI application and endpoints
```

The `__init__.py` file makes this directory a Python package, allowing the modules to import from each other using relative imports (e.g., `from .database import Base`).

## Step 2: Setting up the environment and installing dependencies
1. Open VS Code and navigate to the project directory in the terminal.
2. Run `uv sync` to create a virtual environment and install all dependencies defined in `pyproject.toml`:
   ```bash
   uv sync
   ```
   - This installs `fastapi`, `uvicorn`, `sqlalchemy`, `aiomysql` (async MySQL driver), and `pydantic`.

## Step 3: Configuring the database connection
1. Create `database.py` and start by setting up the async database engine:
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.orm import declarative_base

   DATABASE_URL = "mysql+aiomysql://root:password@localhost:3306/products_db"

   engine = create_async_engine(
       DATABASE_URL,
       echo=True,  # Set to False in production
       future=True,
       pool_recycle=3600
   )
   ```
   - `mysql+aiomysql://root:password@localhost:3306/products_db` specifies the database dialect (`mysql`), the async driver (`aiomysql`), the credentials (`root:password`), the host and port (`localhost:3306`), and the database name (`products_db`). The MySQL server must be running and the database must exist before starting the application.
   - `echo=True` logs all SQL statements to the console, which is useful for debugging during development.
   - `pool_recycle=3600` closes and recreates idle connections after 1 hour to prevent MySQL "gone away" errors on long-running connections.

2. Create the async session factory and the base class for models:
   ```python
   async_session_maker = async_sessionmaker(
       engine,
       class_=AsyncSession,
       expire_on_commit=False
   )

   Base = declarative_base()
   ```
   - `async_sessionmaker` creates a factory that produces new `AsyncSession` instances. Each session represents a connection to the database.
   - `expire_on_commit=False` keeps objects usable after a commit. Without this, accessing attributes after commit would require another database query.
   - `Base` is the base class that all SQLAlchemy models will inherit from. It provides the ORM mapping functionality.

3. Add the session dependency and database initialization functions:
   ```python
   async def get_session() -> AsyncSession:
       async with async_session_maker() as session:
           try:
               yield session
           finally:
               await session.close()


   async def init_db():
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
   ```
   - `get_session` is a dependency function used with FastAPI's `Depends()`. It creates a new session for each request and ensures the session is closed afterward using `try`/`finally`.
   - The `yield` keyword makes this an async generator, which FastAPI uses for dependency injection with cleanup.
   - `init_db` creates all tables defined in the models. It is called once on application startup. In production, database migrations with Alembic should be used instead.

## Step 4: Defining SQLAlchemy models
1. Create `models.py` and define the `Product` model that maps to the `products` database table:
   ```python
   from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, Index
   from sqlalchemy.sql import func
   from .database import Base


   class Product(Base):
       __tablename__ = "products"

       id = Column(Integer, primary_key=True, autoincrement=True, comment="Unique product identifier")
       name = Column(String(200), nullable=False, index=True, comment="Product name")
       description = Column(Text, nullable=True, comment="Product description")
       price = Column(Numeric(precision=10, scale=2), nullable=False, index=True, comment="Product price")
       category = Column(String(100), nullable=False, index=True, comment="Product category")
       manufacturer = Column(String(200), nullable=False, index=True, comment="Manufacturer name")
       stock_quantity = Column(Integer, nullable=True, comment="Stock quantity")
       production_date = Column(Date, nullable=True, comment="Production date")
       created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="Creation timestamp")
       updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="Last update timestamp")

       __table_args__ = (
           Index('idx_category_price', 'category', 'price'),
       )
   ```
   - `__tablename__` sets the actual table name in the database.
   - Each `Column()` defines a database column. The first argument is the column type (`Integer`, `String(200)`, `Text`, `Numeric(10, 2)`, `Date`, `DateTime`). `Text` is used for longer content like descriptions since MySQL requires an explicit length for `String`/`VARCHAR` columns.
   - `primary_key=True` with `autoincrement=True` makes `id` an auto-incrementing primary key.
   - `nullable=False` adds a `NOT NULL` constraint, making the field required at the database level.
   - `index=True` creates a database index on the column for faster queries.
   - `server_default=func.now()` sets the default value to the current timestamp at the database level. `onupdate=func.now()` automatically updates the timestamp on every update.
   - `__table_args__` defines a composite index on `category` and `price` together, speeding up queries that filter by both columns.

2. Add string representations for debugging:
   ```python
   class Product(Base):
       # ... columns defined above ...

       def __repr__(self):
           return (
               f"Product(id={self.id}, name='{self.name}', "
               f"price={self.price}, category='{self.category}')"
           )

       def __str__(self):
           return f"{self.name} (ID: {self.id})"
   ```

## Step 5: Defining Pydantic schemas
1. Create `schemas.py` with the Pydantic schemas for API validation. The response schema now includes database-generated fields:
   ```python
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   from typing import Optional
   from datetime import date, datetime
   from decimal import Decimal


   class ProductBase(BaseModel):
       name: str = Field(..., min_length=2, max_length=200, description="Product name", examples=["Laptop"])
       description: Optional[str] = Field(None, max_length=1000, description="Product description")
       price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="Product price", examples=[1299.99])
       category: str = Field(..., min_length=2, max_length=100, description="Product category", examples=["Electronics"])
       manufacturer: str = Field(..., min_length=2, max_length=200, description="Manufacturer name", examples=["TechCorp"])
       stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity", examples=[50])
       production_date: Optional[date] = Field(None, description="Production date", examples=["2024-01-15"])

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
   ```
   - The `ProductBase`, field constraints, and field validators are the same to what we covered so far.

2. Define the operation-specific schemas:
   ```python
   class ProductCreate(ProductBase):
       """For creation requests - same as base (no ID yet)."""
       pass


   class ProductUpdate(ProductBase):
       """For PUT requests - all fields required."""
       pass


   class ProductPatch(BaseModel):
       """For PATCH requests - all fields optional."""
       name: Optional[str] = Field(None, min_length=2, max_length=200)
       description: Optional[str] = Field(None, max_length=1000)
       price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
       category: Optional[str] = Field(None, min_length=2, max_length=100)
       manufacturer: Optional[str] = Field(None, min_length=2, max_length=200)
       stock_quantity: Optional[int] = Field(None, ge=0)
       production_date: Optional[date] = None

       @field_validator('name')
       @classmethod
       def validate_name(cls, value: Optional[str]) -> Optional[str]:
           if value:
               value = value.strip()
               if value[0].isdigit():
                   raise ValueError("Product name cannot start with a number")
           return value
   ```

3. Define the response schemas that include database-generated fields:
   ```python
   class ProductResponse(ProductBase):
       id: int = Field(..., description="Product ID")
       created_at: datetime = Field(..., description="Creation timestamp")
       updated_at: datetime = Field(..., description="Last update timestamp")

       model_config = ConfigDict(from_attributes=True)


   class ProductListResponse(BaseModel):
       count: int = Field(..., description="Number of products")
       data: list[ProductResponse] = Field(..., description="List of products")
   ```
   - `ProductResponse` adds `id`, `created_at`, and `updated_at` which are generated by the database.
   - `model_config = ConfigDict(from_attributes=True)` allows Pydantic to read data directly from SQLAlchemy model attributes (e.g., `product.name`) instead of requiring a dictionary. This was called `orm_mode = True` in Pydantic v1.
   - This configuration is what bridges SQLAlchemy models and Pydantic schemas - without it, returning a SQLAlchemy object from an endpoint would fail.

## Step 6: Creating the API endpoints
1. Create `main.py` with imports and the FastAPI application instance. The database is initialized on startup:
   ```python
   from fastapi import FastAPI, HTTPException, Depends, status, Path, Query
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, and_
   from sqlalchemy.exc import IntegrityError
   from typing import Optional
   from decimal import Decimal

   from .database import get_session, init_db
   from .models import Product as ProductModel
   from .schemas import (
       ProductCreate, ProductUpdate, ProductPatch,
       ProductResponse, ProductListResponse
   )

   app = FastAPI(
       title="Product API - Database Integration",
       description="Topic 4: Database Integration with SQLAlchemy",
       version="1.0.0"
   )

   @app.on_event("startup")
   async def startup_event():
       await init_db()
       print("Product API - Database initialized")
       print("Swagger UI: http://localhost:8000/docs")
   ```
   - `from .database import get_session, init_db` uses relative imports within the package.
   - `Product as ProductModel` aliases the SQLAlchemy model to avoid confusion with the Pydantic schema.
   - `await init_db()` in the startup event creates all tables if they don't exist. The MySQL database must already exist (see Step 7), but the tables are created automatically.

2. Add the list endpoint with query filtering using SQLAlchemy's `select()` API:
   ```python
   @app.get("/api/products", response_model=ProductListResponse, tags=["Products"])
   async def get_products(
       category: Optional[str] = Query(None, description="Filter by category"),
       min_price: Optional[Decimal] = Query(None, ge=0),
       max_price: Optional[Decimal] = Query(None, ge=0),
       session: AsyncSession = Depends(get_session)
   ):
       """List all products with optional filtering."""
       query = select(ProductModel)

       filters = []
       if category:
           filters.append(ProductModel.category == category)
       if min_price is not None:
           filters.append(ProductModel.price >= min_price)
       if max_price is not None:
           filters.append(ProductModel.price <= max_price)
       if filters:
           query = query.where(and_(*filters))

       result = await session.execute(query)
       products = result.scalars().all()

       return ProductListResponse(count=len(products), data=products)
   ```
   - `session: AsyncSession = Depends(get_session)` injects a database session into the endpoint using FastAPI's dependency injection. The session is created before the function runs and closed automatically afterward.
   - `select(ProductModel)` builds a `SELECT * FROM products` query. Filters are added dynamically using `.where()` and combined with `and_()`.
   - `await session.execute(query)` executes the query asynchronously. `result.scalars().all()` extracts the `Product` objects from the result rows.

3. Add the get-by-ID and create endpoints:
   ```python
   @app.get("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
   async def get_product(
       product_id: int = Path(..., gt=0),
       session: AsyncSession = Depends(get_session)
   ):
       """Get a specific product by ID."""
       product = await session.get(ProductModel, product_id)
       if not product:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product {product_id} not found"
           )
       return product


   @app.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, tags=["Products"])
   async def create_product(
       product: ProductCreate,
       session: AsyncSession = Depends(get_session)
   ):
       """Create a new product."""
       db_product = ProductModel(**product.model_dump())
       session.add(db_product)

       try:
           await session.commit()
           await session.refresh(db_product)
           return db_product
       except IntegrityError:
           await session.rollback()
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail="Database integrity error"
           )
   ```
   - `await session.get(ProductModel, product_id)` fetches a record by primary key. This is a shorthand for `SELECT * FROM products WHERE id = ?`.
   - `ProductModel(**product.model_dump())` converts the validated Pydantic schema to a SQLAlchemy model instance by unpacking the dictionary as keyword arguments.
   - `session.add(db_product)` stages the object for insertion. `await session.commit()` executes the `INSERT` statement.
   - `await session.refresh(db_product)` reloads the object from the database to get the auto-generated `id`, `created_at`, and `updated_at` values.
   - The `try`/`except IntegrityError` handles database constraint violations (e.g., unique constraints). If an error occurs, `session.rollback()` undoes the transaction.

4. Add the update and patch endpoints:
   ```python
   @app.put("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
   async def update_product(
       product_id: int = Path(..., gt=0),
       product_update: ProductUpdate = None,
       session: AsyncSession = Depends(get_session)
   ):
       """Full update of a product (PUT)."""
       db_product = await session.get(ProductModel, product_id)
       if not db_product:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product {product_id} not found"
           )

       update_data = product_update.model_dump()
       for field, value in update_data.items():
           setattr(db_product, field, value)

       await session.commit()
       await session.refresh(db_product)
       return db_product


   @app.patch("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
   async def patch_product(
       product_id: int = Path(..., gt=0),
       product_patch: ProductPatch = None,
       session: AsyncSession = Depends(get_session)
   ):
       """Partial update of a product (PATCH)."""
       db_product = await session.get(ProductModel, product_id)
       if not db_product:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Product {product_id} not found"
           )

       update_data = product_patch.model_dump(exclude_unset=True)
       for field, value in update_data.items():
           setattr(db_product, field, value)

       await session.commit()
       await session.refresh(db_product)
       return db_product
   ```
   - `setattr(db_product, field, value)` dynamically sets attributes on the SQLAlchemy model. SQLAlchemy tracks these changes and generates the appropriate `UPDATE` statement on commit.
   - For `PATCH`, `exclude_unset=True` ensures only fields that were explicitly provided in the request are updated.

5. Add additional query endpoints for searching and filtering:
   ```python
   @app.get("/api/products/category/{category}", response_model=list[ProductResponse], tags=["Products"])
   async def get_products_by_category(
       category: str = Path(..., min_length=1),
       session: AsyncSession = Depends(get_session)
   ):
       """Get products by category."""
       query = select(ProductModel).where(ProductModel.category == category)
       result = await session.execute(query)
       return result.scalars().all()


   @app.get("/api/products/search/", response_model=list[ProductResponse], tags=["Products"])
   async def search_products(
       q: str = Query(..., min_length=1, description="Search query"),
       session: AsyncSession = Depends(get_session)
   ):
       """Search products by name."""
       query = select(ProductModel).where(ProductModel.name.contains(q))
       result = await session.execute(query)
       return result.scalars().all()


   @app.get("/api/products/expensive/", response_model=list[ProductResponse], tags=["Products"])
   async def get_expensive_products(
       session: AsyncSession = Depends(get_session)
   ):
       """Get expensive products (price > $1000), sorted by price descending."""
       query = select(ProductModel).where(
           ProductModel.price > 1000
       ).order_by(ProductModel.price.desc())
       result = await session.execute(query)
       return result.scalars().all()
   ```
   - `.where(ProductModel.category == category)` creates a `WHERE category = ?` clause.
   - `.where(ProductModel.name.contains(q))` creates a `WHERE name LIKE '%q%'` clause for text search.
   - `.order_by(ProductModel.price.desc())` adds `ORDER BY price DESC` for sorting.

6. Add the root endpoint:
   ```python
   @app.get("/", tags=["Root"])
   async def root():
       """Root endpoint with API information."""
       return {
           "message": "Product API - Topic 4: Database Integration",
           "version": "1.0.0",
           "database": "MySQL (async)",
           "docs": "/docs",
       }
   ```

## Step 7: Running the application
1. Make sure the MySQL server is running and create the database:
   ```sql
   CREATE DATABASE products_db;
   ```
   - Update the `DATABASE_URL` in `database.py` with the correct MySQL credentials, host, port, and database name if they differ from the defaults.

2. Since this is a Python package (has `__init__.py`), run it as a module from the parent directory:
   ```bash
   cd ..
   uv run uvicorn DatabaseIntegrationApp.main:app --reload --port 8000
   ```
   - The tables are created automatically on the first run. Data persists across restarts.

3. Open the web browser and navigate to `http://localhost:8000/` to see the root endpoint.

## Step 8: Testing the endpoints
Open Swagger UI at `http://localhost:8000/docs` to test all endpoints interactively. The data is now persisted in the MySQL database, so products created in one session will still be available after restarting the server.

| Method   | Endpoint                              | Description                        |
|----------|---------------------------------------|------------------------------------|
| `GET`    | `/api/products`                       | List all products (with filtering) |
| `GET`    | `/api/products/{product_id}`          | Get a specific product             |
| `POST`   | `/api/products`                       | Create a new product               |
| `PUT`    | `/api/products/{product_id}`          | Full update of a product           |
| `PATCH`  | `/api/products/{product_id}`          | Partial update of a product        |
| `DELETE` | `/api/products/{product_id}`          | Delete a product                   |
| `GET`    | `/api/products/category/{category}`   | Get products by category           |
| `GET`    | `/api/products/search/?q=...`         | Search products by name            |
| `GET`    | `/api/products/expensive/`            | Get products over $1000            |

In Swagger UI, click on any endpoint, then click **Try it out** to fill in the parameters and request body, and click **Execute** to send the request and see the response.
