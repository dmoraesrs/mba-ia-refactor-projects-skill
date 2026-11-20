# code-smells-project

API de E-commerce em Python/Flask (produtos, usuários, pedidos e relatório de vendas), organizada em MVC.

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

export ADMIN_TOKEN='<um-token-forte>'            # habilita as rotas /admin/*
export SEED_ADMIN_PASSWORD='<senha-do-admin>'     # senhas dos usuários de exemplo
export SEED_CUSTOMER_PASSWORD='<senha-dos-clientes>'
.venv/bin/python app.py
```

Por padrão a aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado no primeiro boot com produtos e usuários de exemplo (`admin@loja.com`, `joao@email.com`, `maria@email.com`); as senhas vêm das variáveis de seed e são gravadas com hash. Se o banco já tiver senhas antigas em texto puro, elas são convertidas para hash no boot.

Também funciona com a CLI do Flask: `flask --app app:create_app run`.

## Variáveis de ambiente

Veja `.env.example`.

| Variável | Padrão | Uso |
|----------|--------|-----|
| `SECRET_KEY` | aleatório por processo | Chave do Flask |
| `ADMIN_TOKEN` | vazio (rotas admin bloqueadas) | Valor exigido no header `X-Admin-Token` em `/admin/*` |
| `SEED_ADMIN_PASSWORD` / `SEED_CUSTOMER_PASSWORD` | aleatório | Senhas dos usuários de exemplo no primeiro boot |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `FLASK_DEBUG` | `false` | Modo debug (nunca em produção) |
| `APP_ENV` | `producao` | Nome do ambiente exibido no `/health` |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |
| `CORS_ORIGINS` | `*` | Origens permitidas, separadas por vírgula |
| `LOG_LEVEL` | `INFO` | Nível do log |

## Estrutura

```
app.py                  # composition root: create_app() injeta dependências e registra rotas
src/config/settings.py  # configuração por variável de ambiente
src/database.py         # conexão SQLite por requisição, schema, seed
src/models/             # acesso a dados (queries parametrizadas) e serialização
src/services/           # regras de negócio: pedido, relatório, usuário, notificação
src/controllers/        # fluxo da requisição e validação de entrada
src/views/routes.py     # mapeamento URL + método -> controller
src/middlewares/        # error handler central e proteção das rotas admin
```

## Rotas administrativas

`POST /admin/reset-db` e `POST /admin/query` exigem o header `X-Admin-Token: $ADMIN_TOKEN`. O `/admin/query` aceita apenas `SELECT` e roda numa conexão somente leitura.
