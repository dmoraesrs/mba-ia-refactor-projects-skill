# 05: Playbook de refatoração (Fase 3)

Cada padrão corrige um ou mais anti-patterns do catálogo (`AP-xx`) e traz código antes/depois. Os exemplos mostram Python/Flask e Node.js/Express; para outra stack, aplique a mesma transformação com o idioma dela.

| Padrão | Corrige |
|--------|---------|
| P-01 Query parametrizada | AP-01 |
| P-02 Config por variável de ambiente | AP-02, AP-10 |
| P-03 Quebrar God Class em camadas | AP-03 |
| P-04 Serialização segura e erro sem detalhe interno | AP-04 |
| P-05 Proteger rota administrativa | AP-05 |
| P-06 Hash de senha forte | AP-06 |
| P-07 Extrair regra de negócio para service | AP-07 |
| P-08 Injeção de dependência no composition root | AP-08, AP-09 |
| P-09 Eliminar N+1 | AP-11 |
| P-10 Error handler centralizado | AP-12 |
| P-11 Validação centralizada | AP-13 |
| P-12 Serialização e regra num lugar só | AP-14 |
| P-13 Trocar API deprecated | AP-15 |
| P-14 Callbacks para async/await | AP-16 |
| P-15 Transação em escrita múltipla | AP-17 |
| P-16 Constantes e nomes descritivos | AP-18, AP-19 |
| P-17 Logger e limpeza de código morto | AP-20, AP-21 |

---

## P-01: Query parametrizada (AP-01)

**Antes (Python)**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```

**Depois**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))  # senha conferida por hash (P-06)
clauses.append("(nome LIKE ? OR descricao LIKE ?)")
params.extend([f"%{termo}%", f"%{termo}%"])
cursor.execute("SELECT * FROM produtos WHERE " + " AND ".join(clauses), params)  # só placeholders entram na string
```

**Antes (Node)**
```js
db.all(`SELECT * FROM users WHERE email = '${email}'`, cb);
```
**Depois**
```js
db.all("SELECT * FROM users WHERE email = ?", [email], cb);
```

Endpoint que executa SQL enviado pelo cliente (`/admin/query`) não tem conserto por parametrização: remova a rota ou restrinja a consultas pré-definidas atrás de autenticação (P-05).

## P-02: Config por variável de ambiente (AP-02, AP-10)

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Depois (`src/config/settings.py`)**
```python
import os
import secrets
from dataclasses import dataclass


def _bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_path: str


def load_settings() -> Settings:
    return Settings(
        secret_key=os.environ.get("SECRET_KEY") or secrets.token_hex(32),  # aleatório só em dev
        debug=_bool(os.environ.get("FLASK_DEBUG")),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        database_path=os.environ.get("DATABASE_PATH", "loja.db"),
    )
```

**Antes (Node)**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```
**Depois (`src/config/index.js`)**
```js
const config = Object.freeze({
  port: Number(process.env.PORT || 3000),
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "",
  dbPath: process.env.DB_PATH || ":memory:",
});
module.exports = config;
```
Acompanhe com `.env.example` listando as variáveis sem valor real.

## P-03: Quebrar God Class em camadas (AP-03)

**Antes (Node: uma classe cria o banco, registra rotas e faz o checkout)**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE ... INSERT seed ... */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* 50 linhas de SQL e regra */ });
  }
}
```

**Depois**
```js
// src/database/connection.js   -> abre conexão, cria schema, seed
// src/models/courseModel.js    -> findActiveById(id)
// src/services/checkoutService.js -> checkout({ name, email, password, courseId, card })
// src/controllers/checkoutController.js
const createCheckoutController = ({ checkoutService }) => ({
  async checkout(req, res) {
    const result = await checkoutService.checkout(parseCheckoutInput(req.body));
    res.status(200).json({ msg: "Sucesso", enrollment_id: result.enrollmentId });
  },
});
// src/routes/index.js
router.post("/api/checkout", asyncHandler(checkoutController.checkout));
```

**Antes (Python: `models.py` com produtos, usuários, pedidos e relatório)**
```python
# models.py (314 linhas, 4 domínios)
def get_todos_produtos(): ...
def login_usuario(email, senha): ...
def criar_pedido(usuario_id, itens): ...
def relatorio_vendas(): ...
```
**Depois**
```
src/models/produto_model.py   src/models/usuario_model.py   src/models/pedido_model.py
src/services/pedido_service.py   src/services/relatorio_service.py
```

## P-04: Serialização segura e erro sem detalhe interno (AP-04)

**Antes**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}

