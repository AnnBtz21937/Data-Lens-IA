import pandas as pd


# Dicionários específicos do Censo Escolar
DICIONARIOS = {
    "TP_DEPENDENCIA": {
        1: "Federal",
        2: "Estadual",
        3: "Municipal",
        4: "Privada",
    },

    "TP_LOCALIZACAO": {
        1: "Urbana",
        2: "Rural",
    },

    "TP_CATEGORIA_ESCOLA_PRIVADA": {
        1: "Particular",
        2: "Comunitária",
        3: "Confessional",
        4: "Filantrópica",
    },

    "TP_PODER_PUBLICO_PARCERIA": {
        1: "Municipal",
        2: "Estadual",
        3: "Estadual e Municipal",
    },

    "TP_LOCALIZACAO_DIFERENCIADA": {
        0: "Não está em área diferenciada",
        1: "Área de assentamento",
        2: "Terra indígena",
        3: "Comunidade quilombola",
        8: "Área de povos/comunidades tradicionais",
    },

    "IN_PODER_PUBLICO_PARCERIA": {
        0: "Sem parceria",
        1: "Com parceria",
    },
}

DESCRICOES_COLUNAS = {
    "TP_DEPENDENCIA": "dependência administrativa da escola",
    "TP_LOCALIZACAO": "localização da escola",
    "TP_LOCALIZACAO_DIFERENCIADA": "localização diferenciada da escola",
    "TP_CATEGORIA_ESCOLA_PRIVADA": "categoria da escola privada",
    "IN_PODER_PUBLICO_PARCERIA": "existência de parceria com o poder público",
    "TP_PODER_PUBLICO_PARCERIA": "tipo de parceria com o poder público",
}

def ler_csv(file_path: str):
    """
    Lê um arquivo CSV tentando identificar automaticamente
    o separador e o encoding.
    """

    encodings = ["utf-8", "latin1", "cp1252"]

    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                sep=None,
                engine="python",
                encoding=encoding
            )

            return df

        except (UnicodeDecodeError, pd.errors.ParserError):
            continue

    raise ValueError("Não foi possível ler o arquivo CSV.")


def analisar_colunas(df):
    """
    Analisa genericamente todas as colunas do DataFrame.
    """

    colunas = {}

    for coluna in df.columns:

        serie = df[coluna]

        informacoes = {
            "tipo": str(serie.dtype),
            "valores_nulos": int(serie.isna().sum()),
            "valores_preenchidos": int(serie.notna().sum()),
            "valores_unicos": int(serie.nunique(dropna=True)),
        }

        # Estatísticas para colunas numéricas
        if pd.api.types.is_numeric_dtype(serie):

            valores = pd.to_numeric(
                serie,
                errors="coerce"
            ).dropna()

            if not valores.empty:

                informacoes["estatisticas"] = {
                    "minimo": float(valores.min()),
                    "maximo": float(valores.max()),
                    "media": round(float(valores.mean()), 2),
                    "mediana": float(valores.median()),
                }

        colunas[coluna] = informacoes

    return colunas


def analisar_categorias_censo(df):
    """
    Analisa categorias específicas conhecidas do Censo Escolar.
    """

    resultado = {}

    for coluna, dicionario in DICIONARIOS.items():

        if coluna not in df.columns:
            continue

        valores = df[coluna].value_counts(
            dropna=True
        ).to_dict()

        categorias = {}

        for codigo, quantidade in valores.items():

            try:
                codigo_int = int(codigo)
            except (ValueError, TypeError):
                codigo_int = codigo

            nome = dicionario.get(
                codigo_int,
                f"Código desconhecido: {codigo}"
            )

            categorias[nome] = int(quantidade)

        resultado[coluna] = categorias

    return resultado

def analisar_relacoes_censo(df):
    """
    Analisa relações entre variáveis categóricas do Censo Escolar.
    """

    resultado = {}

    # ---------------------------------------------------------
    # DEPENDÊNCIA ADMINISTRATIVA × LOCALIZAÇÃO
    # ---------------------------------------------------------

    if (
        "TP_DEPENDENCIA" in df.columns
        and "TP_LOCALIZACAO" in df.columns
    ):

        tabela = pd.crosstab(
            df["TP_DEPENDENCIA"],
            df["TP_LOCALIZACAO"]
        )

        relacao = {}

        for dependencia, linha in tabela.iterrows():

            dependencia_nome = DICIONARIOS[
                "TP_DEPENDENCIA"
            ].get(
                int(dependencia),
                str(dependencia)
            )

            total = int(linha.sum())

            if total == 0:
                continue

            relacao[dependencia_nome] = {}

            for localizacao, quantidade in linha.items():

                localizacao_nome = DICIONARIOS[
                    "TP_LOCALIZACAO"
                ].get(
                    int(localizacao),
                    str(localizacao)
                )

                quantidade = int(quantidade)

                percentual = (
                    quantidade / total
                ) * 100

                relacao[dependencia_nome][
                    localizacao_nome
                ] = {
                    "quantidade": quantidade,
                    "percentual": round(percentual, 2)
                }

        resultado[
            "dependencia_x_localizacao"
        ] = relacao

    return resultado

