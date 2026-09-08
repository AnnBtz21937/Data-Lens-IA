from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os
import shutil

from app.database import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate
from app.routes.auth import get_current_user

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("/{project_id}")
def create_source(
    project_id: int,
    source: SourceCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_source = Source(
        name=source.name,
        type=source.type,
        path=source.path,
        project_id=project_id
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return new_source

@router.post("/{project_id}/upload")
def upload_source(
    project_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_extensions = [".xlsx", ".xls", ".csv"]

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Formato de arquivo não permitido."
        )

    upload_directory = "uploads"

    os.makedirs(upload_directory, exist_ok=True)

    file_path = os.path.join(
        upload_directory,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_source = Source(
        name=file.filename,
        type=file_extension.replace(".", ""),
        path=file_path,
        project_id=project_id
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return new_source