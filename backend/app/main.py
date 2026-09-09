from fastapi import FastAPI

from app.database import Base, engine
from app.models.user import User
from app.models.project import Project
from app.models.source import Source
from app.routes.users import router as users_router
from app.routes.projects import router as projects_router
from app.routes.auth import router as auth_router
from app.routes.source import router as sources_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DataLens AI")


app.include_router(users_router)
app.include_router(projects_router)
app.include_router(auth_router)
app.include_router(sources_router)

@app.get("/")
def root():
    return {"message": "DataLens AI API está funcionando!"}