def calcular_cramers_v(tabela):
    """
    Calcula o Cramér's V a partir de uma tabela de contingência.

    O resultado varia de 0 a 1:
    0 = nenhuma associação
    1 = associação muito forte
    """

    import numpy as np

    observados = tabela.to_numpy()

    total = observados.sum()

    if total == 0:
        return 0.0

    # Totais das linhas e colunas
    totais_linhas = observados.sum(axis=1)
    totais_colunas = observados.sum(axis=0)

    # Valores esperados
    esperados = np.outer(
        totais_linhas,
        totais_colunas
    ) / total

    # Evita divisão por zero
    mascara = esperados > 0

    qui_quadrado = (
        ((observados - esperados) ** 2) / esperados
    )[mascara].sum()

    # Tamanho da tabela
    n = observados.sum()

    menor_dimensao = min(
        observados.shape[0] - 1,
        observados.shape[1] - 1
    )

    if menor_dimensao <= 0:
        return 0.0

    cramers_v = np.sqrt(
        (qui_quadrado / n) / menor_dimensao
    )

    return round(float(cramers_v), 4)

def classificar_forca_associacao(cramers_v):
    """
    Classifica a força da associação com base no Cramér's V.
    """

    if cramers_v < 0.10:
        return "Muito fraca"

    if cramers_v < 0.30:
        return "Fraca"

    if cramers_v < 0.50:
        return "Moderada"

    if cramers_v < 0.70:
        return "Forte"

    return "Muito forte"

def descobrir_relacoes_categoricas(df):
    """
    Descobre automaticamente relações entre variáveis categóricas.

    Considera apenas colunas com quantidade controlada de categorias
    para evitar cruzamentos desnecessários ou muito grandes.
    """

    resultado = []

    colunas = []

    # ---------------------------------------------------------
    # IDENTIFICA COLUNAS CATEGÓRICAS RELEVANTES
    # ---------------------------------------------------------

    for coluna in df.columns:

        serie = df[coluna].dropna()

        if serie.empty:
            continue

        quantidade_categorias = serie.nunique()

        # Evita IDs, códigos únicos e colunas com muitas categorias
        if not (2 <= quantidade_categorias <= 10):
            continue

        # Prioriza variáveis categóricas
        eh_categorica = (
            coluna.startswith("TP_")
            or coluna.startswith("IN_")
            or coluna.startswith("SG_")
        )

        if eh_categorica:
            colunas.append(coluna)

    # ---------------------------------------------------------
    # CRUZA AS COLUNAS
    # ---------------------------------------------------------

    for i in range(len(colunas)):

        coluna_a = colunas[i]

        for j in range(i + 1, len(colunas)):

            coluna_b = colunas[j]

            dados = df[
                [coluna_a, coluna_b]
                ].dropna()

            if dados.empty:
                continue

            # Ignora relações em que uma das variáveis
            # # tenha apenas uma categoria após o cruzamento.
            if dados[coluna_a].nunique() < 2:
                continue
            if dados[coluna_b].nunique() < 2:
                continue

            tabela = pd.crosstab(
                dados[coluna_a],
                dados[coluna_b]
            )

            if tabela.empty:
                continue

            forca_associacao = calcular_cramers_v(tabela)

            relacao = {
                "coluna_a": coluna_a,
                "coluna_b": coluna_b,
                "total_registros": int(len(dados)),
                "categorias_a": int(dados[coluna_a].nunique()),
                "categorias_b": int(dados[coluna_b].nunique()),
                "cramers_v": forca_associacao,
                "distribuicao": {}
            }
            relacao = {
                "coluna_a": coluna_a,
                "coluna_b": coluna_b,
                "total_registros": int(len(dados)),
                "categorias_a": int(dados[coluna_a].nunique()),
                "categorias_b": int(dados[coluna_b].nunique()),
                "cramers_v": forca_associacao,
                "forca_associacao": classificar_forca_associacao(
                    forca_associacao
                ),
                "distribuicao": {}
            }

            # -------------------------------------------------
            # CALCULA PERCENTUAIS POR CATEGORIA DA COLUNA A
            # -------------------------------------------------

            for categoria_a, linha in tabela.iterrows():

                total_categoria = int(linha.sum())

                if total_categoria == 0:
                    continue

                distribuicao = {}

                for categoria_b, quantidade in linha.items():

                    quantidade = int(quantidade)

                    percentual = (
                        quantidade / total_categoria
                    ) * 100

                    distribuicao[str(categoria_b)] = {
                        "quantidade": quantidade,
                        "percentual": round(percentual, 2)
                    }

                relacao["distribuicao"][
                    str(categoria_a)
                ] = distribuicao

            resultado.append(relacao)

    # Ordena da relação mais forte para a mais fraca
    resultado.sort(
        key=lambda x: x["cramers_v"],
        reverse=True
    )

    return resultado

