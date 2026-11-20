# Skill `refactor-arch`: auditoria e refatoração arquitetural automatizada

Entrega do desafio **Criação de Skills: Refatoração Arquitetural Automatizada** (módulo Desenvolvimento de Software e Aplicações com IA). A skill `refactor-arch`, para o Claude Code, analisa um backend, audita o código contra um catálogo de anti-patterns, gera um relatório com arquivo e linha de cada problema, **pausa para confirmação** e refatora o projeto para MVC, validando que a aplicação continua de pé.

Ela foi executada nos três projetos legados do repositório (dois Python/Flask e um Node.js/Express). O código refatorado e os relatórios estão commitados.

| O que | Onde |
|-------|------|
| Skill (idêntica nos três projetos) | `*/.claude/skills/refactor-arch/` (`SKILL.md` + 5 referências) |
| Relatórios da Fase 2 | [reports/audit-project-1.md](reports/audit-project-1.md), [reports/audit-project-2.md](reports/audit-project-2.md), [reports/audit-project-3.md](reports/audit-project-3.md) |
| Código refatorado | `code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/` |

---

## A) Análise Manual

Antes de escrever a skill, li o código dos três projetos e registrei os problemas abaixo. Os números de linha se referem aos arquivos **originais** (commit `6d1ce62`). Esta lista foi o insumo do catálogo de anti-patterns: cada item virou um sinal de detecção concreto.

### Projeto 1: `code-smells-project` (Python/Flask, API de e-commerce)

| # | Severidade | Problema | Local | Por que é relevante |
|---|-----------|----------|-------|---------------------|
| 1 | CRITICAL | SQL Injection por concatenação de string em todas as queries, inclusive no login | `models.py:28`, `models.py:109-111`, `models.py:291-293` | `' OR '1'='1` no login entra sem senha; a busca por texto livre permite ler ou apagar qualquer tabela |
| 2 | CRITICAL | Endpoint que executa SQL arbitrário enviado pelo cliente, sem autenticação, e reset do banco aberto | `app.py:47-78` | Qualquer pessoa na rede apaga o banco ou lê a tabela de usuários |
| 3 | CRITICAL | `SECRET_KEY` hardcoded e devolvida no `/health` | `app.py:7`, `controllers.py:289` | Quem lê o repositório ou chama `/health` obtém a chave que assina sessões |
| 4 | CRITICAL | Senha guardada em texto puro e devolvida em `GET /usuarios` | `models.py:83`, `models.py:126-129` | Vazamento direto de credenciais (LGPD) |
| 5 | HIGH | Debug ligado e bind em `0.0.0.0` fixos no código | `app.py:8`, `app.py:88` | O console de debug do Werkzeug permite execução remota de código |
| 6 | HIGH | Conexão SQLite global compartilhada entre threads (`check_same_thread=False`) | `database.py:4-10` | Estado global mutável; condições de corrida entre requisições |
| 7 | MEDIUM | Query N+1 ao listar pedidos (uma query por pedido e outra por item) | `models.py:187-199`, `models.py:219-231` | Cresce linearmente com o número de pedidos e itens |
| 8 | MEDIUM | Validação de produto duplicada entre criar e atualizar | `controllers.py:28-50`, `controllers.py:72-90` | Regras divergem com o tempo (atualizar já não valida tamanho do nome) |
| 9 | LOW | Faixas de desconto como magic numbers | `models.py:257-262` | Regra de negócio escondida em literais |
| 10 | LOW | `print` no lugar de logger e imports não usados | `controllers.py:8`, `controllers.py:208-210`, `database.py:2`, `models.py:2` | Sem nível de log nem como desligar; ruído no código |

### Projeto 2: `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

