from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base


class User(Base):
    """User model for authentication and portfolio management"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("SavedPortfolio", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Holding(Base):
    """Portfolio holding model"""
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    qty = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    exchange = Column(String(10), default="NSE", nullable=False)
    current_price = Column(Float)  # Updated periodically
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="holdings")

    def __repr__(self):
        return f"<Holding {self.ticker} x{self.qty}>"


class SavedPortfolio(Base):
    """Saved portfolio optimization result"""
    __tablename__ = "saved_portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    tickers = Column(String(1000), nullable=False)  # JSON array as string
    capital = Column(Float, nullable=False)
    risk_tolerance = Column(String(20), nullable=False)
    weights = Column(String(2000), nullable=False)  # JSON weights as string
    expected_return = Column(Float)
    volatility = Column(Float)
    sharpe_ratio = Column(Float)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolios")

    def __repr__(self):
        return f"<SavedPortfolio {self.name}>"


class Backtest(Base):
    """Backtest result model"""
    __tablename__ = "backtests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    signal = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    entry_date = Column(DateTime, nullable=False)
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    exit_date = Column(DateTime)
    exit_price = Column(Float)
    return_pct = Column(Float)
    days_held = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Backtest {self.ticker} {self.signal}>"