def selecionar_relacoes_relevantes(
    relacoes,
    limite_cramers=0.30,
    limite_resultados=5
):
    """
    Seleciona as relações categóricas mais relevantes.

    Mantém apenas relações com Cramér's V acima
    do limite definido e limita a quantidade de resultados.
    """

    relacoes_relevantes = [
        relacao
        for relacao in relacoes
        if relacao["cramers_v"] >= limite_cramers
    ]

    return relacoes_relevantes[:limite_resultados]

def nomear_categoria(coluna, valor):
    """
    Converte um código de categoria em seu nome,
    quando existe um dicionário conhecido.
    """

    if coluna not in DICIONARIOS:
        return str(valor)

    try:
        codigo = int(float(valor))
    except (ValueError, TypeError):
        return str(valor)

    return DICIONARIOS[coluna].get(
        codigo,
        str(valor)
    )

def gerar_insights_relacoes_automaticas(relacoes):
    """
    Gera insights em linguagem natural a partir
    das relações consideradas relevantes.

    Além da força da associação, utiliza os percentuais
    encontrados nas tabelas de contingência.
    """

    insights = []

    plurais_dependencia = {
        "Federal": "federais",
        "Estadual": "estaduais",
        "Municipal": "municipais",
        "Privada": "privadas",
    }

    nomes_localizacao = {
        "Urbana": "áreas urbanas",
        "Rural": "áreas rurais",
    }

    nomes_booleanos = {
        "0": "não possuem",
        "1": "possuem",
    }

    for relacao in relacoes:

        coluna_a = relacao["coluna_a"]
        coluna_b = relacao["coluna_b"]

        cramers_v = relacao["cramers_v"]
        forca = relacao["forca_associacao"]

        distribuicao = relacao["distribuicao"]

        # =====================================================
        # 1. DEPENDÊNCIA × LOCALIZAÇÃO
        # =====================================================

        if (
            coluna_a == "TP_DEPENDENCIA"
            and coluna_b == "TP_LOCALIZACAO"
        ):

            for categoria_a, categorias_b in distribuicao.items():

                nome_a = nomear_categoria(
                    coluna_a,
                    categoria_a
                )

                nome_a_plural = plurais_dependencia.get(
                    nome_a,
                    nome_a.lower()
                )

                valores = sorted(
                    categorias_b.items(),
                    key=lambda x: x[1]["percentual"],
                    reverse=True
                )

                if len(valores) < 2:
                    continue

                principal = valores[0]
                secundario = valores[1]

                nome_principal = nomear_categoria(
                    coluna_b,
                    principal[0]
                )

                nome_secundario = nomear_categoria(
                    coluna_b,
                    secundario[0]
                )

                nome_principal = nomes_localizacao.get(
                    nome_principal,
                    nome_principal.lower()
                )

                nome_secundario = nomes_localizacao.get(
                    nome_secundario,
                    nome_secundario.lower()
                )

                percentual_principal = principal[1]["percentual"]
                percentual_secundario = secundario[1]["percentual"]

                insights.append(
                    f"Entre as escolas {nome_a_plural}, "
                    f"{percentual_principal:.2f}% estão localizadas em "
                    f"{nome_principal} e "
                    f"{percentual_secundario:.2f}% em "
                    f"{nome_secundario}."
                )

        # =====================================================
        # 2. DEPENDÊNCIA × PARCERIA COM O PODER PÚBLICO
        # =====================================================

        elif (
            coluna_a == "TP_DEPENDENCIA"
            and coluna_b == "IN_PODER_PUBLICO_PARCERIA"
        ):

            for categoria_a, categorias_b in distribuicao.items():

                nome_a = nomear_categoria(
                    coluna_a,
                    categoria_a
                )

                nome_a_plural = plurais_dependencia.get(
                    nome_a,
                    nome_a.lower()
                )

                valores = sorted(
                    categorias_b.items(),
                    key=lambda x: x[1]["percentual"],
                    reverse=True
                )

                if not valores:
                    continue

                partes = []

                for categoria_b, dados in valores:

                    nome_b = nomes_booleanos.get(
                        str(categoria_b),
                        str(categoria_b)
                    )

                    percentual = dados["percentual"]

                    partes.append(
                        f"{percentual:.2f}% {nome_b} parceria"
                    )

                insights.append(
                    f"Entre as escolas {nome_a_plural}, "
                    f"{', '.join(partes)}."
                )

            insights.append(
                f"Foi identificada uma associação {forca.lower()} "
                f"entre a dependência administrativa da escola e "
                f"a existência de parceria com o poder público, "
                f"com Cramér's V de {cramers_v:.4f}."
            )

        # =====================================================
        # 3. LOCALIZAÇÃO × LOCALIZAÇÃO DIFERENCIADA
        # =====================================================

        elif (
            coluna_a == "TP_LOCALIZACAO"
            and coluna_b == "TP_LOCALIZACAO_DIFERENCIADA"
        ):

            for categoria_a, categorias_b in distribuicao.items():

                nome_a = nomear_categoria(
                    coluna_a,
                    categoria_a
                )

                nome_a = nomes_localizacao.get(
                    nome_a,
                    nome_a.lower()
                )

                valores = sorted(
                    categorias_b.items(),
                    key=lambda x: x[1]["percentual"],
                    reverse=True
                )

                if not valores:
                    continue

                principal = valores[0]

                nome_b = nomear_categoria(
                    coluna_b,
                    principal[0]
                )

                percentual = principal[1]["percentual"]

                insights.append(
                    f"Entre as escolas localizadas em "
                    f"{nome_a}, a categoria de localização "
                    f"diferenciada mais frequente é "
                    f"'{nome_b}', representando "
                    f"{percentual:.2f}% dos registros analisados."
                )

            insights.append(
                f"Foi identificada uma associação {forca.lower()} "
                f"entre a localização da escola e a localização "
                f"diferenciada, com Cramér's V de "
                f"{cramers_v:.4f}."
            )

        # =====================================================
        # 4. CATEGORIA DA ESCOLA PRIVADA × PARCERIA
        # =====================================================

        elif (
            coluna_a == "TP_CATEGORIA_ESCOLA_PRIVADA"
            and coluna_b == "IN_PODER_PUBLICO_PARCERIA"
        ):

            for categoria_a, categorias_b in distribuicao.items():

                nome_a = nomear_categoria(
                    coluna_a,
                    categoria_a
                )

                valores = sorted(
                    categorias_b.items(),
                    key=lambda x: x[1]["percentual"],
                    reverse=True
                )

                if not valores:
                    continue

                partes = []

                for categoria_b, dados in valores:

                    if str(categoria_b) == "1":
                        nome_b = "possuem parceria"
                    elif str(categoria_b) == "0":
                        nome_b = "não possuem parceria"
                    else:
                        nome_b = str(categoria_b)

                    partes.append(
                        f"{dados['percentual']:.2f}% "
                        f"{nome_b}"
                    )

                insights.append(
                    f"Entre as escolas privadas da categoria "
                    f"{nome_a}, {', '.join(partes)}."
                )

            insights.append(
                f"Foi identificada uma associação {forca.lower()} "
                f"entre a categoria da escola privada e a existência "
                f"de parceria com o poder público, com Cramér's V "
                f"de {cramers_v:.4f}. "
                f"Essa relação deve ser interpretada com cautela, "
                f"pois a categoria de escola privada é um campo "
                f"específico desse tipo de estabelecimento."
            )

        # =====================================================
        # 5. OUTRAS RELAÇÕES
        # =====================================================

        else:

            descricao_a = DESCRICOES_COLUNAS.get(
                coluna_a,
                coluna_a
            )

            descricao_b = DESCRICOES_COLUNAS.get(
                coluna_b,
                coluna_b
            )

            insights.append(
                f"Foi identificada uma associação {forca.lower()} "
                f"entre {descricao_a} e {descricao_b}, "
                f"com Cramér's V de {cramers_v:.4f}."
            )

    return insights

