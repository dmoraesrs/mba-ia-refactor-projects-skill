# 02: Catálogo de anti-patterns (Fase 2)

Cada anti-pattern tem ID, severidade padrão, sinais de detecção concretos (o que procurar e como) e o padrão do playbook que o corrige. A severidade pode subir um nível quando o problema atinge dado sensível ou rota pública, e pode descer um nível quando o alcance é mínimo; justifique no relatório quando mudar.

## Escala de severidade

| Severidade | Critério |
|------------|----------|
| **CRITICAL** | Falha grave de arquitetura ou segurança que impede o funcionamento correto, expõe dados sensíveis (credencial hardcoded, SQL Injection, senha devolvida na API) ou viola completamente a separação de responsabilidades (God Class com banco, regra de negócio e roteamento juntos) |
| **HIGH** | Violação forte de MVC ou SOLID que dificulta muito manutenção e teste: regra de negócio pesada no controller ou na rota, acoplamento forte sem injeção de dependência, estado global mutável, hash de senha fraco |
| **MEDIUM** | Padronização, duplicação, performance moderada: N+1, validação ausente ou duplicada, tratamento de erro espalhado, middleware inadequado, API deprecated |
| **LOW** | Legibilidade: nomes ruins, magic numbers, imports não usados, `print` como log |

## Resumo do catálogo

| ID | Anti-pattern | Severidade | Playbook |
|----|--------------|------------|----------|
| AP-01 | SQL Injection (query montada com concatenação ou interpolação) | CRITICAL | P-01 |
| AP-02 | Credenciais e segredos hardcoded | CRITICAL | P-02 |
| AP-03 | God Class / God File | CRITICAL | P-03 |
| AP-04 | Exposição de dado sensível em resposta ou log | CRITICAL | P-04 |
| AP-05 | Rota administrativa ou destrutiva sem autenticação | CRITICAL | P-05 |
| AP-06 | Senha sem hash ou com hash fraco | HIGH | P-06 |
| AP-07 | Regra de negócio no controller ou na rota (fat controller) | HIGH | P-07 |
| AP-08 | Acoplamento forte sem injeção de dependência | HIGH | P-08 |
| AP-09 | Estado global mutável | HIGH | P-08 |
| AP-10 | Modo debug ligado e configuração de ambiente fixa no código | HIGH | P-02 |
| AP-11 | Query N+1 | MEDIUM | P-09 |
| AP-12 | Tratamento de erro espalhado, genérico ou silencioso | MEDIUM | P-10 |
| AP-13 | Validação ausente ou duplicada nas rotas | MEDIUM | P-11 |
| AP-14 | Duplicação de código (serialização, regras repetidas) | MEDIUM | P-12 |
| AP-15 | Uso de API deprecated | MEDIUM | P-13 |
| AP-16 | Callback hell / fluxo assíncrono aninhado | MEDIUM | P-14 |
| AP-17 | Operação de várias escritas sem transação | MEDIUM | P-15 |
| AP-18 | Magic numbers e strings soltas | LOW | P-16 |
| AP-19 | Nomes pouco descritivos | LOW | P-16 |
| AP-20 | `print`/`console.log` no lugar de logger | LOW | P-17 |
| AP-21 | Imports e código morto | LOW | P-17 |

---

## AP-01: SQL Injection

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - Python: `execute(` recebendo string com `+`, `%` ou f-string que contém variável. `grep -rnE "execute\(.*(\+|%|f\")" --include=*.py .` e leitura das linhas seguintes (a query costuma quebrar linha).
  - Node: `db.run(`, `db.all(`, `query(` com template literal `${...}` ou `+` dentro da string SQL.
  - Endpoint que executa SQL vindo do cliente (`cursor.execute(dados["sql"])`) é SQL Injection por definição.
- **Não é achado:** query com placeholders (`?`, `%s`, `$1`, `:nome`) e valores passados à parte; ORM com filtros (`filter_by`, `where`).
- **Impacto:** leitura, alteração ou destruição de qualquer dado; bypass de login (`' OR '1'='1`).

