# 04: Diretrizes de arquitetura MVC (Fase 3)

O alvo é um MVC para APIs: a "View" de uma API é a camada de roteamento e apresentação (rotas e serialização da resposta). As regras abaixo valem para qualquer stack; os nomes de diretório se adaptam à convenção da linguagem.

## Camadas e responsabilidades

| Camada | Responsabilidade | Pode | Não pode |
|--------|------------------|------|----------|
| **Config** (`config/`) | Ler e validar variáveis de ambiente; expor configuração tipada | Ter defaults seguros para desenvolvimento (porta, caminho do banco local) | Ter segredo real como default; ler `os.environ`/`process.env` espalhado pelo código |
| **Models** (`models/`) | Representar entidades e encapsular o acesso a dados: queries parametrizadas ou ORM, serialização da entidade (`to_dict`/`toJSON`) sem campos sensíveis | Conhecer o banco | Conhecer HTTP (`request`, `res`), montar resposta HTTP, enviar e-mail |
| **Views / Routes** (`views/` ou `routes/`) | Mapear método + URL para um controller; aplicar middlewares da rota (auth, validação) | Importar controllers | Ter SQL, regra de negócio ou `try/except` de domínio |
| **Controllers** (`controllers/`) | Fluxo da requisição: ler e validar entrada, chamar services/models, escolher status code e montar a resposta | Conhecer HTTP | Ter SQL; ter regra de negócio que vale fora do HTTP |
| **Services** (`services/`, opcional mas recomendado) | Regras de negócio e casos de uso que envolvem mais de um model ou efeito externo (pedido + estoque + notificação, checkout + pagamento) | Usar models e gateways injetados | Conhecer HTTP |
| **Middlewares** (`middlewares/`) | Tratamento de erro centralizado, autenticação, logging de requisição | Converter exceções de domínio em status HTTP | Ter regra de negócio |
| **Entry point / composition root** (`app.py`, `server.js`, `main.ts`) | Criar a app, carregar config, instanciar dependências e injetá-las, registrar rotas e middlewares, subir o servidor | Instanciar classes concretas | Ter rota com lógica, SQL ou regra |

Direção das dependências: `routes -> controllers -> services -> models -> banco`. Nada aponta para cima. `config` pode ser lido pelo entry point e injetado; camadas internas recebem o que precisam por parâmetro ou construtor.

## Estrutura de diretórios alvo

**Python/Flask**

```
<projeto>/
├── app.py                      # entry point: create_app() + app.run com config
├── .env.example
├── requirements.txt
└── src/                        # (ou pacote com o nome do projeto)
    ├── __init__.py
    ├── config/settings.py
    ├── database.py             # conexão/sessão e criação do schema/seed
    ├── models/<entidade>_model.py
    ├── services/<caso_de_uso>_service.py
    ├── controllers/<entidade>_controller.py
    ├── views/routes.py         # ou views/<entidade>_routes.py com Blueprints
    └── middlewares/error_handler.py
```

**Node.js/Express**

```
<projeto>/
├── package.json                # "start": "node src/server.js"
├── .env.example
└── src/
    ├── server.js               # sobe o servidor (listen)
    ├── app.js                  # composition root: cria app, injeta dependências, registra rotas
    ├── config/index.js
    ├── database/connection.js  # conexão, schema e seed; wrapper com Promise
    ├── models/<entidade>Model.js
    ├── services/<casoDeUso>Service.js
    ├── controllers/<entidade>Controller.js
    ├── routes/index.js         # (camada View)
    └── middlewares/errorHandler.js
```

## Regras obrigatórias

1. **Config sem segredo no código.** Segredo vem de variável de ambiente; sem a variável, a app falha com mensagem clara **ou** gera um valor aleatório só para desenvolvimento e registra aviso. Crie `.env.example` sem valores reais.
2. **Debug desligado por padrão**, ligado só por variável de ambiente.
3. **Queries parametrizadas ou ORM** em todo acesso a dados.
4. **Senha com hash forte** (werkzeug/bcrypt/scrypt) e nunca devolvida na resposta.
5. **Um error handler central**: controllers lançam exceções de domínio (`NotFoundError`, `ValidationError`) ou devolvem o erro esperado; o handler converte em resposta com o mesmo formato que a API já usava. Erro inesperado vira 500 com mensagem genérica e o detalhe vai para o log.
6. **Injeção de dependência** no composition root: conexão de banco, services e gateways (e-mail, pagamento) são criados uma vez e passados para quem usa.
7. **Contrato preservado**: mesmas rotas, métodos, status e chaves de resposta. Mudança de contrato só por segurança, documentada.
8. **Sem código morto** e sem os arquivos antigos substituídos.
9. **Logger** no lugar de `print`/`console.log`.
10. **Constantes nomeadas** para valores de negócio (status válidos, limites, faixas de desconto).

## Adaptação ao ponto de partida

| Ponto de partida | O que fazer |
|------------------|-------------|
| **Monolito sem camadas** (rotas, SQL e regra no mesmo arquivo ou classe) | Criar a estrutura completa; quebrar a God Class por responsabilidade e por domínio; mover cada rota para `routes`, cada fluxo para `controllers`, cada query para `models`, cada regra para `services` |
| **Camadas nominais** (arquivos `models.py`/`controllers.py` existem, mas misturados) | Reaproveitar a divisão por domínio, corrigir o conteúdo de cada camada, tirar as rotas do `app.py` para `views/routes`, extrair config e erro central |
| **Parcialmente organizado** (`models/`, `routes/`, `services/`, `utils/` já existem) | Não recriar o que está certo. Criar `controllers/` e mover para lá o fluxo que está nas rotas; mover regras duplicadas para services ou métodos de model; fazer as rotas só roteiem; centralizar config e erro; usar o service existente via injeção; remover utils não usados |
| **Já em MVC** | Corrigir só os achados; não reestruturar por reestruturar |

## Checklist da Fase 3

- [ ] Estrutura de diretórios segue o MVC acima
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models abstraem os dados
- [ ] Views/Routes só roteiam
- [ ] Controllers concentram o fluxo
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem como na linha de base