| # | Severidade | Problema | Local | Por que é relevante |
|---|-----------|----------|-------|---------------------|
| 1 | CRITICAL | Senha do banco e chave **de produção** do gateway de pagamento hardcoded | `src/utils.js:2-4` | Quem lê o repositório usa a chave `pk_live_...` |
| 2 | CRITICAL | Número completo do cartão e a chave do gateway gravados no log | `src/AppManager.js:45` | Violação de PCI-DSS; o log vira fonte de vazamento |
| 3 | CRITICAL | God Class `AppManager`: cria o banco, faz seed, registra rotas e executa a regra de checkout | `src/AppManager.js:4-139` | Impossível testar ou alterar uma parte sem tocar em tudo |
| 4 | HIGH | Hash de senha caseiro (`badCrypto`: base64 repetido e truncado) | `src/utils.js:17-23` | Reversível na prática; senha padrão `123456` quando não informada |
| 5 | HIGH | Estado global mutável exportado (`globalCache`, `totalRevenue`) | `src/utils.js:9-10` | Vazamento de memória e dependência da ordem das requisições |
| 6 | MEDIUM | Relatório financeiro com N+1 e contadores manuais de pendências | `src/AppManager.js:89-127` | Uma query por curso, por matrícula e por pagamento |
| 7 | MEDIUM | Callback hell no checkout (5 níveis) sem transação | `src/AppManager.js:37-77` | Falha no meio deixa matrícula sem pagamento |
| 8 | MEDIUM | `DELETE /api/users/:id` sem autenticação e deixando matrículas órfãs | `src/AppManager.js:131-137` | Qualquer cliente apaga usuários; dados inconsistentes |
| 9 | LOW | Nomes opacos (`u`, `e`, `p`, `cid`, `cc`) | `src/AppManager.js:29-33` | Legibilidade |
| 10 | LOW | Código morto (`totalRevenue` exportado e nunca usado) e `console.log` como logger | `src/utils.js:10`, `src/utils.js:13` | Ruído e falsa impressão de funcionalidade |

### Projeto 3: `task-manager-api` (Python/Flask, Task Manager parcialmente organizado)

| # | Severidade | Problema | Local | Por que é relevante |
|---|-----------|----------|-------|---------------------|
| 1 | CRITICAL | `User.to_dict()` inclui o hash da senha e é usado em várias respostas, inclusive no login | `models/user.py:21`, `routes/user_routes.py:209` | O hash vaza para qualquer cliente |
| 2 | CRITICAL | `SECRET_KEY` e senha do SMTP hardcoded | `app.py:13`, `services/notification_service.py:10` | Credenciais no repositório |
| 3 | HIGH | Senha com MD5 sem salt | `models/user.py:29-32` | Quebrável por tabela pronta |
| 4 | HIGH | Token de login falso e previsível (`'fake-jwt-token-' + id`) | `routes/user_routes.py:210` | Não há autenticação de verdade |
| 5 | HIGH | Rotas gordas: serialização, cálculo de atraso e busca de relacionamentos dentro do handler | `routes/task_routes.py:11-63` | A camada `routes/` faz papel de controller e de service |
| 6 | MEDIUM | N+1: `User.query.get` e `Category.query.get` dentro do laço de tasks | `routes/task_routes.py:41-57`, `routes/report_routes.py:55-56` | Uma query extra por task |
| 7 | MEDIUM | APIs deprecated: `Query.get()` (legada no SQLAlchemy 2.x) e `datetime.utcnow()` (deprecated no Python 3.12) | `routes/task_routes.py:42`, `models/task.py:15` (e outros) | Avisos hoje, quebra em versões futuras |
| 8 | MEDIUM | Regra "task atrasada" reimplementada em 4 lugares, enquanto `Task.is_overdue()` existe e não é usado | `routes/task_routes.py:30-39`, `routes/task_routes.py:71-80`, `routes/user_routes.py:171-180`, `models/task.py:50` | Duplicação que diverge |
| 9 | LOW | Imports não usados | `app.py:7`, `routes/task_routes.py:7`, `utils/helpers.py:3-7` | Ruído |
| 10 | LOW | Listas de status e limites repetidos como literais, enquanto as constantes existem em `utils/helpers.py:110-116` | `routes/task_routes.py:110`, `routes/user_routes.py:64` | Magic numbers e constantes ignoradas |