def estruturar_relacoes(relacoes):
    """
    Organiza as relações relevantes em uma estrutura
    semântica para consumo pelo frontend e pela futura IA.

    Os códigos das categorias são convertidos para seus
    respectivos nomes quando existe um dicionário conhecido.
    """

    resultado = []

    for relacao in relacoes:

        coluna_a = relacao["coluna_a"]
        coluna_b = relacao["coluna_b"]

        descricao_a = DESCRICOES_COLUNAS.get(
            coluna_a,
            coluna_a
        )

        descricao_b = DESCRICOES_COLUNAS.get(
            coluna_b,
            coluna_b
        )

        distribuicao_original = relacao[
            "distribuicao"
        ]

        distribuicao_semantica = {}

        for categoria_a, categorias_b in (
            distribuicao_original.items()
        ):

            nome_categoria_a = nomear_categoria(
                coluna_a,
                categoria_a
            )

            distribuicao_semantica[
                nome_categoria_a
            ] = {}

            for categoria_b, dados in categorias_b.items():

                nome_categoria_b = nomear_categoria(
                    coluna_b,
                    categoria_b
                )

                distribuicao_semantica[
                    nome_categoria_a
                ][nome_categoria_b] = {
                    "quantidade": dados["quantidade"],
                    "percentual": dados["percentual"]
                }

        resultado.append({
            "variavel_a": {
                "codigo": coluna_a,
                "descricao": descricao_a
            },

            "variavel_b": {
                "codigo": coluna_b,
                "descricao": descricao_b
            },

            "forca_associacao": relacao[
                "forca_associacao"
            ],

            "cramers_v": relacao[
                "cramers_v"
            ],

            "total_registros": relacao[
                "total_registros"
            ],

            "distribuicao": distribuicao_semantica
        })

    return resultado

