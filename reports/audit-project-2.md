================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1 (^4.18.2)
Files:   3 analyzed | ~180 lines of code
Date:    2026-11-19

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials (AP-02)
File: src/utils.js:2-6, src/AppManager.js:18
Description: O objeto `config` define como literais `dbUser: 'admi***'`, `dbPass: 'senh***'`, `paymentGatewayKey: 'pk_l***'` (chave de produção, prefixo `pk_live_`) e `smtpUser: 'no-r***'`. O seed em `initDb` insere o usuário `leonan@...` com `pass` em texto puro `'1***'`.
Impact: Quem lê o repositório obtém a chave de produção do gateway de pagamento e a senha do banco; rotacionar exige novo deploy.
Recommendation: Criar módulo de config lendo `process.env` (PAYMENT_GATEWAY_KEY, PORT, DB_PATH), sem default secreto, e `.env.example` com placeholders; remover chaves não usadas (P-02).

### [CRITICAL] Sensitive Data Exposure in Logs (AP-04)
File: src/AppManager.js:45
Description: No checkout, `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave do gateway no stdout a cada compra (confirmado no log da linha de base).
Impact: Violação de PCI-DSS (PAN em log) e vazamento da chave de produção para qualquer sistema de agregação de logs.
Recommendation: Remover o log; se precisar rastrear, logar apenas os 4 últimos dígitos mascarados e nunca a chave (P-04, P-17).

### [CRITICAL] Unauthenticated Admin/Destructive Routes (AP-05)
File: src/AppManager.js:80, src/AppManager.js:131
Description: `GET /api/admin/financial-report` devolve nome de cada aluno e o valor pago por curso, e `DELETE /api/users/:id` apaga qualquer usuário; nenhuma das duas verifica identidade ou papel.
Impact: Qualquer cliente anônimo lê dados financeiros e pessoais (LGPD) e apaga usuários em massa.
Recommendation: Middleware de autorização administrativa (token em `ADMIN_TOKEN` via env, header `Authorization: Bearer`) aplicado às duas rotas; mudança de contrato de segurança registrada (P-05).

### [CRITICAL] God Class (AP-03)
File: src/AppManager.js:4-139
Description: A classe `AppManager` abre a conexão (`new sqlite3.Database(':memory:')`, linha 7), cria schema e seed (`initDb`, 10-23), executa todo o SQL, aplica a regra de aprovação de pagamento, cria usuários, grava auditoria, alimenta cache, monta o relatório e registra as três rotas Express (`setupRoutes`, 25-138).
Impact: Nada é testável em isolamento; qualquer mudança (trocar banco, mudar regra de pagamento) mexe no mesmo arquivo e no mesmo escopo de closures.
Recommendation: Separar em config, database (conexão + schema/seed), models (User, Course, Enrollment, Payment, AuditLog), services (Checkout, Report, User), controllers, routes e composition root em `app.js` (P-03).

### [HIGH] Missing Input Validation Crashes the Server (AP-13)
File: src/AppManager.js:29-35, src/AppManager.js:46, src/AppManager.js:132
Description: O checkout só confere presença de `usr`, `eml`, `c_id`, `card`; não checa tipo nem formato. Com `"card": 4111` (número), `cc.startsWith` lança `TypeError` dentro do callback do sqlite e **derruba o processo** (reproduzido: curl sem resposta e processo morto). `eml` não tem validação de formato e `:id` do DELETE não é validado. Severidade elevada de MEDIUM para HIGH por ser rota pública com impacto de disponibilidade.
Impact: Uma única requisição anônima tira a API do ar (DoS).
Recommendation: Validação centralizada do corpo do checkout (strings não vazias, `c_id` inteiro, `card` string de dígitos) antes de chamar o service, devolvendo o mesmo 400 "Bad Request" do contrato atual (P-11).

### [HIGH] Business Logic in Route Handlers (AP-07)
File: src/AppManager.js:28-78, src/AppManager.js:80-129
Description: O handler de `POST /api/checkout` (51 linhas) decide aprovação de pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`, linha 46), cria usuário implicitamente (66-72), grava matrícula, pagamento, auditoria e cache. O handler do relatório calcula receita somando só pagamentos `PAID` (108-110).
Impact: Regra de pagamento e de receita não reaproveitável nem testável sem HTTP.
Recommendation: Extrair `CheckoutService.checkout()` e `ReportService.financialReport()`; controller apenas lê a requisição e traduz resultado em resposta (P-07).

