# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, organizada em MVC.

## Como rodar

```bash
npm install
cp .env.example .env   # preencha ADMIN_TOKEN e PAYMENT_GATEWAY_KEY
npm run start:env      # carrega o .env (Node 20.6+)
# ou, exportando as variáveis no shell:
ADMIN_TOKEN=troque-me npm start
```

A aplicação sobe em `http://localhost:3000` (ou na porta de `PORT`). Com `DB_PATH=:memory:` (padrão) o banco é recriado com seed a cada boot.

## Variáveis de ambiente

| Variável | Padrão | Uso |
|----------|--------|-----|
| `PORT` | `3000` | Porta HTTP |
| `DB_PATH` | `:memory:` | Arquivo SQLite; o seed só roda se o banco estiver vazio |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway de pagamento (simulado) |
| `ADMIN_TOKEN` | vazio | Token das rotas administrativas. Sem ele, essas rotas respondem `401` |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn`, `error`, `silent` |

## Endpoints

| Método | Rota | Auth |
|--------|------|------|
| POST | `/api/checkout` | pública |
| GET | `/api/admin/financial-report` | `Authorization: Bearer <ADMIN_TOKEN>` |
| DELETE | `/api/users/:id` | `Authorization: Bearer <ADMIN_TOKEN>` |

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
├── server.js            # entry point: carrega config e sobe o servidor
├── app.js               # composition root: cria dependências e registra rotas
├── config/              # variáveis de ambiente
├── database/            # conexão (wrapper Promise + transações) e schema/seed
├── models/              # acesso a dados (queries parametrizadas)
├── services/            # regras de negócio: checkout, relatório, usuários, gateway, hash
├── controllers/         # fluxo HTTP e validação de entrada
├── routes/              # mapeamento de URL -> controller (camada View)
└── middlewares/         # erro centralizado e autenticação admin
```
