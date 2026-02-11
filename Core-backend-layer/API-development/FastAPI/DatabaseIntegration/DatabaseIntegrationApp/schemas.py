"""
Pydantic Schemas - Request/Response Validation

This module defines Pydantic models for API validation:
- Separate from database models (SQLAlchemy)
- Used for request validation and response serialization
- Type safety and automatic documentation

Why separate schemas from models?
- Database models (SQLAlchemy) handle database operations
- Pydantic schemas handle API validation and serialization
- Clean separation of concerns
- Different validation rules for create vs update
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class ProductBase(BaseModel):
    """
    Base Product schema with common fields

    Used as base for other schemas (create, update, response)
    """

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Product name",
        examples=["Laptop"]
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Product description",
        examples=["High-performance laptop"]
    )

    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Product price",
        examples=[1299.99]
    )

    category: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Product category",
        examples=["Electronics"]
    )

    manufacturer: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Manufacturer name",
        examples=["TechCorp"]
    )

    stock_quantity: Optional[int] = Field(
        None,
        ge=0,
        description="Stock quantity",
        examples=[50]
    )

    production_date: Optional[date] = Field(
        None,
        description="Production date",
        examples=["2024-01-15"]
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate product name"""
        value = value.strip()
        if value[0].isdigit():
            raise ValueError("Product name cannot start with a number")
        return value

    @field_validator('price')
    @classmethod
    def validate_price(cls, value: Decimal) -> Decimal:
        """Validate product price"""
        if value > 1000000:
            raise ValueError("Price seems too high")
        return value

    @field_validator('production_date')
    @classmethod
    def validate_production_date(cls, value: Optional[date]) -> Optional[date]:
        """Validate production date"""
        if value and value > date.today():
            raise ValueError("Production date cannot be in the future")
        return value


class ProductCreate(ProductBase):
    """
    Schema for creating products

    Same as ProductBase - no ID yet
    """
    pass


class ProductUpdate(ProductBase):
    """
    Schema for full update (PUT)

    All fields required except ID
    """
    pass


class ProductPatch(BaseModel):
    """
    Schema for partial update (PATCH)

    All fields optional
    """

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


class ProductResponse(ProductBase):
    """
    Schema for product responses

    Includes database-generated fields (id, timestamps)

    ConfigDict allows reading from ORM objects:
    - from_attributes=True enables product.id, product.name, etc.
    - Previously orm_mode=True in Pydantic v1
    """

    id: int = Field(..., description="Product ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Pydantic v2 configuration
    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """
    Schema for list responses with metadata
    """

    count: int = Field(..., description="Number of products")
    data: list[ProductResponse] = Field(..., description="List of products")