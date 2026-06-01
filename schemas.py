from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class RawTransaction(BaseModel):
    amount: float
    creditcard: int
    codigo: str
    email: Optional[EmailStr]
    datetime: datetime

class Transaction(BaseModel):
    original_amount: float
    final_amount: float
    creditcard: int
    codigo: str
    email: Optional[EmailStr]
    total_points: Optional[int]
    datetime: datetime


class CustomerPoints(BaseModel): #haría un input y un output pero serían exactamente las mismas
    email: EmailStr
    points: int

