from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
import jwt

from app.database import get_db
from app.models.user import User

SECRET_KEY = "uma-chave-secreta-temporaria"
ALGORITHM = "HS256"

router = APIRouter(prefix="/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Token inválido."
            )

        return user_id

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido."
        )


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos."
        )

    if not password_hash.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos."
        )

    token = jwt.encode(
        {
            "user_id": user.id,
            "email": user.email
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }