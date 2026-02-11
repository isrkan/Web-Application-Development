"""
SQLAlchemy Models - Database Table Definitions

This module defines SQLAlchemy models for database tables:
- Product model with all fields
- Column types and constraints
- Relationships (for future topics)

SQLAlchemy provides:
- ORM mapping (Python objects ↔ database rows)
- Type safety
- Query interface
- Relationship management
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, Index
from sqlalchemy.sql import func
from datetime import date
from .database import Base


class Product(Base):
    """
    Product model - Maps to 'products' table in database

    SQLAlchemy features:
    - __tablename__ defines table name
    - Column() defines database columns
    - Column types map to database types
    - Constraints define data rules
    - Indexes improve query performance

    This is similar to Django models but with more explicit configuration
    """

    # Table name in database
    __tablename__ = "products"

    # ==================== Columns ====================

    # Primary key with auto-increment
    # Integer maps to INTEGER
    # primary_key=True makes this the primary key
    # autoincrement=True enables auto-increment (default for Integer primary keys)
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique product identifier"
    )

    # Product name - required
    # String(200) maps to VARCHAR(200)
    # nullable=False adds NOT NULL constraint
    # index=True creates an index for faster queries
    name = Column(
        String(200),
        nullable=False,
        index=True,
        comment="Product name"
    )

    # Product description - optional
    # Text maps to TEXT type in MySQL (for longer content)
    # nullable=True allows NULL (default)
    description = Column(
        Text,
        nullable=True,
        comment="Product description"
    )

    # Product price - required decimal
    # Numeric(10, 2) maps to DECIMAL(10, 2)
    # precision=10, scale=2 means up to 99.99999999
    # nullable=False makes it required
    price = Column(
        Numeric(precision=10, scale=2),
        nullable=False,
        index=True,
        comment="Product price"
    )

    # Product category - required
    # index=True for fast category filtering
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Product category"
    )

    # Manufacturer - required
    manufacturer = Column(
        String(200),
        nullable=False,
        index=True,
        comment="Manufacturer name"
    )

    # Stock quantity - optional integer
    stock_quantity = Column(
        Integer,
        nullable=True,
        comment="Stock quantity"
    )

    # Production date - optional date
    # Date maps to DATE type
    production_date = Column(
        Date,
        nullable=True,
        comment="Production date"
    )

    # Timestamp fields - automatically managed
    # DateTime for timestamps
    # server_default=func.now() sets default to current time (database-side)
    # onupdate=func.now() updates on every update (for updated_at)
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp"
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )

    # ==================== Indexes ====================

    # Composite index for common queries
    # Speeds up queries filtering by category and price together
    __table_args__ = (
        Index('idx_category_price', 'category', 'price'),
    )

    # ==================== String Representation ====================

    def __repr__(self):
        """
        String representation for debugging

        Returns:
            str: Product representation
        """
        return (
            f"Product(id={self.id}, name='{self.name}', "
            f"price={self.price}, category='{self.category}')"
        )

    def __str__(self):
        """
        Human-readable string representation

        Returns:
            str: Product name and ID
        """
        return f"{self.name} (ID: {self.id})"