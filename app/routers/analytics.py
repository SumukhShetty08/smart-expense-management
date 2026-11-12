from datetime import date
from calendar import monthrange
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.deps import get_current_user
from app.models import Transaction, Category, User

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary")
def summary(month: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    month = month or date.today().strftime("%Y-%m")
    start = date.fromisoformat(month + "-01")
    end = date(start.year, start.month, monthrange(start.year, start.month)[1])
    base = select(Transaction).where(Transaction.user_id == user.id, Transaction.transaction_date >= start, Transaction.transaction_date <= end)
    income = db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.user_id == user.id, Transaction.kind == "income", Transaction.transaction_date.between(start, end))) or 0
    expense = db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.user_id == user.id, Transaction.kind == "expense", Transaction.transaction_date.between(start, end))) or 0
    count = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.user_id == user.id, Transaction.transaction_date.between(start, end))) or 0
    grouped = db.execute(select(Category.name, func.sum(Transaction.amount)).join(Transaction, Transaction.category_id == Category.id)
                         .where(Transaction.user_id == user.id, Transaction.kind == "expense", Transaction.transaction_date.between(start, end))
                         .group_by(Category.name).order_by(func.sum(Transaction.amount).desc())).all()
    return {"month": month, "income": round(float(income),2), "expenses": round(float(expense),2),
            "balance": round(float(income-expense),2), "transaction_count": count,
            "categories": [{"name": name, "amount": round(float(amount),2)} for name, amount in grouped]}

@router.get("/trend")
def trend(months: int = 6, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    months = max(1, min(months, 24))
    today = date.today()
    result = []
    for offset in reversed(range(months)):
        index = today.year * 12 + today.month - 1 - offset
        year, month_num = divmod(index, 12)
        month_num += 1
        start = date(year, month_num, 1)
        end = date(year, month_num, monthrange(year, month_num)[1])
        vals = {}
        for kind in ("income", "expense"):
            amount = db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user.id, Transaction.kind == kind,
                Transaction.transaction_date.between(start, end))) or 0
            vals[kind] = round(float(amount), 2)
        result.append({"month": start.strftime("%b %Y"), **vals})
    return result

@router.get("/forecast")
def forecast(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Simple transparent baseline: average of the last three complete/current months.
    trend_rows = trend(3, db, user)
    values = [r["expense"] for r in trend_rows]
    estimate = round(sum(values) / len(values), 2) if values else 0
    return {"method": "three-month moving average", "estimated_next_month_expense": estimate,
            "based_on_months": trend_rows}