---

## B) Construção da Skill

### Decisões de design

- **O `SKILL.md` é o roteiro; as referências são o conhecimento.** O `SKILL.md` descreve só as três fases, as regras invioláveis e os formatos de saída. Tudo que depende de stack mora nas referências, em tabelas por linguagem. Assim o prompt principal fica curto e cada referência só é lida na fase em que é necessária.
- **Cinco referências, uma por área exigida:**

| Arquivo | Área | Conteúdo |
|---------|------|----------|
| `references/01-project-analysis.md` | Análise de projeto | Inventário, detecção de linguagem, framework, banco, domínio, mapeamento de endpoints por stack, classificação da arquitetura e como preparar o ambiente para a linha de base |
| `references/02-anti-patterns-catalog.md` | Catálogo de anti-patterns | 21 anti-patterns (AP-01 a AP-21) com severidade, sinais de detecção (incluindo comandos `grep`), o que **não** é achado e o padrão do playbook que corrige |
| `references/03-report-template.md` | Template de relatório | Estrutura obrigatória, regras de preenchimento e um exemplo de achado bem preenchido |
| `references/04-mvc-guidelines.md` | Guidelines de arquitetura | Camadas, o que cada uma pode e não pode fazer, direção das dependências, estrutura alvo para Flask e Express e a tabela de adaptação ao ponto de partida |
| `references/05-refactoring-playbook.md` | Playbook de refatoração | 17 padrões (P-01 a P-17) com código antes/depois em Python e JavaScript |

- **Regras invioláveis no topo do `SKILL.md`:** nenhum arquivo do projeto muda antes da confirmação; arquivo e linha conferidos com ferramenta, nunca estimados; contrato público preservado, com mudanças só por segurança e documentadas; o `✓` de validação só aparece quando o comando rodou e passou; segredos são citados mascarados.
- **Linha de base de runtime na Fase 1.** Antes de auditar, a skill sobe a aplicação original e registra o status e o formato de resposta de cada endpoint. Na Fase 3, repete as mesmas requisições e compara. É isso que transforma "os endpoints continuam respondendo" em evidência.
- **Pausa obrigatória.** A Fase 2 termina com `Proceed with refactoring (Phase 3)? [y/n]` e a instrução de parar. Qualquer resposta diferente de confirmação encerra sem tocar no código.

### Anti-patterns do catálogo e por quê

| Severidade | Anti-patterns | Motivo da escolha |
|-----------|---------------|-------------------|
| CRITICAL | SQL Injection, segredos hardcoded, God Class, dado sensível em resposta ou log, rota administrativa sem autenticação | Apareceram na análise manual nos três projetos e expõem dados ou impedem manutenção |
| HIGH | Hash de senha fraco, fat controller, acoplamento sem DI, estado global mutável, debug ligado | Violações fortes de MVC/SOLID ou de segurança que dificultam teste e operação |
| MEDIUM | N+1, erro espalhado, validação ausente ou duplicada, duplicação, **API deprecated**, callback hell, escrita múltipla sem transação | Padronização e performance. A detecção de API deprecated (AP-15) traz uma tabela por stack com o equivalente moderno (`Query.get` para `db.session.get`, `utcnow` para `now(timezone.utc)`, `new Buffer` para `Buffer.from`, callbacks para Promise etc.) e inclui dependências com vulnerabilidade conhecida |
| LOW | Magic numbers, nomes opacos, `print`/`console.log`, código morto | Legibilidade |

### Como a skill ficou agnóstica de tecnologia

- **Nada de stack no `SKILL.md`.** Ele fala em "manifesto de dependências", "camada de rotas" e "ferramenta de auditoria da stack"; os nomes concretos estão nas tabelas das referências.
- **Detecção por evidência:** linguagem pelo manifesto, framework pela dependência e pelo import, banco pelo driver, domínio pelas tabelas e rotas.
- **Estrutura alvo por stack** (Flask e Express) e uma regra para outras stacks: aplicar a mesma transformação com o idioma delas.
- **Adaptação ao ponto de partida:** monolito sem camadas, camadas nominais, parcialmente organizado e já em MVC recebem tratamentos diferentes. Foi isso que permitiu à skill completar a estrutura do `task-manager-api` em vez de recriá-la do zero.
- **Validação por HTTP**, que funciona igual em qualquer stack.