## AP-02: Credenciais e segredos hardcoded

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - Atribuições a nomes como `SECRET_KEY`, `password`, `pass`, `senha`, `token`, `api_key`, `apiKey`, `gatewayKey`, `dbPass`, `smtp` com literal string: `grep -rniE "(secret|passw|senha|token|api_?key|gateway|smtp|dbpass)[a-z_]*['\"]?\s*[:=]\s*['\"][^'\"]+['\"]" .`
  - Chaves com prefixos conhecidos: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`.
  - URI de banco com usuário e senha no código.
- **Não é achado:** leitura de variável de ambiente (`os.environ`, `os.getenv`, `process.env`) sem default secreto; placeholders em `.env.example`.
- **Impacto:** quem lê o repositório ganha acesso aos sistemas; rotação exige deploy.

## AP-03: God Class / God File

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - Um arquivo ou classe com três ou mais destas responsabilidades: conexão/criação de schema do banco, SQL, regra de negócio, validação, roteamento HTTP, formatação de resposta, notificação.
  - Classe com nome genérico (`Manager`, `AppManager`, `Utils`, `Helper`) que registra rotas **e** acessa o banco.
  - Arquivo com mais de 300 linhas cobrindo vários domínios (produtos, usuários e pedidos no mesmo módulo).
- **Impacto:** impossível testar em isolamento; qualquer mudança afeta tudo.

## AP-04: Exposição de dado sensível em resposta ou log

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - Serialização que inclui `senha`, `password`, `pass`, `hash` (`to_dict` com `'password'`, `SELECT *` de usuários devolvido direto).
  - Health check ou endpoint de debug devolvendo `secret_key`, `db_path`, flags de debug.
  - Log com número de cartão, senha, token ou chave: `console.log(` / `print(` com `card`, `cc`, `senha`, `key`.
  - Mensagem de erro devolvendo `str(e)` ou stack trace ao cliente (o detalhe interno vai para o log, não para a resposta).
- **Impacto:** vazamento de credenciais e dados pessoais (LGPD), PCI-DSS no caso de cartão.

## AP-05: Rota administrativa ou destrutiva sem autenticação

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - Rotas com `admin`, `reset`, `query`, `debug`, `financial`, `report` ou métodos `DELETE` sem verificação de identidade ou papel antes da ação.
  - Token falso ou previsível (`'fake-jwt-token-' + id`).
- **Impacto:** qualquer cliente apaga o banco, executa SQL arbitrário ou lê dados financeiros.

## AP-06: Senha sem hash ou com hash fraco

- **Severidade:** HIGH (CRITICAL se a senha em texto puro também for devolvida pela API)
- **Sinais de detecção:**
  - Insert de senha recebida direto na tabela; login comparando `senha = '<valor>'` no SQL.
  - `hashlib.md5`, `hashlib.sha1`, `createHash('md5')`, base64 ou função caseira (`badCrypto`) usada como hash de senha.
- **Correção esperada:** `werkzeug.security.generate_password_hash`/`check_password_hash`, `bcrypt`, `argon2`, `crypto.scrypt` com salt.

## AP-07: Regra de negócio no controller ou na rota (fat controller)

- **Severidade:** HIGH
- **Sinais de detecção:**
  - Handler HTTP com cálculo de domínio (total de pedido, desconto, estoque, status de pagamento, taxa de conclusão, "atrasado") em vez de chamar um service ou model.
  - Handler com mais de ~40 linhas ou com laço sobre entidades fazendo cálculo.
  - Efeitos colaterais de negócio (envio de e-mail/SMS, auditoria, cache) disparados dentro do handler.
- **Impacto:** regra não reaproveitável nem testável sem HTTP; duplicação entre rotas.

## AP-08: Acoplamento forte sem injeção de dependência

- **Severidade:** HIGH
- **Sinais de detecção:**
  - Controller ou service instanciando dependência concreta internamente (`new sqlite3.Database(...)` no construtor, `NotificationService()` dentro da função, `smtplib.SMTP(` no meio da regra).
  - Módulos importando a conexão global em vez de recebê-la (`from database import get_db` em todo lugar).
- **Impacto:** impossível substituir por fake em teste; troca de banco exige reescrever tudo.

## AP-09: Estado global mutável

- **Severidade:** HIGH
- **Sinais de detecção:**
  - Variável de módulo alterada em runtime: `global x`, `let cache = {}` exportado e mutado, lista de notificações em atributo de instância singleton, conexão única compartilhada entre threads (`check_same_thread=False`).
- **Impacto:** condições de corrida, vazamento de memória, comportamento que depende da ordem das requisições.

## AP-10: Debug ligado e ambiente fixo no código

- **Severidade:** HIGH
- **Sinais de detecção:** `debug=True`, `DEBUG = True`, `app.run(host="0.0.0.0", debug=True)`, porta, URI de banco e nome de ambiente literais (`"ambiente": "producao"`).
- **Impacto:** console de debug do Werkzeug permite execução remota de código; configuração não muda por ambiente.

## AP-11: Query N+1

- **Severidade:** MEDIUM
- **Sinais de detecção:**
  - Query dentro de laço que percorre o resultado de outra query: `for row in rows:` seguido de `execute(`/`query.get(`/`filter_by(`; `forEach` com `db.get(` dentro.
  - Acesso a relacionamento lazy dentro de laço (`len(u.tasks)` para cada usuário).
  - Várias contagens separadas da mesma tabela (`count()` por status) onde um `GROUP BY` resolveria.
- **Correção esperada:** JOIN, `IN (...)`, eager loading (`joinedload`), `GROUP BY`.

## AP-12: Tratamento de erro espalhado, genérico ou silencioso

- **Severidade:** MEDIUM
- **Sinais de detecção:** `try/except Exception` repetido em cada handler, `except:` sem tipo, `catch` vazio, callback que ignora `err`, resposta 500 montada à mão em vários lugares, ausência de error handler global (`@app.errorhandler`, middleware `(err, req, res, next)`).

## AP-13: Validação ausente ou duplicada nas rotas

- **Severidade:** MEDIUM
- **Sinais de detecção:** campos do corpo usados sem checar tipo ou presença (`dados.get(...)` em `None`, `priority < 1` com string), as mesmas validações copiadas em criar e atualizar, listas de valores válidos repetidas em vários arquivos, `request.get_json()` sem tratar corpo vazio.

## AP-14: Duplicação de código

- **Severidade:** MEDIUM
- **Sinais de detecção:** o mesmo dicionário de serialização montado campo a campo em vários lugares; a mesma regra (por exemplo "está atrasado?") reimplementada em vários handlers; funções quase idênticas (`get_pedidos_usuario` e `get_todos_pedidos`).

## AP-15: Uso de API deprecated

- **Severidade:** MEDIUM (LOW se for só aviso sem data de remoção)
- **Como detectar:** procure cada item da tabela da stack detectada. Recomende sempre o equivalente moderno.

| Stack | API deprecated | Sinal (`grep -rn`) | Equivalente moderno |
|-------|----------------|--------------------|---------------------|
| Python 3.12+ | `datetime.utcnow()` / `datetime.utcfromtimestamp()` | `utcnow\(` | `datetime.now(timezone.utc)` |
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)` (API legada) | `query\.get\(` | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `Model.query.filter(...)` em código novo | `\.query\.` | `db.session.execute(db.select(Model).where(...))` |
| Flask 2.3+ | `@app.before_first_request`, `flask.json.JSONEncoder`, `app.json_encoder` | `before_first_request`, `JSONEncoder` | inicialização no factory, `app.json` provider |
| Python | `hashlib.md5` para senha (inseguro, não usar) | `md5\(` | `werkzeug.security`, `bcrypt` |
| Node.js | `new Buffer(...)` | `new Buffer\(` | `Buffer.from(...)` / `Buffer.alloc(...)` |
| Node.js | `url.parse(`, `fs.exists(`, `crypto.createCipher(` | idem | `new URL()`, `fs.existsSync`/`fs.access`, `crypto.createCipheriv` |
| Express 4 | `body-parser` separado, `req.param()`, `res.send(status, body)`, `res.json(status, obj)` | idem | `express.json()`, `req.params`/`req.query`, `res.status(s).send(b)` |
| Node.js | APIs só de callback onde há versão com Promise (`sqlite3` com callbacks aninhados) | callbacks aninhados | wrapper com Promise e `async/await` |
| JavaScript | `var` | `\bvar\b` | `const`/`let` |
| Dependências | Versão com vulnerabilidade conhecida ou fora de suporte | `npm audit`, `pip-audit` se disponíveis | Atualizar para a versão corrigida |

## AP-16: Callback hell

- **Severidade:** MEDIUM
- **Sinais de detecção:** três ou mais níveis de callback aninhado (`db.get(..., (err, x) => { db.run(..., function(err) { ... }) })`), contadores manuais de pendências (`pending--; if (pending === 0)`).

## AP-17: Várias escritas sem transação

- **Severidade:** MEDIUM
- **Sinais de detecção:** sequência de `INSERT`/`UPDATE` relacionados (pedido, itens e estoque; matrícula e pagamento) sem `BEGIN/COMMIT/ROLLBACK` ou sem `session.commit()` único; `DELETE` de entidade pai sem tratar filhos.

## AP-18: Magic numbers e strings

- **Severidade:** LOW
- **Sinais de detecção:** números de negócio literais (`10000`, `0.1`, `5000`, `0.05`, limites de tamanho `200`, `3`, `4`) e listas de status ou categorias literais no meio da lógica.

## AP-19: Nomes pouco descritivos

- **Severidade:** LOW
- **Sinais de detecção:** variáveis de uma ou duas letras fora de laço curto (`u`, `e`, `p`, `cc`, `cid`), campos de API abreviados (`usr`, `eml`, `pwd`, `c_id`), parâmetro chamado `id` sombreando builtin.

## AP-20: `print`/`console.log` como log

- **Severidade:** LOW
- **Sinais de detecção:** `print(` e `console.log(` em código de aplicação; mensagens simulando efeitos ("ENVIANDO EMAIL").
- **Correção esperada:** logger da stack (`logging`, `pino`/`console` encapsulado num módulo de logger) com nível.

## AP-21: Imports e código morto

- **Severidade:** LOW
- **Sinais de detecção:** imports não usados (`import os, sys, json` sem uso), funções e variáveis exportadas nunca usadas (`totalRevenue`), constantes declaradas e ignoradas, métodos de model que ninguém chama.
