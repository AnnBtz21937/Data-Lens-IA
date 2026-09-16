import pandas as pd

from app.database import engine


def listar_tabelas_mysql():
    query = """
        SELECT TABLE_NAME
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        ORDER BY TABLE_NAME
    """

    df = pd.read_sql(query, engine)

    return df["TABLE_NAME"].tolist()


def ler_tabela_mysql(nome_tabela: str):
    tabelas = listar_tabelas_mysql()

    if nome_tabela not in tabelas:
        raise ValueError("Tabela não encontrada no banco de dados.")

    query = f"SELECT * FROM `{nome_tabela}`"

    return pd.read_sql(query, engine)

def resumo_tabela_mysql(nome_tabela: str):
    df = ler_tabela_mysql(nome_tabela)

    return {
        "tabela": nome_tabela,
        "total_registros": int(len(df)),
        "total_colunas": int(len(df.columns)),
        "colunas": list(df.columns),
        "dados": df.to_dict(orient="records")
    }

def contexto_mysql_para_ia(nome_tabela: str) -> dict:
    df = ler_tabela_mysql(nome_tabela)

    contexto = {
        "tabela": nome_tabela,
        "total_registros": int(len(df)),
        "total_colunas": int(len(df.columns)),
        "colunas": list(df.columns)
    }

    if "quantidade_alunos" in df.columns:
        contexto["total_alunos"] = int(
            df["quantidade_alunos"].sum()
        )

    return contexto