### Desafios encontrados e como resolvi

1. **Porta 5000 ocupada no macOS** (AirPlay). Os dois projetos Flask fixavam a porta no código. Coloquei nas referências a orientação de subir a app original importando o objeto e escolhendo outra porta, sem editar código na Fase 1. Na Fase 3, a porta passa a vir de `PORT`.
2. **Validar a pausa sem modo interativo.** Rodei a skill com `claude -p "/refactor-arch ../reports/audit-project-N.md"`. A sessão para na pergunta da Fase 2 e eu retomo com `claude -p "y" --resume <sessão>`. Entre uma chamada e outra, conferi o relatório e o `git status`: só o relatório tinha sido criado.
3. **Dependências vulneráveis que a primeira versão da skill não cobria em todos os projetos.** No projeto 2, a skill apontou e corrigiu parte delas. Nos projetos 1 e 3, os gates que rodei depois (`pip-audit`) acharam `flask-cors` e `python-dotenv` com CVE. Corrigi atualizando para versões publicadas há pelo menos 7 dias e **iterei a skill**: as Fases 2 e 3 agora auditam as dependências explicitamente (passo 6 da Fase 2 e passo 6.6 da Fase 3 do `SKILL.md`).
4. **Projeto parcialmente organizado.** O risco era a skill recriar tudo. A tabela "Adaptação ao ponto de partida" fez a Fase 3 manter o que estava certo, criar `controllers/` e `services/` e mover a regra de negócio para lá.
5. **Contrato versus segurança.** Remover a senha das respostas ou exigir token nas rotas destrutivas muda a resposta da API. A regra ficou explícita: mudança de contrato só por segurança, listada na seção "Contract changes" da Fase 3.

---

## C) Resultados

### Achados por projeto (Fase 2)

| Projeto | Stack detectada | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|-----------------|----------|---------|------|--------|-----|-------|
| 1. code-smells-project | Python + Flask 3.1.1 | 4 | 6 | 5 | 5 | 4 | **20** |
| 2. ecommerce-api-legacy | JavaScript (Node.js) + Express 4 | 3 | 4 | 5 | 6 | 4 | **19** |
| 3. task-manager-api | Python + Flask 3.0.0 (Flask-SQLAlchemy) | 15 | 3 | 5 | 6 | 4 | **18** |

Em todos os projetos, a Fase 2 encontrou os problemas da análise manual acima, incluindo os CRITICAL e HIGH.

### Antes e depois da estrutura

**Projeto 1**

```
ANTES                         DEPOIS
app.py  (rotas + admin)       app.py                      # entry point: create_app()
controllers.py                src/config/settings.py      # variáveis de ambiente
models.py (4 domínios + SQL)  src/database.py             # conexão por requisição, schema, seed
database.py (global)          src/models/                 # produto, usuario, pedido, admin
                              src/services/               # pedido, relatorio, usuario, notificação
                              src/controllers/            # um por domínio + validators
                              src/views/routes.py         # só roteamento
                              src/middlewares/            # error_handler, auth (token admin)
                              src/errors.py, src/security.py, src/constants.py
```

**Projeto 2**

```
ANTES                         DEPOIS
src/app.js                    src/server.js               # listen
src/AppManager.js (God Class) src/app.js                  # composition root (injeção de dependência)
src/utils.js (config+cache)   src/config/index.js
                              src/database/               # conexão com Promise, schema e seed
                              src/models/                 # user, course, enrollment, payment, auditLog
                              src/services/               # checkout, report, user, paymentGateway, passwordHasher
                              src/controllers/            # checkout, report, user + validators
                              src/routes/index.js         # camada View
                              src/middlewares/            # errorHandler, requireAdmin
```

