def preparar_contexto_ia(resultado_analise):
    """
    Prepara os resultados da análise para serem enviados
    posteriormente para um modelo de IA.

    A IA recebe apenas informações calculadas pelo sistema.
    """

    analise_automatica = resultado_analise.get(
        "analise_automatica",
        {}
    )

    contexto = {
        "total_registros": resultado_analise.get(
            "total_registros",
            0
        ),

        "total_colunas": resultado_analise.get(
            "total_colunas",
            0
        ),

        "relacoes_relevantes": analise_automatica.get(
            "relacoes_estruturadas",
            []
        ),

        "comparacoes": analise_automatica.get(
            "comparacoes",
            []
        ),

        "insights": resultado_analise.get(
            "insights",
            {}
        )
    }

    return contexto

def criar_prompt_analise(contexto):
    """
    Cria as instruções que serão enviadas posteriormente
    para o modelo de IA.
    """

    prompt = f"""
Você é um assistente de análise de dados.

Sua função é interpretar os resultados calculados pelo
sistema e explicar os principais achados em linguagem
natural e clara.

REGRAS:
- Não invente números.
- Não faça cálculos que não estejam nos dados fornecidos.
- Não altere os valores apresentados.
- Não confunda associação com causalidade.
- Quando houver uma associação entre variáveis, diga que
  existe uma associação, e não que uma variável causou a outra.
- Priorize os resultados mais relevantes.
- Explique os resultados de forma que uma pessoa sem
  conhecimento técnico consiga entender.

DADOS DA ANÁLISE:

Total de registros:
{contexto["total_registros"]}

Total de colunas:
{contexto["total_colunas"]}

Relações relevantes:
{contexto["relacoes_relevantes"]}

Comparações:
{contexto["comparacoes"]}

Com base exclusivamente nesses dados, produza uma
interpretação dos principais achados.
"""

    return prompt