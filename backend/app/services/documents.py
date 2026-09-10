import re
import unicodedata
import json
from pathlib import Path

from app.services.analysis import analisar_colunas, analisar_csv


TABLE_EXTENSIONS = {".csv", ".xls", ".xlsx"}
TEXT_EXTENSIONS = {".pdf", ".docx", ".txt"}
SUPPORTED_EXTENSIONS = TABLE_EXTENSIONS | TEXT_EXTENSIONS


def _read_text_file(file_path: str) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
        try:
            return Path(file_path).read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("Não foi possível ler o texto deste arquivo.")


def _read_pdf(file_path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise ValueError("O suporte a PDF não está instalado no backend.") from error

    reader = PdfReader(file_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _read_docx(file_path: str) -> str:
    try:
        from docx import Document
    except ImportError as error:
        raise ValueError("O suporte a DOCX não está instalado no backend.") from error

    document = Document(file_path)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    tables = [
        " | ".join(cell.text for cell in row.cells)
        for table in document.tables
        for row in table.rows
    ]
    return "\n".join(paragraphs + tables).strip()


def read_document(file_path: str) -> dict:
    if file_path.startswith("database:"):
        import pandas as pd

        config = json.loads(file_path.removeprefix("database:"))
        rows = config.get("rows", [])
        frame = pd.DataFrame(rows)
        return {
            "kind": "table",
            "analysis": {
                "total_registros": int(len(frame)),
                "total_colunas": int(len(frame.columns)),
                "colunas": [str(column) for column in frame.columns],
                "analise_colunas": analisar_colunas(frame),
                "insights": {}
            },
            "text": ""
        }

    extension = Path(file_path).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Formato não suportado. Use PDF, DOCX, TXT, CSV, XLS ou XLSX."
        )

    if extension in TABLE_EXTENSIONS:
        return {
            "kind": "table",
            "analysis": analisar_csv(file_path),
            "text": ""
        }

    if extension == ".pdf":
        text = _read_pdf(file_path)
    elif extension == ".docx":
        text = _read_docx(file_path)
    else:
        text = _read_text_file(file_path)

    if not text.strip():
        raise ValueError("Não foi possível encontrar texto no arquivo.")

    return {
        "kind": "text",
        "analysis": {
            "total_caracteres": len(text),
            "total_palavras": len(re.findall(r"\S+", text)),
            "total_paragrafos": len([line for line in text.splitlines() if line.strip()])
        },
        "text": text
    }


def _table_answer(question: str, analysis: dict) -> str:
    lower_question = _normalize(question)
    total_records = analysis.get("total_registros", 0)
    total_columns = analysis.get("total_colunas", 0)
    columns = analysis.get("colunas", [])
    insights = analysis.get("insights", {})
    column_analysis = analysis.get("analise_colunas", {})

    mentioned_column = next(
        (
            column for column in columns
            if _normalize(str(column)) in lower_question
        ),
        None
    )

    if mentioned_column:
        details = column_analysis.get(mentioned_column, {})
        answer = [
            f"Análise da coluna {mentioned_column}",
            f"Tipo: {details.get('tipo', 'não identificado')}.",
            f"Valores preenchidos: {details.get('valores_preenchidos', 0)}.",
            f"Valores nulos: {details.get('valores_nulos', 0)}.",
            f"Valores únicos: {details.get('valores_unicos', 0)}."
        ]
        statistics = details.get("estatisticas")
        if statistics:
            answer.append(
                "Estatísticas: "
                f"mínimo {statistics['minimo']}, "
                f"máximo {statistics['maximo']}, "
                f"média {statistics['media']} e "
                f"mediana {statistics['mediana']}."
            )
        return "\n\n".join(answer)

    if any(term in lower_question for term in ("coluna", "campo", "variavel")):
        return "\n\n".join([
            "Estrutura do arquivo",
            f"O arquivo possui {total_columns} colunas e {total_records} registros.",
            "Colunas: " + ", ".join(str(column) for column in columns) + "."
        ])

    if any(term in lower_question for term in ("linha", "registro", "quantidade", "total")):
        return "\n\n".join([
            "Dimensão do arquivo",
            f"Foram encontrados {total_records} registros e {total_columns} colunas.",
            "Esse número foi calculado diretamente a partir da tabela enviada."
        ])

    highlights = []
    for group in ("gerais", "relacoes", "comparativos", "qualidade_dados"):
        values = insights.get(group, [])
        if isinstance(values, list):
            highlights.extend(str(value) for value in values[:3])

    if highlights:
        return "\n\n".join([
            "Resumo da análise",
            f"O arquivo contém {total_records} registros distribuídos em {total_columns} colunas.",
            "Principais achados:\n- " + "\n- ".join(highlights[:4])
        ])

    return "\n\n".join([
        "Resultado da análise",
        f"O arquivo contém {total_records} registros e {total_columns} colunas.",
        "Não foi identificado um achado específico para essa pergunta."
    ])


def _text_answer(question: str, text: str) -> str:
    keywords = {
        word for word in _normalize(question).split()
        if len(word) >= 4 and word not in {
            "qual", "quais", "como", "onde", "quando", "sobre",
            "esse", "esta", "para", "arquivo", "documento"
        }
    }
    paragraphs = [
        " ".join(paragraph.split())
        for paragraph in re.split(r"\n\s*\n|(?<=[.!?])\s+", text)
        if paragraph.strip()
    ]

    ranked = sorted(
        (
            (sum(keyword in _normalize(paragraph) for keyword in keywords), index, paragraph)
            for index, paragraph in enumerate(paragraphs)
        ),
        key=lambda item: (item[0], -item[1]),
        reverse=True
    )
    matches = [paragraph for score, _, paragraph in ranked if score > 0][:3]

    asks_for_summary = any(
        term in _normalize(question)
        for term in ("assunto", "tema", "resumo", "resuma", "principal")
    )
    if not matches and asks_for_summary:
        matches = paragraphs[:3]

    if matches:
        return "\n\n".join([
            "Resposta baseada no documento",
            "Encontrei estes trechos relacionados à sua pergunta:",
            "- " + "\n- ".join(matches),
            "A resposta foi construída apenas com o texto extraído do arquivo."
        ])

    excerpt = " ".join(text.split())[:700]
    return "\n\n".join([
        "Informação não localizada",
        "Não encontrei termos diretamente relacionados à pergunta no documento.",
        f"Trecho inicial disponível: {excerpt}",
        "Tente perguntar usando palavras que aparecem no arquivo."
    ])


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^\w\s]", " ", without_accents.lower())


def answer_question(file_path: str, source_name: str, question: str) -> dict:
    document = read_document(file_path)

    if document["kind"] == "table":
        answer = _table_answer(question, document["analysis"])
    else:
        answer = _text_answer(question, document["text"])

    return {
        "source_name": source_name,
        "question": question,
        "answer": answer,
        "kind": document["kind"],
        "analysis": document["analysis"]
    }