**Projeto 3**

```
ANTES                         DEPOIS
app.py                        app.py + seed.py
database.py                   src/config/settings.py, src/database.py
models/ (senha no dict)       src/models/                 # task, user, category (serialização única, sem senha)
routes/ (rotas gordas)        src/routes/                 # só roteamento (blueprints)
services/ (só notificação)    src/controllers/            # novo: fluxo da requisição + validators
utils/helpers.py              src/services/               # task, user, auth, category, report, notification
                              src/middlewares/            # error_handler, auth (token assinado)
                              src/security.py, src/clock.py, src/constants.py
```

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|------|:---------:|:---------:|:---------:|
| **Fase 1:** linguagem detectada corretamente | ✅ Python | ✅ JavaScript (Node.js) | ✅ Python |
| **Fase 1:** framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4 | ✅ Flask 3.0.0 + Flask-SQLAlchemy |
| **Fase 1:** domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| **Fase 1:** número de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2:** relatório segue o template | ✅ | ✅ | ✅ |
| **Fase 2:** cada achado com arquivo e linhas exatos | ✅ | ✅ | ✅ |
| **Fase 2:** ordenado de CRITICAL a LOW | ✅ | ✅ | ✅ |
| **Fase 2:** mínimo de 5 achados | ✅ 20 | ✅ 19 | ✅ 18 |
| **Fase 2:** APIs deprecated | ✅ seção presente (nenhuma no código) | ✅ callbacks do sqlite3 e dependências vulneráveis | ✅ `Query.get`, `datetime.utcnow`, MD5 |
| **Fase 2:** pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3:** estrutura segue MVC | ✅ | ✅ | ✅ |
| **Fase 3:** configuração extraída (sem hardcoded) | ✅ | ✅ | ✅ |
| **Fase 3:** models abstraem os dados | ✅ | ✅ | ✅ |
| **Fase 3:** views/routes separadas | ✅ | ✅ | ✅ |
| **Fase 3:** controllers concentram o fluxo | ✅ | ✅ | ✅ |
| **Fase 3:** error handling centralizado | ✅ | ✅ | ✅ |
| **Fase 3:** entry point claro | ✅ `app.py` | ✅ `src/server.js` + `src/app.js` | ✅ `app.py` |
| **Fase 3:** aplicação inicia sem erros | ✅ | ✅ | ✅ |
| **Fase 3:** endpoints originais respondem | ✅ | ✅ | ✅ |

### Evidência: aplicações rodando após a refatoração

Além da validação feita pela própria skill, rodei uma verificação independente: um script que repete as mesmas requisições contra a aplicação **original** e a **refatorada** e compara status HTTP e chaves da resposta. As únicas diferenças são as correções de segurança documentadas.

**Projeto 1:** 22 requisições, 21 idênticas. A diferença é a remoção de `secret_key`, `db_path` e `debug` do `/health`.

```
GET /produtos -> 200 ['dados', 'sucesso']                     (igual)
POST /login -> 200 / 401                                       (igual)
POST /pedidos -> 201 / 400 (estoque insuficiente)              (igual)
GET /relatorios/vendas -> 200 ['dados', 'sucesso']             (igual)
< GET /health -> 200 ['ambiente','counts','database','db_path','debug','secret_key','status','versao']
> GET /health -> 200 ['ambiente','counts','database','status','versao']
POST /admin/reset-db sem token -> 403
POST /login com "x' OR '1'='1" -> 401
```

**Projeto 2:** os 4 cenários de checkout são idênticos (200, 400 pagamento recusado, 404 curso, 400 bad request). As rotas administrativas respondem 401 sem token e, com `Authorization: Bearer <ADMIN_TOKEN>`, devolvem exatamente o mesmo que a original. Um `card` numérico, que derrubava o processo, agora devolve 400 e o servidor continua de pé.

