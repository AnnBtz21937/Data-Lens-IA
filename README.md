# BDIA

Sistema web para envio de documentos, análise de dados e perguntas sobre o conteúdo das fontes. Atividade solicitada na disciplina de Sistemas Inteligentes, do professor Edilson Lima, da Universidade CEUMA, no curso de Engenharia de Computação.

O sistema não utiliza APIs externas de IA, como OpenAI ou Gemini. A interpretação em linguagem natural é realizada pelo modelo Llama 3.2 1B executado localmente por meio do Ollama. A API da aplicação foi desenvolvida pela dupla utilizando FastAPI.

BDIA - é B de Beatriz e D de Duda, a dupla da atividade. 

## Comece aqui

Para rodar na sua máquina, você precisa de Python 3.12 ou compatível. O modo local usa SQLite automaticamente, então não é necessário instalar MySQL para começar.

```bash
git clone https://github.com/AnnBtz21937/Data-Lens-IA.git
cd Data-Lens-IA
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Linux ou macOS
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências e siga para [Executar localmente](#executar-localmente):

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

## Visão geral

O projeto é dividido em duas partes:

- `front-end/`: interface estática em HTML, CSS e JavaScript.
- `backend/`: API FastAPI, autenticação JWT, banco SQLAlchemy e serviços de leitura/análise.

O frontend não acessa o banco diretamente. Ele conversa com a API em `http://localhost:8000` usando `fetch`. A API grava usuários, projetos e fontes no banco e processa os arquivos enviados.

## Fluxo da aplicação

1. O usuário cria uma conta em `POST /users/`.
2. O login envia e-mail e senha para `POST /auth/login`.
3. A API devolve um token JWT. O frontend guarda o token no `localStorage` e o envia no cabeçalho `Authorization: Bearer <token>`.
4. Depois do login, o frontend carrega o usuário em `GET /users/me`.
5. O primeiro projeto do usuário é carregado por `GET /projects/`. Se não existir nenhum, o frontend cria um projeto inicial com `POST /projects/`.
6. As fontes do projeto são carregadas por `GET /sources/project/{project_id}`.
7. Um upload é enviado como `multipart/form-data` para `POST /sources/{project_id}/upload`.
8. A pergunta é enviada para `POST /sources/{source_id}/ask`.
9. O backend lê novamente o arquivo, calcula a resposta com base no conteúdo e devolve a resposta e os dados da análise.
10. O frontend exibe a resposta, incrementa as perguntas respondidas e marca o conteúdo como analisado.

Cada pergunta respondida é salva na tabela `questions` com usuário, projeto, fonte, pergunta, resposta e data. Ao abrir ou trocar de projeto, o frontend chama `GET /projects/{project_id}/history`, restaura a conversa e atualiza o contador de perguntas a partir do banco.

## Estrutura do backend

```text
backend/app/
	main.py                 inicialização da API, CORS e rotas
	database.py             conexão SQLAlchemy e fallback SQLite local
	models/                 tabelas User, Project e Source
	models/question.py      histórico persistente de perguntas e respostas
	schemas/                modelos de entrada da API
	routes/auth.py          login e validação do JWT
	routes/users.py         criação e consulta do usuário autenticado
	routes/projects.py      criação e listagem de projetos
	routes/source.py        upload, fontes, análise e perguntas
	services/analysis.py    estatísticas e relações para CSV/Excel
	services/documents.py   leitura de PDF, DOCX, TXT, CSV e Excel
	services/ai.py          integração com Ollama e criação de prompts
```

## Formatos aceitos

- `PDF`: texto extraído com `pypdf`.
- `DOCX`: parágrafos e tabelas extraídos com `python-docx`.
- `TXT`: leitura com tentativas de UTF-8, CP1252 e Latin-1.
- `CSV`: separador e encoding detectados pelo pandas.
- `XLSX` e `XLS`: leitura com pandas, OpenPyXL e xlrd.
- `MySQL`: consulta SQL informada pelo usuário usando SQLAlchemy/PyMySQL.
- `MongoDB`: consulta simples por coleção e filtro JSON usando PyMongo.

Arquivos `.doc` antigos não são processados diretamente. Salve-os como `.docx` antes do upload.

Fontes MySQL e MongoDB não enviam arquivos: o sistema executa uma consulta controlada no momento do cadastro, guarda o resultado consultado como fonte tabular e permite fazer perguntas sobre esse resultado.

Para MongoDB, informe a URL com o banco e use uma coleção seguida, opcionalmente, por um filtro JSON:

```text
mongodb://localhost:27017/meu_banco
clientes?{"status":"ativo"}
```

Sem filtro, use apenas o nome da coleção. O backend limita a consulta a 1.000 registros e converte o campo `_id` para texto.

## Como as respostas são produzidas

O sistema atual é fundamentado no arquivo e não inventa dados:

- Em documentos de texto, a pergunta é normalizada, os trechos são classificados pela quantidade de termos relevantes e os melhores trechos são apresentados como evidência.
- Perguntas sobre assunto, tema ou resumo usam os primeiros parágrafos quando não existe uma palavra idêntica no texto.
- Em tabelas, perguntas sobre colunas listam a estrutura; perguntas sobre registros informam dimensões; perguntas que citam uma coluna mostram tipo, nulos, valores únicos e estatísticas numéricas.
- Perguntas gerais usam os insights calculados pelo analisador, incluindo relações categóricas e qualidade dos dados.
- Quando a informação não está disponível, a resposta informa isso e mostra um trecho de contexto, em vez de afirmar algo sem evidência.

