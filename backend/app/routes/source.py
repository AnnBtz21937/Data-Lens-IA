from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os
import shutil

from app.database import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate
from app.routes.auth import get_current_user
from app.services.documents import (
    answer_question,
    read_document,
    SUPPORTED_EXTENSIONS
)

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("/project/{project_id}")
def get_project_sources(
    project_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Source).filter(Source.project_id == project_id).all()


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
    allowed_extensions = SUPPORTED_EXTENSIONS

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Formato de arquivo não permitido."
        )

    upload_directory = "uploads"

    os.makedirs(upload_directory, exist_ok=True)

    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(
        upload_directory,
        safe_filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_source = Source(
        name=safe_filename,
        type=file_extension.replace(".", ""),
        path=file_path,
        project_id=project_id
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return new_source


@router.post("/{source_id}/ask")
def ask_source(
    source_id: int,
    question: dict,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(Source.id == source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail="Fonte de dados não encontrada.")

    question_text = str(question.get("question", "")).strip()
    if not question_text:
        raise HTTPException(status_code=400, detail="Digite uma pergunta.")

    if not source.path or not os.path.exists(source.path):
        raise HTTPException(status_code=404, detail="Arquivo da fonte não encontrado.")

    try:
        return answer_question(source.path, source.name, question_text)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao responder a pergunta: {str(error)}"
        ) from error

@router.post("/{source_id}/analyze")
def analyze_source(
    source_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(
        Source.id == source_id
    ).first()

    if not source:
        raise HTTPException(
            status_code=404,
            detail="Fonte de dados não encontrada."
        )

    if not source.path:
        raise HTTPException(
            status_code=400,
            detail="A fonte não possui um arquivo associado."
        )

    if not os.path.exists(source.path):
        raise HTTPException(
            status_code=404,
            detail="Arquivo da fonte não encontrado."
        )

    try:
        resultado = read_document(source.path)["analysis"]

        return {
            "source_id": source.id,
            "source_name": source.name,
            "analysis": resultado
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao analisar o arquivo: {str(e)}"
        )