### [HIGH] Weak Password Hashing (AP-06)
File: src/utils.js:17-23, src/AppManager.js:68, src/AppManager.js:18
Description: `badCrypto` repete 10000 vezes os 2 primeiros caracteres do base64 da senha e corta em 10 caracteres: sem salt, reversível em parte e com colisões triviais (toda senha com o mesmo prefixo gera o mesmo "hash"). Se `pwd` não vier, usa a senha padrão literal `"123456"` (linha 68). O seed grava senha em texto puro (linha 18).
Impact: Senhas recuperáveis por qualquer um com acesso ao banco; contas criadas sem senha ficam com senha conhecida.
Recommendation: `crypto.scrypt` com salt aleatório (formato `salt:hash`); gerar senha aleatória quando `pwd` estiver ausente; seed com hash (P-06).

### [HIGH] Tight Coupling without Dependency Injection (AP-08)
File: src/AppManager.js:7, src/AppManager.js:2, src/app.js:8-10
Description: O construtor instancia a conexão concreta `new sqlite3.Database(':memory:')`; os handlers usam `config`, `logAndCache` e `badCrypto` importados direto de `utils`.
Impact: Impossível trocar o banco por um fake em teste ou apontar para outro arquivo sem editar a classe.
Recommendation: Composition root em `app.js` cria a conexão e injeta em models, services e controllers por construtor (P-08).

### [HIGH] Mutable Global State (AP-09)
File: src/utils.js:9-10, src/utils.js:14, src/utils.js:25
Description: `globalCache` é um objeto de módulo exportado e mutado a cada checkout (`globalCache[key] = data`) sem limite nem leitura; `totalRevenue` é um `let` de módulo exportado.
Impact: Crescimento de memória sem fim (uma chave por usuário que compra) e estado compartilhado que depende da ordem das requisições.
Recommendation: Remover o cache que ninguém lê e `totalRevenue`; se cache for necessário, um componente injetado com limite (P-08).

### [MEDIUM] N+1 Queries in Financial Report (AP-11)
File: src/AppManager.js:83, src/AppManager.js:92, src/AppManager.js:104, src/AppManager.js:106
Description: O relatório faz 1 query de cursos, 1 de matrículas por curso e, para cada matrícula, 1 de usuário e 1 de pagamento: 1 + C + 2E queries.
Impact: Tempo de resposta cresce linearmente com o número de matrículas.
Recommendation: Uma única query com `LEFT JOIN` de courses, enrollments, users e payments, agregando em memória no model/service (P-09).