def gerar_insights_comparativos(relacoes):
    """
    Identifica padrões comparativos nas relações estruturadas.

    Procura:
    - maior percentual;
    - menor percentual;
    - diferença entre categorias.

    Os cálculos são feitos pelo Python.
    A futura IA ficará responsável apenas pela interpretação.
    """

    insights = []

    plurais_dependencia = {
        "Federal": "federais",
        "Estadual": "estaduais",
        "Municipal": "municipais",
        "Privada": "privadas",
    }

    nomes_localizacao_plural = {
        "Urbana": "áreas urbanas",
        "Rural": "áreas rurais",
    }

    for relacao in relacoes:

        coluna_a = relacao["variavel_a"]["codigo"]
        coluna_b = relacao["variavel_b"]["codigo"]

        descricao_a = relacao["variavel_a"]["descricao"]
        descricao_b = relacao["variavel_b"]["descricao"]

        distribuicao = relacao["distribuicao"]

        # =====================================================
        # DEPENDÊNCIA × LOCALIZAÇÃO
        # =====================================================

        if (
            coluna_a == "TP_DEPENDENCIA"
            and coluna_b == "TP_LOCALIZACAO"
        ):

            comparacoes = []

            for categoria, localizacoes in distribuicao.items():

                rural = localizacoes.get("Rural")

                if rural:
                    comparacoes.append({
                        "categoria": categoria,
                        "percentual": rural["percentual"]
                    })

            if len(comparacoes) >= 2:

                maior = max(
                    comparacoes,
                    key=lambda x: x["percentual"]
                )

                menor = min(
                    comparacoes,
                    key=lambda x: x["percentual"]
                )

                diferenca = (
                    maior["percentual"]
                    - menor["percentual"]
                )

                nome_maior = plurais_dependencia.get(
                    maior["categoria"],
                    maior["categoria"].lower()
                )

                nome_menor = plurais_dependencia.get(
                    menor["categoria"],
                    menor["categoria"].lower()
                )

                insights.append(
                    f"Entre as categorias de dependência "
                    f"administrativa, as escolas {nome_maior} "
                    f"apresentam a maior proporção de localização rural, "
                    f"com {maior['percentual']:.2f}%. "
                    f"As escolas {nome_menor} apresentam "
                    f"a menor proporção, com {menor['percentual']:.2f}%, "
                    f"uma diferença de {diferenca:.2f} pontos percentuais."
                )

        # =====================================================
        # DEPENDÊNCIA × PARCERIA
        # =====================================================

        elif (
            coluna_a == "TP_DEPENDENCIA"
            and coluna_b == "IN_PODER_PUBLICO_PARCERIA"
        ):

            comparacoes = []

            for categoria, valores in distribuicao.items():

                parceria = valores.get("1")

                if parceria:
                    comparacoes.append({
                        "categoria": categoria,
                        "percentual": parceria["percentual"]
                    })

            if len(comparacoes) >= 2:

                maior = max(
                    comparacoes,
                    key=lambda x: x["percentual"]
                )

                menor = min(
                    comparacoes,
                    key=lambda x: x["percentual"]
                )

                diferenca = (
                    maior["percentual"]
                    - menor["percentual"]
                )

                nome_maior = plurais_dependencia.get(
                    maior["categoria"],
                    maior["categoria"].lower()
                )

                nome_menor = plurais_dependencia.get(
                    menor["categoria"],
                    menor["categoria"].lower()
                )

                insights.append(
                    f"Entre as categorias de dependência "
                    f"administrativa, as escolas {nome_maior} "
                    f"apresentam a maior proporção de parceria com o "
                    f"poder público, com {maior['percentual']:.2f}%. "
                    f"As escolas {nome_menor} apresentam a menor proporção, "
                    f"com {menor['percentual']:.2f}%, "
                    f"uma diferença de {diferenca:.2f} pontos percentuais."
                )

        # =====================================================
        # CATEGORIA PRIVADA × PARCERIA
        # =====================================================

        elif (
            coluna_a == "TP_CATEGORIA_ESCOLA_PRIVADA"
            and coluna_b == "IN_PODER_PUBLICO_PARCERIA"
        ):

            comparacoes = []

            for categoria, valores in distribuicao.items():

                parceria = valores.get("1")

                if parceria:
                    comparacoes.append({
                        "categoria": categoria,
                        "percentual": parceria["percentual"]
                    })

            if len(comparacoes) >= 2:

                maior = max(
                    comparacoes,
                    key=lambda x: x["percentual"]
                )

                menor = min(
                    comparacoes,
                    key=lambda x: x["percentual"]
                )

                diferenca = (
                    maior["percentual"]
                    - menor["percentual"]
                )

                insights.append(
                    f"Entre as categorias de escolas privadas, "
                    f"{maior['categoria']} apresenta a maior proporção "
                    f"de parceria com o poder público, com "
                    f"{maior['percentual']:.2f}%. "
                    f"{menor['categoria']} apresenta a menor proporção, "
                    f"com {menor['percentual']:.2f}%, "
                    f"uma diferença de {diferenca:.2f} pontos percentuais."
                )

        # =====================================================
        # LOCALIZAÇÃO × LOCALIZAÇÃO DIFERENCIADA
        # =====================================================

        elif (
            coluna_a == "TP_LOCALIZACAO"
            and coluna_b == "TP_LOCALIZACAO_DIFERENCIADA"
        ):

            comparacoes = []

            for localizacao, categorias in distribuicao.items():

                sem_area_diferenciada = categorias.get(
                    "Não está em área diferenciada"
                )

                if sem_area_diferenciada:

                    comparacoes.append({
                        "categoria": localizacao,
                        "percentual": sem_area_diferenciada[
                            "percentual"
                        ]
                    })

            if len(comparacoes) >= 2:

                maior = max(
                    comparacoes,
                    key=lambda x: x["percentual"]
                )

                menor = min(
                    comparacoes,
                    key=lambda x: x["percentual"]
                )

                diferenca = (
                    maior["percentual"]
                    - menor["percentual"]
                )

                nome_maior = nomes_localizacao_plural.get(
                    maior["categoria"],
                    maior["categoria"].lower()
                )

                nome_menor = nomes_localizacao_plural.get(
                    menor["categoria"],
                    menor["categoria"].lower()
                )

                insights.append(
                    f"A proporção de escolas que não estão em "
                    f"área de localização diferenciada é maior nas "
                    f"{nome_maior}, com "
                    f"{maior['percentual']:.2f}%, enquanto nas "
                    f"{nome_menor} é de "
                    f"{menor['percentual']:.2f}%. "
                    f"A diferença é de {diferenca:.2f} pontos percentuais."
                )

    return insights

