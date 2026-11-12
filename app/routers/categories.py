from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.deps import get_current_user
from app.models import Category, User
from app.schemas import CategoryIn, CategoryOut

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Category).where(Category.user_id == user.id).order_by(Category.kind, Category.name)).all()

@router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = Category(user_id=user.id, **payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    db.refresh(item)
    return item
