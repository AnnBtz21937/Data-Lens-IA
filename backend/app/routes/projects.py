from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.source import Source
from app.schemas.project import ProjectCreate
from app.routes.auth import get_current_user


router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/")
def create_project(
    project: ProjectCreate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_project = Project(
        name=project.name,
        description=project.description,
        user_id=user_id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project

@router.get("/")
def get_projects(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).filter(
        Project.user_id == user_id
    ).all()

    return projects


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    db.query(Source).filter(Source.project_id == project_id).delete(
        synchronize_session=False
    )
    db.delete(project)
    db.commit()
    return {"message": "Projeto excluído."}