def gerar_comparacoes_genericas(
    relacoes,
    limite_cramers=0.30
):
    """
    Identifica automaticamente maiores, menores e diferenças
    percentuais nas relações categóricas.

    Os cálculos são realizados pelo Python.
    Os códigos das categorias são convertidos para nomes
    quando existe um dicionário conhecido.
    """

    comparacoes = []

    for relacao in relacoes:
        if relacao["cramers_v"] < limite_cramers:
            continue

        coluna_a = relacao["variavel_a"]["codigo"]
        coluna_b = relacao["variavel_b"]["codigo"]

        distribuicao = relacao["distribuicao"]

        for categoria_a, categorias_b in distribuicao.items():

            if not categorias_b:
                continue

            valores_validos = []

            for categoria_b, dados in categorias_b.items():

                percentual = dados.get("percentual")

                if percentual is None:
                    continue

                valores_validos.append({
                    "categoria": nomear_categoria(
                        coluna_b,
                        categoria_b
                    ),
                    "percentual": float(percentual)
                })

            if len(valores_validos) < 2:
                continue

            maior = max(
                valores_validos,
                key=lambda x: x["percentual"]
            )

            menor = min(
                valores_validos,
                key=lambda x: x["percentual"]
            )

            diferenca = (
                maior["percentual"]
                - menor["percentual"]
            )

            comparacoes.append({
                "variavel_a": {
                    "codigo": coluna_a,
                    "descricao": relacao[
                        "variavel_a"
                    ]["descricao"]
                },

                "variavel_b": {
                    "codigo": coluna_b,
                    "descricao": relacao[
                        "variavel_b"
                    ]["descricao"]
                },

                "categoria_analisada": nomear_categoria(
                    coluna_a,
                    categoria_a
                ),

                "maior": maior,

                "menor": menor,

                "diferenca_pontos_percentuais": round(
                    diferenca,
                    2
                )
            })

    return comparacoes

def filtrar_comparacoes_relevantes(
    comparacoes,
    percentual_minimo=1.0,
    diferenca_minima=5.0
):
    """
    Filtra comparações que possuem potencial para gerar
    insights relevantes.

    Uma comparação é considerada relevante quando:
    - o maior percentual está acima do percentual mínimo; e
    - a diferença entre maior e menor é significativa.

    Os dados originais não são alterados.
    """

    comparacoes_relevantes = []

    for comparacao in comparacoes:

        maior = comparacao["maior"]
        menor = comparacao["menor"]

        diferenca = comparacao[
            "diferenca_pontos_percentuais"
        ]

        if (
            maior["percentual"] >= percentual_minimo
            and diferenca >= diferenca_minima
        ):
            comparacoes_relevantes.append(
                comparacao
            )

    return comparacoes_relevantes

