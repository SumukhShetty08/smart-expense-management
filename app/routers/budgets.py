from datetime import date
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.deps import get_current_user
from app.models import Budget, Transaction, Category, User
from app.schemas import BudgetIn, BudgetOut

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])

@router.get("")
def list_budgets(month: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    month = month or date.today().strftime("%Y-%m")
    budgets = db.scalars(select(Budget).where(Budget.user_id == user.id, Budget.month == month)).all()
    result = []
    for b in budgets:
        month_start = date.fromisoformat(month + "-01")
        month_end = date(month_start.year, month_start.month, monthrange(month_start.year, month_start.month)[1])
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id, Transaction.kind == "expense",
            Transaction.transaction_date >= month_start, Transaction.transaction_date <= month_end)
        if b.category_id:
            stmt = stmt.where(Transaction.category_id == b.category_id)
        spent = float(db.scalar(stmt) or 0)
        pct = round(spent / b.monthly_limit * 100, 1)
        result.append({"id": b.id, "name": b.name, "category_id": b.category_id, "month": b.month,
                       "monthly_limit": b.monthly_limit, "spent": spent, "remaining": round(b.monthly_limit-spent, 2),
                       "utilization": pct, "alert": "exceeded" if pct >= 100 else ("warning" if pct >= 80 else "healthy")})
    return result

@router.post("", response_model=BudgetOut, status_code=201)
def create_budget(payload: BudgetIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.category_id:
        cat = db.get(Category, payload.category_id)
        if not cat or cat.user_id != user.id or cat.kind != "expense":
            raise HTTPException(status_code=400, detail="Budget category must be one of your expense categories")
    item = Budget(user_id=user.id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.scalar(select(Budget).where(Budget.id == budget_id, Budget.user_id == user.id))
    if not item: raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(item); db.commit()
