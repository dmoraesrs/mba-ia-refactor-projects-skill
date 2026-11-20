# 01: Análise de projeto (Fase 1)

Heurísticas para detectar a stack, o banco, o domínio e a arquitetura atual de qualquer backend. Siga as seções em ordem; cada conclusão precisa de uma evidência (arquivo e linha ou trecho do manifesto).

## 1. Inventário de arquivos-fonte

- Liste com `find . -type f` excluindo: `.git`, `.claude`, `node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `coverage`, `instance`.
- Arquivos-fonte são os de código da aplicação (`.py`, `.js`, `.ts`, `.mjs`, `.cjs`, `.go`, `.java`, `.rb`, `.php`, `.cs`). Manifestos, lockfiles, `.http`, `.md` e bancos `.db`/`.sqlite` **não** entram na contagem de arquivos-fonte, mas são lidos como evidência.
- Conte linhas com `wc -l` sobre a lista final. Informe o total aproximado.

## 2. Linguagem e framework

| Evidência | Linguagem | Como achar o framework e a versão |
|-----------|-----------|-----------------------------------|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | Linha `flask==X`, `django==X`, `fastapi==X`; import `from flask import Flask` |
| `package.json` | JavaScript (TypeScript se houver `tsconfig.json` ou `.ts`) | `dependencies.express`, `fastify`, `@nestjs/core`, `koa`; `require('express')` ou `import express` |
| `go.mod` | Go | `github.com/gin-gonic/gin`, `github.com/labstack/echo`, `net/http` |
| `pom.xml`, `build.gradle` | Java/Kotlin | `spring-boot-starter-web` |
| `Gemfile` | Ruby | `rails`, `sinatra` |
| `composer.json` | PHP | `laravel/framework`, `slim/slim` |

- A versão vem do manifesto. Se o manifesto usar faixa (`^4.18.2`), informe a faixa e, se existir lockfile, a versão resolvida.
- Liste as dependências relevantes (ORM, driver de banco, CORS, validação, HTTP client), não o lockfile inteiro.

## 3. Banco de dados e tabelas

| Sinal no código | Banco | Onde estão as tabelas |
|-----------------|-------|-----------------------|
| `sqlite3.connect(`, `new sqlite3.Database(`, `sqlite:///` | SQLite | `CREATE TABLE` no código ou classes de model |
| `psycopg`, `pg`, `postgresql://` | PostgreSQL | migrations, `CREATE TABLE`, models |
| `mysql`, `pymysql`, `mysql2` | MySQL | idem |
| `mongoose`, `pymongo` | MongoDB | schemas/collections |
| `SQLAlchemy`, `db.Model`, `__tablename__` | ORM (o banco sai da URI) | atributo `__tablename__` ou nome da classe |
| `sequelize.define`, `prisma/schema.prisma`, `typeorm` | ORM Node | definição dos models |

- Registre se o banco é em arquivo, em memória (`:memory:`) ou externo, e se há seed automático no boot.

## 4. Domínio da aplicação

Deduza o domínio a partir de três fontes, nesta ordem de peso:

1. **Nomes das tabelas e entidades** (`produtos`, `pedidos` sugerem e-commerce; `tasks`, `categories` sugerem task manager; `courses`, `enrollments` sugerem LMS).
2. **Rotas** (`/checkout`, `/relatorios/vendas`, `/tasks/stats`).
3. **README e mensagens** da própria aplicação.

Escreva o domínio em uma linha com as entidades principais. Exemplo: `E-commerce API (produtos, pedidos, usuários)`.

## 5. Mapeamento de endpoints

| Stack | Padrão de rota | Comando de busca |
|-------|----------------|------------------|
| Flask | `@app.route(`, `@bp.route(`, `app.add_url_rule(`, `Blueprint(` | `grep -rnE "route\(|add_url_rule\(" --include=*.py .` |
| FastAPI | `@app.get(`, `@router.post(` | `grep -rnE "@(app|router)\.(get|post|put|patch|delete)\(" .` |
| Express | `app.get(`, `router.post(`, `app.use('/prefixo', router)` | `grep -rnE "(app|router)\.(get|post|put|patch|delete)\(" --include=*.js .` |
| Django | `path(`, `re_path(` em `urls.py` | `grep -rn "path(" --include=urls.py .` |

- Para cada endpoint: método, caminho completo (some o prefixo do blueprint/router), handler e arquivo:linha.
- Inclua rotas administrativas e de debug: são as que mais escondem problemas de segurança.

## 6. Arquitetura atual

Classifique com base na distribuição de responsabilidades, não no nome das pastas:

| Classificação | Sinais |
|---------------|--------|
| **Monolítica sem camadas** | Poucos arquivos fazem tudo: rota, SQL, regra de negócio e formatação no mesmo arquivo ou na mesma classe. Ex.: uma classe `AppManager` que cria o banco e registra rotas |
| **Camadas nominais** | Existem arquivos chamados `models`, `controllers`, mas o conteúdo não respeita o nome (SQL no controller, regra de negócio no model, rota no `app.py`) |
| **Parcialmente organizada** | Pastas `models/`, `routes/`, `services/`, `utils/` com separação real em parte, mas rotas gordas com regra de negócio, serialização duplicada, services pouco usados, config hardcoded |
| **MVC/camadas adequado** | Rotas só roteiam, controllers orquestram, models encapsulam dados, config externa, erro centralizado |

Descreva em uma linha: classificação + principal problema de organização. Exemplo: `Monolítica, tudo em 4 arquivos, SQL e regra de negócio misturados com roteamento`.

## 7. Ambiente de execução (para a linha de base e a validação)

| Stack | Preparar dependências | Subir | Observações |
|-------|----------------------|-------|-------------|
| Python | `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` (use Python 3.10 ou superior se disponível, por exemplo `python3.12`) | `.venv/bin/python app.py` ou importar a app e chamar `app.run(port=<livre>)` | Se a porta do código estiver ocupada (no macOS a 5000 costuma ser do AirPlay), suba importando a app em outra porta, sem editar o código na Fase 1 |
| Node | `npm ci` ou `npm install` com `--ignore-scripts`; depois `npm rebuild <pacote-nativo>` só para o que precisa compilar (ex.: `sqlite3`) | `npm start` ou `node <main>` | Para trocar a porta sem editar código, use a variável que o código ler; se não ler nenhuma, mate o processo que ocupa a porta só se for seu |

- Confira porta livre com `lsof -nP -iTCP:<porta> -sTCP:LISTEN` antes de subir.
- Rode o processo em background, espere ficar pronto (tente `curl` por até 15 s) e mate pelo PID ao terminar.
- Projetos que exigem seed antes do primeiro boot (README diz "rode seed.py") precisam do seed antes da linha de base.
- Use `curl -s -o /dev/null -w "%{http_code}"` para status e `curl -s` para o corpo. Registre para cada requisição: método, caminho, corpo enviado, status, chaves de topo do JSON (ou início do texto).
