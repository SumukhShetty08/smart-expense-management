from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    model_config = ConfigDict(from_attributes=True)

class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    kind: Literal["income", "expense"]
    color: str = "#64748b"

class CategoryOut(CategoryIn):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TransactionIn(BaseModel):
    category_id: int | None = None
    kind: Literal["income", "expense"]
    amount: float = Field(gt=0, le=100000000)
    description: str = Field(min_length=1, max_length=250)
    transaction_date: date
    recurring: bool = False

class TransactionOut(BaseModel):
    id: int
    category_id: int | None
    kind: str
    amount: float
    description: str
    transaction_date: date
    recurring: bool
    model_config = ConfigDict(from_attributes=True)

class BudgetIn(BaseModel):
    category_id: int | None = None
    name: str = Field(min_length=1, max_length=100)
    monthly_limit: float = Field(gt=0)
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")

class BudgetOut(BudgetIn):
    id: int
    model_config = ConfigDict(from_attributes=True)