Para perguntas que precisam de uma resposta em linguagem natural, o backend chama o Ollama local em `http://localhost:11434` usando o modelo `llama3.2:1b`. A análise estrutural dos arquivos continua funcionando sem o modelo, mas o chat pode falhar ou usar o fallback local se o Ollama não estiver ativo.

Instale o Ollama e baixe o modelo:

```bash
ollama pull llama3.2:1b
ollama serve
```

## Requisitos e instalação

Use Python 3.12 ou compatível. A forma recomendada é instalar tudo pelo arquivo de dependências:

```bash
python -m pip install -r backend/requirements.txt
```

## Banco de dados

Se todas estas variáveis existirem, a API usa MySQL:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

Quando elas não existem, a aplicação usa `datalens.db` em SQLite para facilitar o desenvolvimento local. Arquivos enviados ficam na pasta `uploads/`.

## Executar localmente

Abra dois terminais na raiz do projeto. No Windows, use `py` no lugar de `python` se necessário.

### Terminal 1: API

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Teste a API:

```bash
curl http://localhost:8000/health
```

Resposta esperada: `{"status":"ok"}`.

### Terminal 2: frontend

```bash
cd front-end
python -m http.server 5500 --bind 0.0.0.0
```

Abra `http://localhost:5500`.

Documentação automática da API: `http://localhost:8000/docs`.

O frontend usa `front-end/config.js` para localizar a API. Localmente, a API fica na porta `8000`; em previews do Codespaces, o host encaminhado é adaptado automaticamente.

## Deploy público

O deploy recomendado separa os serviços:

- **Backend:** Render, usando o `render.yaml` da raiz.
- **Frontend:** Vercel, usando `front-end/` como Root Directory.
- **Banco:** MySQL externo. SQLite local não é adequado para produção.

### 1. Publicar o backend no Render

1. Suba o repositório para o GitHub.
2. No Render, escolha **New Blueprint** e selecione o repositório.
3. O Render encontrará `render.yaml` e criará o serviço `bdia-api`.
4. Configure as variáveis `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD` com os dados do MySQL.
5. Depois do deploy, teste `https://SEU-BACKEND.onrender.com/health`.

O endereço público da API será algo como:

```text
https://bdia-api.onrender.com
```

### 2. Ligar o frontend ao backend público

Edite `front-end/config.js` antes de publicar:

```javascript
window.BDIA_API_URL = "https://bdia-api.onrender.com";
```

No Render, configure `CORS_ORIGINS` com o domínio que a Vercel fornecerá, por exemplo:

```text
https://bdia.vercel.app
```

Durante o desenvolvimento, mantenha `http://localhost:8000` no `config.js`.

### 3. Publicar o frontend na Vercel

1. No Vercel, importe o mesmo repositório.
2. Defina `front-end` como **Root Directory**.
3. Não é necessário build command: é um frontend estático.
4. Publique e copie o domínio gerado.
5. Atualize `CORS_ORIGINS` no Render com esse domínio.
6. Faça um novo deploy do frontend depois de confirmar a URL da API em `front-end/config.js`.

### Cuidados de produção

- O SQLite e a pasta local `uploads/` são adequados apenas para testes. Em serviços gratuitos, arquivos locais podem ser apagados quando a aplicação reinicia.
- Para uso real, use MySQL persistente e armazenamento de arquivos, como Cloudinary, S3 ou Cloudflare R2.
- O backend chama o Ollama local para respostas em linguagem natural. Em produção, configure um provedor de IA acessível pelo backend ou mantenha respostas baseadas no fallback local.

## Rotas principais

| Método | Rota | Função |
| --- | --- | --- |
| `POST` | `/users/` | cria uma conta |
| `GET` | `/users/me` | retorna o usuário autenticado |
| `POST` | `/auth/login` | autentica com OAuth2 form e retorna JWT |
| `GET` | `/projects/` | lista projetos do usuário |
| `POST` | `/projects/` | cria um projeto |
| `GET` | `/sources/project/{project_id}` | lista fontes do projeto |
| `POST` | `/sources/{project_id}/upload` | envia uma fonte |
| `POST` | `/sources/{source_id}/analyze` | executa análise explícita |
| `POST` | `/sources/{source_id}/ask` | responde uma pergunta sobre a fonte |
| `GET` | `/projects/{project_id}/history` | carrega o histórico do projeto |

## Diagnóstico rápido

- Tela sem estilo: confirme que o frontend foi iniciado dentro de `front-end` e que `http://localhost:5500/style.css` retorna `200`.
- Erro de conexão: confirme que a API está em `http://localhost:8000`.
- Erro de banco MySQL: remova as variáveis MySQL para usar SQLite local ou configure todas corretamente.
- PDF sem resposta: PDFs escaneados como imagem precisam de OCR; o leitor atual extrai texto nativo do PDF.
- Arquivo `.doc`: converta para `.docx` antes do envio.