def gerar_insights_relacoes(relacoes):
    """
    Gera insights em linguagem natural a partir
    das relações calculadas pelo sistema.
    """

    insights = []

    dependencia_localizacao = relacoes.get(
        "dependencia_x_localizacao",
        {}
    )

    for dependencia, localizacoes in dependencia_localizacao.items():

        if not localizacoes:
            continue

        # Encontra a localização predominante
        localizacao_principal = max(
            localizacoes,
            key=lambda x: localizacoes[x]["percentual"]
        )

        percentual_principal = localizacoes[
            localizacao_principal
        ]["percentual"]

        # Pega a segunda localização
        outras = [
            nome for nome in localizacoes
            if nome != localizacao_principal
        ]

        if outras:

            localizacao_secundaria = outras[0]

            percentual_secundaria = localizacoes[
                localizacao_secundaria
            ]["percentual"]

            plural_dependencia = {
                "Federal": "federais",
                "Estadual": "estaduais",
                "Municipal": "municipais",
                "Privada": "privadas"
            }
            plural_localizacao = {
                "Urbana": "áreas urbanas",
                "Rural": "áreas rurais"
            }
            insights.append(
                f"Entre as escolas {plural_dependencia.get(dependencia, dependencia.lower())}, "
                f"{percentual_principal:.2f}% estão localizadas em "
                f"{plural_localizacao.get(localizacao_principal, localizacao_principal.lower())} "
                f"e {percentual_secundaria:.2f}% em "
                f"{plural_localizacao.get(localizacao_secundaria, localizacao_secundaria.lower())}."
            )

    return insights

def gerar_insights_qualidade(df):
    """
    Analisa valores nulos e diferencia campos
    realmente ausentes de campos não aplicáveis.
    """

    insights = []

    total = len(df)

    if total == 0:
        return insights

    # ---------------------------------------------------------
    # CAMPOS DO CENSO ONDE O NULO PODE SER "NÃO APLICÁVEL"
    # ---------------------------------------------------------

    campos_nao_aplicaveis = {
        "TP_CATEGORIA_ESCOLA_PRIVADA": (
            "não se aplica às escolas públicas"
        ),

        "TP_PODER_PUBLICO_PARCERIA": (
            "não se aplica quando não há parceria com o poder público"
        ),

        "NO_SUBDISTRITO": (
            "não se aplica aos registros sem subdistrito informado"
        ),

        "CO_SUBDISTRITO": (
            "não se aplica aos registros sem subdistrito informado"
        ),
    }

    # ---------------------------------------------------------
    # ANALISA VALORES NULOS
    # ---------------------------------------------------------

    for coluna in df.columns:

        nulos = int(df[coluna].isna().sum())

        if nulos == 0:
            continue

        percentual = (nulos / total) * 100

        # Ignora quantidades muito pequenas
        if percentual < 1:
            continue

        # -----------------------------------------------------
        # CAMPO COM NULO SEMANTICAMENTE ESPERADO
        # -----------------------------------------------------

        if coluna in campos_nao_aplicaveis:

            motivo = campos_nao_aplicaveis[coluna]

            insights.append(
                f"{coluna} possui {nulos:,} valores não aplicáveis, "
                f"representando {percentual:.2f}% dos registros. "
                f"Isso ocorre porque {motivo}."
                .replace(",", ".")
            )

        # -----------------------------------------------------
        # POSSÍVEL AUSÊNCIA DE DADO
        # -----------------------------------------------------

        else:

            insights.append(
                f"{coluna} possui {nulos:,} valores nulos, "
                f"representando {percentual:.2f}% dos registros."
                .replace(",", ".")
            )

    return insights

def analisar_gestores_censo(df):
    """
    Calcula estatísticas específicas da quantidade
    de gestores da educação básica.
    """

    if "QT_GEST_BAS" not in df.columns:
        return {}

    gestores = pd.to_numeric(
        df["QT_GEST_BAS"],
        errors="coerce"
    ).dropna()

    if gestores.empty:
        return {}

    return {
        "total_gestores": int(gestores.sum()),
        "media_por_escola": round(float(gestores.mean()), 2),
        "maior_quantidade": int(gestores.max()),
        "menor_quantidade": int(gestores.min()),
        "escolas_com_gestor": int((gestores > 0).sum()),
    }

