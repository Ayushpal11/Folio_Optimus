from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class HoldingCreate(BaseModel):
    """Schema for creating a holding"""
    ticker: str = Field(..., max_length=20)
    qty: float = Field(..., gt=0)
    avg_price: float = Field(..., gt=0)
    exchange: str = "NSE"


class HoldingUpdate(BaseModel):
    """Schema for updating a holding"""
    qty: Optional[float] = Field(None, gt=0)
    avg_price: Optional[float] = Field(None, gt=0)
    current_price: Optional[float] = Field(None, gt=0)


class HoldingResponse(BaseModel):
    """Schema for holding response"""
    id: int
    ticker: str
    qty: float
    avg_price: float
    current_price: Optional[float]
    exchange: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SavedPortfolioCreate(BaseModel):
    """Schema for saving a portfolio"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    tickers: str  # JSON array string
    capital: float = Field(..., gt=0)
    risk_tolerance: str
    weights: str  # JSON weights string


class SavedPortfolioResponse(BaseModel):
    """Schema for saved portfolio response"""
    id: UUID
    name: str
    description: Optional[str]
    capital: float
    risk_tolerance: str
    expected_return: Optional[float]
    volatility: Optional[float]
    sharpe_ratio: Optional[float]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BacktestCreate(BaseModel):
    """Schema for creating backtest"""
    ticker: str
    signal: str
    entry_date: datetime
    entry_price: float
    target_price: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    return_pct: Optional[float] = None
    days_held: Optional[int] = None


class BacktestResponse(BaseModel):
    """Schema for backtest response"""
    id: UUID
    ticker: str
    signal: str
    entry_price: float
    exit_price: Optional[float]
    return_pct: Optional[float]
    days_held: Optional[int]
    entry_date: datetime
    exit_date: Optional[datetime]

    class Config:
        from_attributes = True