### [MEDIUM] Callback Hell and Manual Pending Counters (AP-16)
File: src/AppManager.js:37-77, src/AppManager.js:86-121
Description: O checkout tem 6 níveis de callback (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`), alternando `this`/`self`. O relatório controla término com contadores `coursesPending--`/`enrPending--` (97, 117, 120) e `res.json(report)` repetido (98, 121); a ordem dos cursos e alunos na resposta depende de qual callback termina primeiro (observado na linha de base: ordem variou entre chamadas).
Impact: Difícil de ler e manter; exceções em callbacks não chegam a nenhum handler; resposta não determinística.
Recommendation: Wrapper Promise sobre sqlite3 e `async/await` (P-14).

### [MEDIUM] Multiple Writes without Transaction (AP-17)
File: src/AppManager.js:50-61, src/AppManager.js:69, src/AppManager.js:133
Description: Checkout insere usuário, matrícula, pagamento e auditoria em comandos separados sem `BEGIN/COMMIT`; se o pagamento falhar, a matrícula fica sem pagamento. `DELETE FROM users` não trata matrículas e pagamentos do usuário (a própria resposta admite: "as matrículas e pagamentos ficaram sujos no banco").
Impact: Dados inconsistentes (matrícula sem pagamento, pagamentos órfãos que aparecem como "Unknown" no relatório).
Recommendation: Envolver o checkout numa transação com rollback e apagar usuário com seus dependentes na mesma transação (P-15).

### [MEDIUM] Scattered and Silent Error Handling (AP-12)
File: src/AppManager.js:38, src/AppManager.js:41, src/AppManager.js:51, src/AppManager.js:55, src/AppManager.js:57, src/AppManager.js:70, src/AppManager.js:84, src/AppManager.js:92, src/AppManager.js:104-106, src/AppManager.js:133-135, src/app.js:1-14
Description: Respostas 500 montadas à mão em 5 lugares; erro de banco na busca do curso vira 404 (38); `err` ignorado na auditoria (57), nas matrículas do relatório (92, onde `enrollments.length` com `undefined` derrubaria o processo), em usuário/pagamento (104-106) e no DELETE (133, sempre responde 200). Não existe middleware de erro `(err, req, res, next)`.
Impact: Falhas silenciosas, respostas inconsistentes e exceções que derrubam o processo.
Recommendation: Erros de domínio tipados (`HttpError`) lançados pelos services e um middleware de erro único em `app.js` (P-10).

### [MEDIUM] Deprecated/Outdated APIs and Vulnerable Dependencies (AP-15)
File: src/AppManager.js:11-136, package.json:8-9, package-lock.json
Description: Todo o acesso a dados usa a API só de callback do `sqlite3` com aninhamento profundo. `npm audit --omit=dev` reporta 13 vulnerabilidades (2 critical, 8 high): `proxy-addr`, `body-parser`, `path-to-regexp`, `qs` (transitivas do express 4.22.1) e `tar`/`node-gyp` (cadeia de build do sqlite3 5.1.7, correção só no sqlite3 6.x, major).
Impact: Código difícil de compor; exposição a CVEs conhecidos.
Recommendation: Wrapper Promise + `async/await` (P-13, P-14); `npm audit fix` para as correções não-breaking e avaliar upgrade de major do sqlite3 separadamente.

### [MEDIUM] Environment Configuration Fixed in Code (AP-10)
File: src/utils.js:6, src/AppManager.js:7
Description: Porta `3000` e banco `':memory:'` são literais. Não há modo debug ligado, por isso a severidade desce de HIGH para MEDIUM.
Impact: Não dá para mudar porta ou banco por ambiente sem editar código.
Recommendation: `PORT` e `DB_PATH` no módulo de config com defaults `3000` e `:memory:` (P-02).

### [LOW] Poorly Named Variables (AP-19)
File: src/AppManager.js:26, src/AppManager.js:29-33, src/utils.js:17
Description: Variáveis `u`, `e`, `p`, `cid`, `cc`, alias `self = this`, função `badCrypto`. Os campos da API (`usr`, `eml`, `pwd`, `c_id`, `card`) também são abreviados, mas fazem parte do contrato público.
Impact: Leitura difícil.
Recommendation: Nomes descritivos internamente (`name`, `email`, `password`, `courseId`, `cardNumber`), mantendo os nomes de campo do contrato na borda (controller) (P-16).

### [LOW] Magic Numbers and Strings (AP-18)
File: src/AppManager.js:37, src/AppManager.js:46, src/AppManager.js:48, src/AppManager.js:68, src/AppManager.js:108, src/utils.js:19-22
Description: Prefixo de aprovação `"4"`, status `"PAID"`/`"DENIED"` repetidos, `active = 1`, senha padrão `"123456"`, `10000`, `substring(0, 2)` e `substring(0, 10)` no hash.
Impact: Regras escondidas e espalhadas.
Recommendation: Constantes nomeadas (`PaymentStatus`, `APPROVED_CARD_PREFIX`) no model/service (P-16).

### [LOW] console.log as Logger (AP-20)
File: src/utils.js:13, src/app.js:13
Description: `console.log('[LOG] Salvando no cache: ...')` e mensagem de boot via `console.log` (o log do cartão em AppManager.js:45 está em AP-04).
Impact: Sem nível nem desligamento por ambiente.
Recommendation: Módulo `logger` com níveis (P-17).

### [LOW] Dead Code and Unused Imports (AP-21)
File: src/AppManager.js:2, src/utils.js:2-3, src/utils.js:5, src/utils.js:9-10, src/utils.js:25
Description: `totalRevenue` é importado em AppManager.js e nunca usado; `dbUser`, `dbPass` e `smtpUser` nunca são lidos; `globalCache` é escrito e nunca lido.
Impact: Ruído e segredos mantidos sem necessidade.
Recommendation: Remover (P-17).

## Deprecated APIs
| Local | API | Equivalente moderno |
|-------|-----|---------------------|
| src/AppManager.js:11-136 | `sqlite3` só de callback, com callbacks aninhados | Wrapper Promise + `async/await` |
| package-lock.json (express 4.22.1 → proxy-addr, body-parser, path-to-regexp, qs) | Versões transitivas com CVE (npm audit: critical/high) | `npm audit fix` (sem breaking) |
| package-lock.json (sqlite3 5.1.7 → node-gyp, tar) | Cadeia de build com CVE (critical) | sqlite3 6.x (major, avaliar à parte) |

Nenhum uso de `var`, `new Buffer(`, `url.parse(`, `fs.exists(`, `crypto.createCipher(`, `body-parser` separado ou `req.param()` encontrado.

## Endpoints mapped (baseline)
| Method | Path | Handler | Baseline status |
|--------|------|---------|-----------------|
| POST | /api/checkout | src/AppManager.js:28 (anônimo em setupRoutes) | 200 `{msg, enrollment_id}` (novo e existente); 400 "Pagamento recusado"; 400 "Bad Request" (campos ausentes / corpo vazio); 404 "Curso não encontrado" |
| GET | /api/admin/financial-report | src/AppManager.js:80 (anônimo em setupRoutes) | 200 `[{course, revenue, students:[{student, paid}]}]` (ordem não determinística) |
| DELETE | /api/users/:id | src/AppManager.js:131 (anônimo em setupRoutes) | 200 texto "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." (também para id inexistente) |

================================
Total: 19 findings
================================
