"""
Product API - Database Integration with SQLAlchemy

This application demonstrates database integration using SQLAlchemy:
- Async SQLAlchemy for non-blocking database operations
- Separate database models (SQLAlchemy) and schemas (Pydantic)
- CRUD operations with database persistence
- Query filtering with SQLAlchemy
- Automatic database initialization

Differences from Topic 3:
- Topic 3: In-memory dict storage
- Topic 4: MySQL database with SQLAlchemy ORM

FastAPI + SQLAlchemy Benefits:
- Async database operations (non-blocking)
- Type-safe queries
- Automatic migrations (with Alembic)
- Database abstraction (works with MySQL, PostgreSQL, SQLite, etc.)
"""

from fastapi import FastAPI, HTTPException, Depends, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional
from decimal import Decimal

from .database import get_session, init_db
from .models import Product as ProductModel
from .schemas import (
    ProductCreate,
    ProductUpdate,
    ProductPatch,
    ProductResponse,
    ProductListResponse
)

# Create FastAPI app
app = FastAPI(
    title="Product API - Database Integration",
    description="Topic 4: Database Integration with SQLAlchemy",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """
    Initialize database on startup

    Creates all tables if they don't exist
    """
    print("========================================")
    print("Product API - Topic 4: Database Integration")
    print("========================================")
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")
    print("Using SQLAlchemy with async MySQL")
    print("Swagger UI: http://localhost:8000/docs")
    print("========================================")


# ==================== Endpoints ====================

@app.get(
    "/api/products",
    response_model=ProductListResponse,
    tags=["Products"]
)
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    session: AsyncSession = Depends(get_session)
):
    """
    List all products with optional filtering

    Demonstrates:
    - SQLAlchemy select() for queries
    - where() for filtering
    - Async database operations with await
    - Dependency injection for database session
    """
    # Build query
    # select(ProductModel) creates SELECT * FROM products
    query = select(ProductModel)

    # Apply filters
    filters = []
    if category:
        # ProductModel.category == category creates WHERE clause
        filters.append(ProductModel.category == category)

    if min_price is not None:
        # >= operator
        filters.append(ProductModel.price >= min_price)

    if max_price is not None:
        # <= operator
        filters.append(ProductModel.price <= max_price)

    if filters:
        # and_() combines filters with AND
        query = query.where(and_(*filters))

    # Execute query
    # await is required for async operations
    result = await session.execute(query)

    # Get all results
    # scalars() returns just the Product objects (not tuples)
    # all() fetches all rows
    products = result.scalars().all()

    return ProductListResponse(
        count=len(products),
        data=products
    )


@app.get(
    "/api/products/{product_id}",
    response_model=ProductResponse,
    tags=["Products"]
)
async def get_product(
    product_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific product by ID

    Demonstrates:
    - session.get() for fetching by primary key
    - HTTPException for 404 errors
    """
    # Get by primary key
    # session.get(Model, id) is shorthand for SELECT WHERE id = ?
    product = await session.get(ProductModel, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    return product


@app.post(
    "/api/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Products"]
)
async def create_product(
    product: ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new product

    Demonstrates:
    - Creating database records
    - session.add() to stage object
    - session.commit() to save to database
    - session.refresh() to get generated ID and timestamps
    """
    # Convert Pydantic model to SQLAlchemy model
    # **product.model_dump() unpacks the dictionary
    db_product = ProductModel(**product.model_dump())

    # Add to session (stages for INSERT)
    session.add(db_product)

    try:
        # Commit transaction (executes INSERT)
        await session.commit()

        # Refresh to get database-generated values (id, created_at, updated_at)
        await session.refresh(db_product)

        return db_product

    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error"
        )


@app.put(
    "/api/products/{product_id}",
    response_model=ProductResponse,
    tags=["Products"]
)
async def update_product(
    product_id: int = Path(..., gt=0),
    product_update: ProductUpdate = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Full update of a product (PUT)

    Demonstrates:
    - Fetching existing record
    - Updating all fields
    - Committing changes
    """
    # Get existing product
    db_product = await session.get(ProductModel, product_id)

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    # Update all fields
    update_data = product_update.model_dump()
    for field, value in update_data.items():
        setattr(db_product, field, value)

    # Commit changes
    await session.commit()
    await session.refresh(db_product)

    return db_product


@app.patch(
    "/api/products/{product_id}",
    response_model=ProductResponse,
    tags=["Products"]
)
async def patch_product(
    product_id: int = Path(..., gt=0),
    product_patch: ProductPatch = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Partial update of a product (PATCH)

    Demonstrates:
    - Updating only provided fields
    - exclude_unset=True to get only set fields
    """
    db_product = await session.get(ProductModel, product_id)

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    # Get only fields that were provided
    # exclude_unset=True excludes fields not in request
    update_data = product_patch.model_dump(exclude_unset=True)

    # Update only provided fields
    for field, value in update_data.items():
        setattr(db_product, field, value)

    await session.commit()
    await session.refresh(db_product)

    return db_product


@app.delete(
    "/api/products/{product_id}",
    tags=["Products"]
)
async def delete_product(
    product_id: int = Path(..., gt=0),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a product

    Demonstrates:
    - session.delete() for deletion
    """
    db_product = await session.get(ProductModel, product_id)

    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    # Delete from database
    await session.delete(db_product)
    await session.commit()

    return {
        "message": "Product deleted successfully",
        "id": product_id
    }


@app.get(
    "/api/products/category/{category}",
    response_model=list[ProductResponse],
    tags=["Products"]
)
async def get_products_by_category(
    category: str = Path(..., min_length=1),
    session: AsyncSession = Depends(get_session)
):
    """
    Get products by category

    Demonstrates:
    - WHERE clause filtering
    """
    query = select(ProductModel).where(ProductModel.category == category)
    result = await session.execute(query)
    products = result.scalars().all()

    return products


@app.get(
    "/api/products/search/",
    response_model=list[ProductResponse],
    tags=["Products"]
)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    session: AsyncSession = Depends(get_session)
):
    """
    Search products by name

    Demonstrates:
    - LIKE query with contains()
    - Case-insensitive search
    """
    # ProductModel.name.contains(q) creates LIKE '%q%'
    # ilike() for case-insensitive (PostgreSQL)
    query = select(ProductModel).where(ProductModel.name.contains(q))
    result = await session.execute(query)
    products = result.scalars().all()

    return products


@app.get(
    "/api/products/expensive/",
    response_model=list[ProductResponse],
    tags=["Products"]
)
async def get_expensive_products(
    session: AsyncSession = Depends(get_session)
):
    """
    Get expensive products (price > $1000)

    Demonstrates:
    - Comparison operators (>)
    - order_by() for sorting
    """
    query = select(ProductModel).where(
        ProductModel.price > 1000
    ).order_by(ProductModel.price.desc())

    result = await session.execute(query)
    products = result.scalars().all()

    return products


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Product API - Topic 4: Database Integration",
        "version": "1.0.0",
        "framework": "FastAPI with SQLAlchemy",
        "database": "MySQL (async)",
        "topics_demonstrated": [
            "Async SQLAlchemy ORM",
            "Separate models and schemas",
            "CRUD operations with database",
            "Query filtering",
            "Dependency injection",
            "Automatic database initialization"
        ],
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Run with: uvicorn main:app --reload --port 8000