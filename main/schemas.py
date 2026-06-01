from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class RawTransaction(BaseModel):
    amount: float | None
    creditcard: int | None
    codigo: str | None
    email: Optional[EmailStr] | None
    datetime: datetime | None

class Transaction(BaseModel):
    original_amount: float
    final_amount: float
    creditcard: int
    codigo: str
    email: Optional[EmailStr] | None = None
    total_points: Optional[int] | None = None
    datetime: datetime
