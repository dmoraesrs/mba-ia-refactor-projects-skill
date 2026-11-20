# task-manager-api

API de Task Manager em Python/Flask (tasks, usuários, categorias e relatórios), organizada em MVC.

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env            # preencha SECRET_KEY e SEED_PASSWORD
.venv/bin/python seed.py        # apaga e popula o banco com dados de exemplo
.venv/bin/python app.py
```

Por padrão a aplicação sobe em `http://127.0.0.1:5000` (no macOS a porta 5000 costuma estar ocupada pelo AirPlay; use `PORT=5055`). O banco SQLite fica em `instance/tasks.db`. O `seed.py` cria os usuários `joao@email.com` (admin), `maria@email.com` (user) e `pedro@email.com` (manager), todos com a senha de `SEED_PASSWORD`, gravada com hash scrypt.

Também funciona com a CLI do Flask: `flask --app app:create_app run`. Nesse modo a CLI procura um `.env` subindo pelos diretórios; prefira exportar as variáveis ou manter o `.env` na raiz do projeto.

## Variáveis de ambiente

Veja `.env.example`.

| Variável | Padrão | Uso |
|----------|--------|-----|
| `SECRET_KEY` | aleatório por processo | Chave do Flask e assinatura dos tokens de login |
| `TOKEN_MAX_AGE` | `28800` (8 h) | Validade do token de login, em segundos |
| `SEED_PASSWORD` | aleatória (exibida no log) | Senha dos usuários de exemplo do `seed.py` |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `FLASK_DEBUG` | `false` | Modo debug (nunca em produção) |
| `LOG_LEVEL` | `INFO` | Nível do log |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI SQLAlchemy do banco |
| `CORS_ORIGINS` | `*` | Origens permitidas, separadas por vírgula |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_SENDER` | vazio / `587` | E-mail de "task atribuída". Sem SMTP configurado, a notificação vai só para o log |

## Autenticação

`POST /login` devolve um `token` assinado. Envie-o como `Authorization: Bearer <token>` nas rotas protegidas:

| Rota | Exige |
|------|-------|
| `DELETE /tasks/<id>` | usuário autenticado |
| `DELETE /users/<id>` | admin |
| `DELETE /categories/<id>` | admin |
| `POST /users` com `role` diferente de `user` | admin |
| `PUT /users/<id>` que altera o `role` | admin |

Sem token, a resposta é `401`. Com token de quem não é admin, onde se exige admin, a resposta é `403`. As demais rotas continuam abertas, como na versão anterior.

## Estrutura

```
app.py                     # composition root: create_app() injeta dependências e registra rotas
seed.py                    # dados de exemplo
src/config/settings.py     # configuração por variável de ambiente
src/database.py            # instância do Flask-SQLAlchemy e criação do schema
src/models/                # entidades, consultas/agregações e serialização (sem senha)
src/services/              # regras de negócio: tasks, usuários, categorias, relatórios, auth, notificação
src/controllers/           # fluxo da requisição e validação de entrada (validators.py)
src/routes/                # camada View: URL + método -> controller
src/middlewares/           # error handler central e autenticação por token
src/constants.py           # status, roles, limites e demais constantes de negócio
src/security.py            # hash de senha (scrypt) e token assinado
```
