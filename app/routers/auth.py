from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import User, Category
from app.schemas import RegisterIn, LoginIn, UserOut
from app.security import hash_password, verify_password, create_access_token
from app.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    defaults = [
        ("Salary", "income", "#16a34a"), ("Other income", "income", "#0d9488"),
        ("Food", "expense", "#f97316"), ("Transport", "expense", "#3b82f6"),
        ("Shopping", "expense", "#a855f7"), ("Bills", "expense", "#eab308"),
        ("Health", "expense", "#ef4444"), ("Education", "expense", "#06b6d4"),
        ("Other", "expense", "#64748b")
    ]
    for name, kind, color in defaults:
        db.add(Category(user_id=user.id, name=name, kind=kind, color=color))
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer", "user": UserOut.model_validate(user)}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