def gerar_insights(df):
    """
    Gera os principais insights do conjunto de dados.
    Evita gerar um insight para cada coluna numérica.
    """

    insights = []

    total = len(df)

    if total == 0:
        return ["O conjunto de dados está vazio."]

    # ---------------------------------------------------------
    # 1. TAMANHO DO DATASET
    # ---------------------------------------------------------

    insights.append(
        f"O conjunto de dados possui {total:,} registros "
        f"e {len(df.columns)} colunas.".replace(",", ".")
    )

    # ---------------------------------------------------------
    # 2. PRINCIPAIS COLUNAS CATEGÓRICAS
    # ---------------------------------------------------------

    colunas_categoricas = []

    for coluna in df.columns:

        serie = df[coluna].dropna()

        if serie.empty:
            continue

        quantidade_categorias = serie.nunique()

        eh_categórica = (
            coluna.startswith("TP_")
            or coluna.startswith("IN_")
            or coluna.startswith("NO_")
            or coluna.startswith("SG_")
            or coluna in DICIONARIOS
        )

        if eh_categórica and 2 <= quantidade_categorias <= 10:
            colunas_categoricas.append(coluna)

    # Limita os insights categóricos para evitar excesso
    for coluna in colunas_categoricas:

        serie = df[coluna].dropna()

        contagem = serie.value_counts()

        if contagem.empty:
            continue

        categoria_principal = contagem.index[0]
        quantidade_principal = int(contagem.iloc[0])

        percentual = (
            quantidade_principal / len(serie)
        ) * 100

        # Traduz códigos conhecidos
        if coluna in DICIONARIOS:

            try:
                codigo = int(categoria_principal)
                nome_categoria = DICIONARIOS[coluna].get(
                    codigo,
                    str(categoria_principal)
                )

            except (ValueError, TypeError):

                nome_categoria = str(categoria_principal)

        elif coluna == "IN_PODER_PUBLICO_PARCERIA":

            if categoria_principal == 0:
                nome_categoria = "Sem parceria com o poder público"
            elif categoria_principal == 1:
                nome_categoria = "Com parceria com o poder público"
            else:
                nome_categoria = str(categoria_principal)

        else:
            nome_categoria = str(categoria_principal)

        insights.append(
            f"{coluna}: a categoria mais frequente é "
            f"{nome_categoria}, representando "
            f"{percentual:.2f}% dos valores preenchidos."
        )

    # ---------------------------------------------------------
    # 3. PRINCIPAL COLUNA DE QUANTIDADE
    # ---------------------------------------------------------

    if "QT_GEST_BAS" in df.columns:

        gestores = pd.to_numeric(
            df["QT_GEST_BAS"],
            errors="coerce"
        ).dropna()

        if not gestores.empty:

            insights.append(
                f"A quantidade média de gestores por escola é "
                f"{gestores.mean():.2f}, com mínimo de "
                f"{gestores.min():.0f} e máximo de "
                f"{gestores.max():.0f}."
            )

    return insights

def analisar_csv(file_path: str):
    """
    Analisa genericamente qualquer arquivo CSV.

    Caso o arquivo possua colunas conhecidas do Censo Escolar,
    também executa análises específicas desse conjunto de dados.
    """

    df = ler_csv(file_path)

    # ---------------------------------------------------------
    # # DESCOBERTA AUTOMÁTICA DE RELAÇÕES
    # # ---------------------------------------------------------
    
    relacoes_automaticas = descobrir_relacoes_categoricas(df)

    relacoes_relevantes = selecionar_relacoes_relevantes(
        relacoes_automaticas
    )

    insights_relacoes_automaticas = (
        gerar_insights_relacoes_automaticas(
            relacoes_relevantes
        )
    )

    # ---------------------------------------------------------
    # # ESTRUTURAÇÃO SEMÂNTICA
    # ---------------------------------------------------------
    
    relacoes_estruturadas = estruturar_relacoes(
        relacoes_relevantes
    )

    insights_comparativos = gerar_insights_comparativos(
        relacoes_estruturadas
    )

    comparacoes_genericas = gerar_comparacoes_genericas(
        relacoes_estruturadas
    )

    # ---------------------------------------------------------
    # RESULTADO PRINCIPAL
    # ---------------------------------------------------------

    resultado = {
        "total_registros": int(len(df)),
        "total_colunas": int(len(df.columns)),
        "colunas": list(df.columns),

        "analise_colunas": analisar_colunas(df),

        "insights": {
            "gerais": gerar_insights(df),
            "relacoes": insights_relacoes_automaticas,
            "comparativos": insights_comparativos,
            "qualidade_dados": gerar_insights_qualidade(df)
        },

        "analise_especifica": {}
    }

    # ---------------------------------------------------------
    # ANÁLISE ESPECÍFICA DO CENSO
    # ---------------------------------------------------------

    colunas_censo = set(DICIONARIOS.keys())

    colunas_encontradas = colunas_censo.intersection(
        set(df.columns)
    )

    if colunas_encontradas:

        relacoes_censo = analisar_relacoes_censo(df)

        resultado["analise_especifica"] = {
            "tipo": "Censo Escolar",
            "categorias": analisar_categorias_censo(df),
            "gestores": analisar_gestores_censo(df),
            "relacoes": relacoes_censo
        }

    # ---------------------------------------------------------
    # RELAÇÕES AUTOMÁTICAS
    # ---------------------------------------------------------

    resultado["analise_automatica"] = {
        "relacoes_encontradas": relacoes_automaticas,
        "relacoes_relevantes": relacoes_relevantes,
        "relacoes_estruturadas": relacoes_estruturadas,
        "comparacoes": comparacoes_genericas
    }

    return resultado