return jsonify({..., "secret_key": "minha-chave-super-secreta-123"})
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```

**Depois**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email}  # sem senha/hash

return jsonify({"status": "ok", "database": "connected", "counts": counts})
# erro inesperado: handler central loga o detalhe e responde mensagem genérica (P-10)
```

**Antes (Node)**
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**Depois**
```js
logger.info("Processando pagamento", { cardLast4: card.slice(-4) });
```

## P-05: Proteger rota administrativa (AP-05)

**Antes**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    ...  # apaga tudo sem checar quem chamou
```

**Depois**
```python
# middlewares/auth.py
def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config["ADMIN_TOKEN"]
        if not expected or not hmac.compare_digest(request.headers.get("X-Admin-Token", ""), expected):
            raise ForbiddenError("Acesso administrativo negado")
        return view(*args, **kwargs)
    return wrapper

admin_bp.add_url_rule("/admin/reset-db", view_func=require_admin_token(admin_controller.reset), methods=["POST"])
```
Node: middleware `requireAdmin(req, res, next)` lendo `process.env.ADMIN_TOKEN` e comparando com `crypto.timingSafeEqual`. A rota continua existindo (contrato), mas exige credencial: registre como mudança de contrato por segurança.

## P-06: Hash de senha forte (AP-06)

**Antes**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```js
function badCrypto(pwd) { /* base64 repetido */ }
```

**Depois**
```python
from werkzeug.security import check_password_hash, generate_password_hash

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    return check_password_hash(self.password, raw)
```
```js
const crypto = require("crypto");
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString("hex");
  return `${salt}:${crypto.scryptSync(password, salt, 64).toString("hex")}`;
}
```
Atualize o seed para gravar senhas já com hash, assim o login dos usuários de exemplo continua funcionando.

## P-07: Extrair regra de negócio para service (AP-07)

**Antes (cálculo de desconto e notificação no fluxo HTTP/modelo)**
```python
def criar_pedido():
    ...
    resultado = models.criar_pedido(usuario_id, itens)
    print("ENVIANDO EMAIL: Pedido ...")
    print("ENVIANDO SMS: ...")
```

**Depois**
```python
# services/pedido_service.py
class PedidoService:
    def __init__(self, pedido_model, produto_model, notifier):
        self._pedidos, self._produtos, self._notifier = pedido_model, produto_model, notifier

    def criar(self, usuario_id, itens):
        total = self._calcular_total(itens)          # valida estoque e soma
        pedido_id = self._pedidos.criar(usuario_id, itens, total)
        self._notifier.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

# controllers/pedido_controller.py
def criar(self):
    dados = require_json()
    resultado = self._service.criar(dados["usuario_id"], dados["itens"])
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201
```

## P-08: Injeção de dependência no composition root (AP-08, AP-09)

**Antes**
```python
db_connection = None  # global mutável
def get_db():
    global db_connection
    ...
```
```python
class TaskController:
    def notify(self):
        NotificationService().notify_task_assigned(...)  # instancia dentro
```

**Depois**
```python
# app.py (composition root)
def create_app(settings=None):
    settings = settings or load_settings()
    app = Flask(__name__)
    database = Database(settings.database_path)       # criado uma vez
    produto_model = ProdutoModel(database)
    pedido_service = PedidoService(PedidoModel(database), produto_model, LogNotifier())
    app.register_blueprint(build_routes(ProdutoController(produto_model), PedidoController(pedido_service)))
    register_error_handlers(app)
    return app
```
Para conexão SQLite por requisição em Flask, use `flask.g` + `teardown_appcontext` em vez de conexão global compartilhada entre threads.

## P-09: Eliminar N+1 (AP-11)

**Antes**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**Depois**
```python
rows = db.execute(
    """SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
       FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
       WHERE i.pedido_id IN (%s)""" % ",".join("?" * len(ids)),
    ids,
).fetchall()
```
```python
# SQLAlchemy: eager loading e GROUP BY
tasks = db.session.execute(db.select(Task).options(joinedload(Task.user), joinedload(Task.category))).scalars().all()
counts = dict(db.session.execute(db.select(Task.status, func.count()).group_by(Task.status)).all())
```

## P-10: Error handler centralizado (AP-12)

**Antes**
```python
def listar_produtos():
    try:
        ...
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Depois (Flask)**
```python
# middlewares/error_handler.py
class AppError(Exception):
    status_code = 400
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code or self.status_code

class NotFoundError(AppError):
    status_code = 404

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"erro": error.message, "sucesso": False}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        app.logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno"}), 500
```

**Depois (Express)**
```js
// middlewares/errorHandler.js
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
function errorHandler(err, req, res, next) {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  logger.error("Erro não tratado", { error: err.message });
  res.status(500).send("Erro interno");
}
app.use(errorHandler); // registrado por último no composition root
```
Preserve o formato de erro que a API já usava (JSON com `erro`/`error`, ou texto puro).

## P-11: Validação centralizada (AP-13)

**Antes (mesmas checagens em criar e atualizar)**
```python
if "nome" not in dados: return jsonify({"erro": "Nome é obrigatório"}), 400
if preco < 0: return jsonify({"erro": "Preço não pode ser negativo"}), 400
```

**Depois**
```python
# controllers/validators.py
def validar_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo, mensagem in (("nome", "Nome é obrigatório"), ("preco", "Preço é obrigatório"), ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidationError(mensagem)
    if not isinstance(dados["preco"], (int, float)) or dados["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
    ...
```
Mantenha as mesmas mensagens de erro do código original para não mudar o contrato.

## P-12: Serialização e regra num lugar só (AP-14)

**Antes (o mesmo dicionário em 5 rotas, regra "atrasada" repetida)**
```python
task_data['due_date'] = str(t.due_date) if t.due_date else None
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
```

**Depois**
```python
class Task(db.Model):
    def is_overdue(self, now=None):
        now = now or utcnow_naive()
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    def to_dict(self, include_overdue=False):
        data = {...}
        if include_overdue:
            data["overdue"] = self.is_overdue()
        return data
```

## P-13: Trocar API deprecated (AP-15)

**Antes**
```python
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
task = Task.query.get(task_id)
```
**Depois**
```python
from datetime import datetime, timezone

def utcnow_naive():
    """UTC sem tzinfo, compatível com colunas DateTime naive já gravadas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utcnow_naive)
task = db.session.get(Task, task_id)
```

**Antes (Node)**
```js
const b = new Buffer(pwd);
```
**Depois**
```js
const b = Buffer.from(pwd);
```

## P-14: Callbacks para async/await (AP-16)

**Antes**
```js
this.db.get(sqlCourse, [cid], (err, course) => {
  this.db.get(sqlUser, [e], (err, user) => {
    this.db.run(sqlEnroll, [userId, cid], function (err) {
      self.db.run(sqlPay, [this.lastID, course.price], (err) => { res.json(...) });
    });
  });
});
```

**Depois**
```js
// database/connection.js
const get = (sql, params = []) => new Promise((resolve, reject) =>
  db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
const run = (sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));

// services/checkoutService.js
async checkout(input) {
  const course = await courses.findActiveById(input.courseId);
  if (!course) throw new NotFoundError("Curso não encontrado");
  const userId = await users.findOrCreate(input);
  const enrollmentId = await enrollments.create(userId, course.id);
  await payments.create(enrollmentId, course.price, "PAID");
  return { enrollmentId };
}
```
Relatórios com contadores manuais (`pending--`) viram uma query com JOIN (P-09) ou `Promise.all`.

## P-15: Transação em escrita múltipla (AP-17)

**Antes**
```python
cursor.execute("INSERT INTO pedidos ...")
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()  # falha no meio deixa estado parcial na conexão compartilhada
```
**Depois**
```python
with connection:  # sqlite3: commit no sucesso, rollback em exceção
    pedido_id = connection.execute("INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)", (...)).lastrowid
    connection.executemany("INSERT INTO itens_pedido (...) VALUES (?, ?, ?, ?)", linhas)
    connection.executemany("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", baixas)
```
```js
await run("BEGIN");
try { /* inserts */ await run("COMMIT"); } catch (err) { await run("ROLLBACK"); throw err; }
```
Exclusão de entidade pai: apague ou trate os filhos na mesma transação.

## P-16: Constantes e nomes descritivos (AP-18, AP-19)

**Antes**
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
```
```js
let u = req.body.usr; let cc = req.body.card;
```
**Depois**
```python
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))  # (faturamento mínimo, percentual)

def calcular_desconto(faturamento):
    return next((faturamento * taxa for minimo, taxa in FAIXAS_DESCONTO if faturamento > minimo), 0)
```
```js
const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body; // contrato externo mantido
```

## P-17: Logger e limpeza de código morto (AP-20, AP-21)

**Antes**
```python
import os, sys, json, datetime
print("Produto criado com ID: " + str(id))
```
**Depois**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Produto criado", extra={"produto_id": produto_id})
```
Remova imports não usados, funções e exports sem chamador (`totalRevenue`, `globalCache` exportado) e utilitários duplicados por constantes já existentes.