```
< GET /api/admin/financial-report -> 200 list[2]
> GET /api/admin/financial-report -> 401 text:Não autorizado     (sem token)
GET /api/admin/financial-report com token -> 200 [{"course":"Clean Architecture","revenue":997,...}]
POST /api/checkout com "card": 4111 -> 400 Bad Request; servidor segue respondendo 200
```

**Projeto 3:** 26 requisições. As diferenças são o campo `password` removido de `/users` e o 401 nos `DELETE` sem token; com o token de admin obtido no `/login`, os três `DELETE` devolvem 200 como no original.

```
< GET /users/1 -> 200 ['active','created_at','email','id','name','password','role','tasks']
> GET /users/1 -> 200 ['active','created_at','email','id','name','role','tasks']
> DELETE /tasks/3 -> 401 (sem token) | 200 (com token de admin)
GET /tasks, /tasks/stats, /reports/summary, /categories -> iguais à linha de base
```

Gates de segurança no código final dos três projetos: `ruff` com as regras do Bandit sem achados (falsos positivos anotados linha a linha com o motivo), `pip-audit` e `npm audit --omit=dev` sem vulnerabilidades conhecidas.

### Observações sobre stacks diferentes

- **Flask monolítico (projeto 1):** a skill criou a estrutura completa e usou o padrão de factory (`create_app`) como composition root.
- **Express (projeto 2):** a maior transformação foi trocar callbacks aninhados por um wrapper de Promise com `async/await`, e a transação do checkout. A skill também achou um bug real durante a linha de base: `card` numérico derrubava o processo.
- **Flask parcialmente organizado (projeto 3):** a skill não recriou o projeto. Criou as camadas que faltavam (controllers e services), tirou a regra de negócio das rotas, unificou a serialização e trocou as APIs deprecated.
- **Mesmo `SKILL.md` nos três**, sem nenhuma adaptação manual entre uma execução e outra.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code) instalado e autenticado.
- Python 3.10+ (testado com 3.12) para os projetos Flask; Node.js 20+ para o projeto Express.
- Opcional, para os gates: [`uv`](https://docs.astral.sh/uv/) (`uvx pip-audit`, `uvx ruff`).

### Executar a skill

A skill é invocada de dentro de cada projeto. O argumento opcional é o caminho do relatório.

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch ../reports/audit-project-1.md"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch ../reports/audit-project-2.md"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch ../reports/audit-project-3.md"
```

Ao fim da Fase 2, a skill pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar. Em modo não interativo: `claude -p "/refactor-arch ..."` e depois `claude -p "y" --resume <id-da-sessão>`.

### Validar a refatoração

Cada projeto tem um `.env.example` com as variáveis. Exemplos:

```bash
# Projeto 1 (Flask)
cd code-smells-project
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PORT=5001 ADMIN_TOKEN=troque SEED_ADMIN_PASSWORD=troque SEED_CUSTOMER_PASSWORD=troque .venv/bin/python app.py
curl http://localhost:5001/produtos

# Projeto 2 (Express)
cd ecommerce-api-legacy
npm ci --ignore-scripts && npm rebuild sqlite3
ADMIN_TOKEN=troque npm start
curl -X POST http://localhost:3000/api/checkout -H 'Content-Type: application/json' \
  -d '{"usr":"Ana","eml":"ana@x.com","pwd":"senha","c_id":2,"card":"4111222233334444"}'

# Projeto 3 (Flask)
cd task-manager-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
SEED_PASSWORD=troque .venv/bin/python seed.py
PORT=5003 SECRET_KEY=troque .venv/bin/python app.py
curl http://localhost:5003/tasks
```

No macOS, a porta 5000 costuma estar ocupada pelo AirPlay; por isso os exemplos usam `PORT`. Cada projeto tem um README próprio com todos os endpoints e variáveis.

### Ordem sugerida

1. Ler a análise manual (seção A) e um relatório da Fase 2 (`reports/`).
2. Ler o `SKILL.md` e as referências em `code-smells-project/.claude/skills/refactor-arch/`.
3. Rodar a skill num clone do repositório, para ver as três fases.
4. Validar com os comandos acima.
