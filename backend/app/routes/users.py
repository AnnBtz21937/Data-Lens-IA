from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate


router = APIRouter(prefix="/users", tags=["Users"])

password_hash = PasswordHash.recommended()

@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="E-mail já cadastrado."
        )

    hashed_password = password_hash.hash(user.password)
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }