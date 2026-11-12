from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.deps import get_current_user
from app.models import Transaction, User

router = APIRouter(prefix="/api/recurring", tags=["Recurring transactions"])

@router.post("/generate")
def generate_monthly(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Idempotent per transaction template and target month.
    target = date.today().replace(day=1)
    templates = db.scalars(select(Transaction).where(Transaction.user_id == user.id, Transaction.recurring == True)).all()
    created = 0
    for template in templates:
        key = f"{template.id}:{target.strftime('%Y-%m')}"
        exists = db.scalar(select(Transaction).where(Transaction.user_id == user.id, Transaction.recurring_key == key))
        if exists: continue
        db.add(Transaction(user_id=user.id, category_id=template.category_id, kind=template.kind,
            amount=template.amount, description=template.description + " (recurring)",
            transaction_date=target, recurring=False, recurring_key=key))
        created += 1
    db.commit()
    return {"created": created, "month": target.strftime("%Y-%m")}
