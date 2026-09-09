from sqlalchemy import text
from app.database import engine

try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("Conexão com o MySQL realizada com sucesso!")

except Exception as error:
    print("Erro ao conectar ao MySQL:")
    print(error)