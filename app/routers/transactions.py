import csv, io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.database import get_db
from app.deps import get_current_user
from app.models import Transaction, Category, User
from app.schemas import TransactionIn, TransactionOut

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

def validate_category(db, user_id, category_id, kind):
    if category_id is not None:
        category = db.get(Category, category_id)
        if not category or category.user_id != user_id or category.kind != kind:
            raise HTTPException(status_code=400, detail="Select a valid category for this transaction type")

@router.get("", response_model=list[TransactionOut])
def list_transactions(
    start: date | None = None, end: date | None = None, kind: str | None = None,
    category_id: int | None = None, search: str | None = None,
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    stmt = select(Transaction).where(Transaction.user_id == user.id)
    if start: stmt = stmt.where(Transaction.transaction_date >= start)
    if end: stmt = stmt.where(Transaction.transaction_date <= end)
    if kind in ("income", "expense"): stmt = stmt.where(Transaction.kind == kind)
    if category_id: stmt = stmt.where(Transaction.category_id == category_id)
    if search: stmt = stmt.where(Transaction.description.ilike(f"%{search}%"))
    return db.scalars(stmt.order_by(desc(Transaction.transaction_date), desc(Transaction.id)).limit(limit).offset(offset)).all()

@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(payload: TransactionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    validate_category(db, user.id, payload.category_id, payload.kind)
    item = Transaction(user_id=user.id, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item

@router.put("/{transaction_id}", response_model=TransactionOut)
def update_transaction(transaction_id: int, payload: TransactionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id))
    if not item: raise HTTPException(status_code=404, detail="Transaction not found")
    validate_category(db, user.id, payload.category_id, payload.kind)
    for key, value in payload.model_dump().items(): setattr(item, key, value)
    db.commit(); db.refresh(item)
    return item

@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.scalar(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id))
    if not item: raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(item); db.commit()
    return Response(status_code=204)

@router.get("/export.csv")
def export_csv(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.transaction_date)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "type", "description", "amount", "category_id", "recurring"])
    for row in rows:
        writer.writerow([row.transaction_date, row.kind, row.description, row.amount, row.category_id or "", row.recurring])
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=transactions.csv"})

@router.post("/import.csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")
    raw = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    created = 0
    for row in reader:
        try:
            kind = row["type"].strip().lower()
            amount = float(row["amount"])
            tx_date = date.fromisoformat(row["date"])
            if kind not in ("income", "expense") or amount <= 0: raise ValueError()
            category_id = int(row["category_id"]) if row.get("category_id") else None
            validate_category(db, user.id, category_id, kind)
            db.add(Transaction(user_id=user.id, kind=kind, amount=amount, transaction_date=tx_date,
                               description=row["description"][:250], category_id=category_id,
                               recurring=row.get("recurring", "").lower() == "true"))
            created += 1
        except (ValueError, KeyError, TypeError):
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Invalid CSV row near record {created + 2}")
    db.commit()
    return {"imported": created}
