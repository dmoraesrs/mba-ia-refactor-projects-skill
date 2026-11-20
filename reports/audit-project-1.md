================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.12 + Flask 3.1.1 (flask-cors 5.0.1, sqlite3 stdlib)
Files:   4 analyzed | ~780 lines of code
Date:    2026-11-19

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] SQL Injection (AP-01)
File: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-161, models.py:163-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299, app.py:59-69
Description: Todas as queries com parâmetro são montadas por concatenação de string. Os casos mais graves recebem texto livre do cliente: `login_usuario` monta `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"` (models.py:110), `criar_produto`/`atualizar_produto`/`criar_usuario` concatenam `nome`, `descricao`, `email`, `senha` e `categoria`, e `buscar_produtos` concatena `q` e `categoria` da query string em `LIKE '%" + termo + "%'` (models.py:291-293). Além disso, `POST /admin/query` (app.py:59-69) executa `cursor.execute(dados["sql"])` com o SQL enviado no corpo.
Impact: Bypass de login com `' OR '1'='1`, leitura de toda a tabela `usuarios` (senhas em texto puro), alteração ou destruição de qualquer dado por qualquer cliente anônimo.
Recommendation: Trocar todas as queries por placeholders `?` com valores passados à parte, concentradas nos models; remover o endpoint de SQL arbitrário ou restringi-lo a admin autenticado (P-01, P-05).

### [CRITICAL] Rota administrativa ou destrutiva sem autenticação (AP-05)
File: app.py:47-57, app.py:59-78, controllers.py:98-109, controllers.py:237-255
Description: `POST /admin/reset-db` apaga as quatro tabelas e `POST /admin/query` executa SQL arbitrário sem nenhuma verificação de identidade ou papel. `DELETE /produtos/<id>` e `PUT /pedidos/<id>/status` também não exigem autenticação; a aplicação não emite token (o `/login` só devolve os dados do usuário).
Impact: Qualquer cliente na rede apaga o banco inteiro ou executa qualquer comando SQL (confirmado na linha de base: `/admin/query` devolveu 200 com dados e `/admin/reset-db` devolveu 200).
Recommendation: Proteger as rotas `/admin/*` com uma chave administrativa lida de variável de ambiente (header) e desabilitá-las quando a chave não estiver configurada (P-05).

### [CRITICAL] Exposição de dado sensível em resposta (AP-04)
File: models.py:83, models.py:99, controllers.py:285-289
Description: A serialização de usuário em `get_todos_usuarios` e `get_usuario_por_id` inclui o campo `"senha"`, então `GET /usuarios` e `GET /usuarios/<id>` devolvem a senha em texto puro (confirmado na linha de base). O `GET /health` devolve `"secret_key": "minh***"`, `"db_path": "loja.db"`, `"debug": True` e `"ambiente": "producao"`.
Impact: Vazamento de credenciais de todos os usuários (LGPD) e da chave de assinatura da aplicação para qualquer cliente anônimo.
Recommendation: Remover `senha` da serialização pública do model `Usuario` e retirar `secret_key`, `db_path` e `debug` da resposta do health check (P-04).

### [CRITICAL] Senha sem hash (AP-06)
File: models.py:126-129, models.py:109-111, database.py:75-83
Description: `criar_usuario` grava a senha recebida direto na coluna `senha`; `login_usuario` compara a senha em texto puro dentro do SQL; o seed grava `admin@loja.com` com `'admi***'`, `joao@email.com` com `'1234***'` e `maria@email.com` com `'senh***'`. Severidade elevada para CRITICAL porque a senha em texto puro também é devolvida pela API (ver AP-04).
Impact: Qualquer leitura do banco (ou das rotas de usuários) entrega as senhas reais, reaproveitáveis em outros sistemas.
Recommendation: Usar `werkzeug.security.generate_password_hash` no cadastro e no seed e `check_password_hash` no login, buscando o usuário só pelo e-mail (P-06).

### [CRITICAL] Credenciais e segredos hardcoded (AP-02)
File: app.py:7, controllers.py:289, database.py:76-78
Description: `app.config["SECRET_KEY"]` recebe o literal `'minh***'` em app.py:7, e o mesmo literal é repetido na resposta do health check (controllers.py:289). As senhas dos usuários de seed estão literais em database.py:76-78, incluindo a do administrador (`'admi***'`).
Impact: Quem lê o repositório obtém a chave usada para assinar sessões e a senha do admin; rotação exige deploy.
Recommendation: Ler `SECRET_KEY` de variável de ambiente num módulo de config, criar `.env.example` sem valores e parametrizar a senha do admin de seed por variável de ambiente (P-02).

### [CRITICAL] God File / ausência de camadas (AP-03)
File: models.py:1-314, controllers.py:1-292, app.py:1-88, database.py:1-86
Description: `models.py` (314 linhas) cobre produtos, usuários, pedidos e relatórios e mistura SQL, serialização e regra de negócio (validação de estoque e cálculo de total em `criar_pedido`, faixas de desconto em `relatorio_vendas`). `controllers.py` mistura validação, notificações simuladas, formatação de resposta e acesso direto ao banco (`health_check`, controllers.py:266-274). `app.py` junta configuração, roteamento e SQL (rotas admin). `database.py` junta conexão, criação de schema e seed.
Impact: Nenhuma regra pode ser testada sem banco e sem HTTP; qualquer mudança de domínio mexe em arquivos que servem todos os domínios.
Recommendation: Reestruturar em config, models por entidade, services com as regras, controllers finos, routes por recurso e entry point com app factory (P-03).

### [HIGH] Regra de negócio no lugar errado (AP-07)
File: models.py:133-169, models.py:256-262, controllers.py:208-210, controllers.py:247-250, controllers.py:43-54
Description: `criar_pedido` no model valida existência e estoque de produto e calcula o total; `relatorio_vendas` no model aplica faixas de desconto (10%/5%/2%). O handler `criar_pedido` dispara efeitos colaterais de negócio ("ENVIANDO EMAIL", "ENVIANDO SMS", "ENVIANDO PUSH") e `atualizar_status_pedido` decide notificações por status. As regras de produto (preço e estoque não negativos, tamanho do nome, categorias válidas) ficam inline no handler.
Impact: Regras não reaproveitáveis nem testáveis sem HTTP/banco; a camada de dados conhece política comercial.
Recommendation: Extrair `PedidoService`, `RelatorioService` e `ProdutoService` com as regras e um serviço de notificação injetado; models só persistem (P-07).

### [HIGH] Modo debug ligado e ambiente fixo no código (AP-10)
File: app.py:8, app.py:9, app.py:88, database.py:5, controllers.py:286-288
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` expõem o debugger do Werkzeug em todas as interfaces; o caminho do banco (`"loja.db"`), a porta e o nome do ambiente (`"producao"`) são literais; `CORS(app)` libera qualquer origem sem configuração.
Impact: O console de debug do Werkzeug permite execução remota de código; a configuração não muda por ambiente.
Recommendation: Ler DEBUG, HOST, PORT, DATABASE_PATH e origens CORS de variáveis de ambiente num módulo de config, com debug desligado por padrão (P-02).

### [HIGH] Estado global mutável (AP-09)
File: database.py:4, database.py:7-11
Description: `db_connection` é uma variável de módulo inicializada via `global db_connection` e compartilhada por todas as requisições com `sqlite3.connect(db_path, check_same_thread=False)`.
Impact: O servidor de desenvolvimento do Flask atende em threads; cursores e transações de requisições concorrentes se misturam (um `commit()` de uma requisição grava escritas pendentes de outra).
Recommendation: Abrir uma conexão por requisição guardada em `flask.g` e fechá-la no `teardown_appcontext` (P-08).

### [HIGH] Acoplamento forte sem injeção de dependência (AP-08)
File: models.py:1, controllers.py:2-3, controllers.py:266, app.py:3-4, app.py:49, app.py:66
Description: Todas as 15 funções de `models.py` chamam `get_db()` importado do módulo global; os controllers importam o módulo `models` e o `get_db` diretamente; `app.py` usa `get_db()` nas rotas admin. Não existe ponto onde a conexão ou os serviços sejam injetados.
Impact: Impossível substituir o banco por um fake em teste; troca de banco exige reescrever todos os módulos.
Recommendation: App factory como composition root, models recebendo a conexão por função de acesso (`get_db` ligada ao app context) e controllers chamando services (P-08).

### [HIGH] Detalhe interno de erro devolvido ao cliente (AP-04)
File: app.py:78, controllers.py:12, controllers.py:22, controllers.py:62, controllers.py:96, controllers.py:109, controllers.py:126, controllers.py:134, controllers.py:144, controllers.py:165, controllers.py:186, controllers.py:220, controllers.py:227, controllers.py:235, controllers.py:255, controllers.py:262, controllers.py:292, controllers.py:161, controllers.py:179, controllers.py:182
Description: Todos os handlers devolvem `{"erro": str(e)}` com status 500, expondo mensagens do SQLite e exceções Python (por exemplo `'NoneType' object has no attribute 'get'`). E-mails de usuários são impressos no log em cadastro e login (controllers.py:161, 179, 182). Severidade reduzida de CRITICAL para HIGH porque não expõe credencial diretamente, mas facilita explorar o SQL Injection acima.
Impact: Mensagens de erro do banco guiam a exploração de SQL Injection; dado pessoal em log.
Recommendation: Error handler central que registra o detalhe no logger e devolve mensagem genérica; não registrar e-mail em log de nível informativo (P-04, P-10).

### [MEDIUM] Várias escritas sem transação (AP-17)
File: models.py:139-168, models.py:65-70, app.py:51-55
Description: `criar_pedido` lê estoque, insere o pedido, insere cada item e decrementa o estoque sem transação explícita nem rollback: se uma exceção ocorrer no meio (por exemplo item sem `quantidade`), as escritas parciais ficam pendentes na conexão global e são gravadas pelo próximo `commit()` de qualquer requisição. A checagem de estoque (linha 144) e o decremento (linha 163) não são atômicos. `deletar_produto` apaga o produto sem tratar `itens_pedido` que o referenciam.
Impact: Pedidos sem itens, estoque inconsistente e venda acima do estoque sob concorrência.
Recommendation: Envolver o fluxo do pedido numa transação com rollback em erro (`with conn:`) e decremento condicional `WHERE estoque >= ?` (P-15).

### [MEDIUM] Validação ausente ou duplicada (AP-13)
File: controllers.py:28-50, controllers.py:72-90, controllers.py:169-170, controllers.py:195-201, controllers.py:239-245, app.py:61-62
Description: As validações de produto são copiadas entre `criar_produto` e `atualizar_produto`, mas a atualização não verifica tamanho do nome nem categoria. Não há checagem de tipo: `"preco": "abc"` gera `TypeError` e 500. `login`, `atualizar_status_pedido` e `/admin/query` chamam `dados.get` sem tratar corpo vazio (500). Os itens do pedido não são validados: falta de `produto_id`/`quantidade` gera `KeyError` (500) e `quantidade` negativa passa na checagem de estoque, reduz o total e **aumenta** o estoque (`estoque - -5`). `atualizar_status_pedido` responde 200 para pedido inexistente.
Impact: Erros 500 para entradas inválidas e corrupção de dados de negócio (estoque e faturamento).
Recommendation: Centralizar validadores por entidade (produto, usuário, pedido) reutilizados em criar/atualizar, com checagem de tipo e de corpo vazio (P-11).

### [MEDIUM] Query N+1 (AP-11)
File: models.py:177-199, models.py:209-231, models.py:139-140, models.py:154-155, models.py:239-254
Description: `get_pedidos_usuario` e `get_todos_pedidos` fazem 1 query de pedidos, 1 query de itens por pedido e 1 query de produto por item. `criar_pedido` consulta cada produto duas vezes (validação e inserção). `relatorio_vendas` faz cinco consultas separadas na tabela `pedidos` (total, soma e uma contagem por status).
Impact: Número de queries cresce linearmente com pedidos e itens; latência alta em listagens.
Recommendation: JOIN entre `itens_pedido` e `produtos` com `IN (...)` pelos pedidos carregados, reaproveitar os produtos lidos na validação e usar uma agregação com `SUM(CASE ...)`/`GROUP BY` no relatório (P-09).

### [MEDIUM] Tratamento de erro espalhado e genérico (AP-12)
File: app.py:77, controllers.py:10, controllers.py:21, controllers.py:60, controllers.py:95, controllers.py:108, controllers.py:125, controllers.py:133, controllers.py:143, controllers.py:164, controllers.py:185, controllers.py:218, controllers.py:226, controllers.py:234, controllers.py:254, controllers.py:261, controllers.py:291
Description: 17 blocos `try/except Exception` idênticos, um por handler, cada um montando a resposta 500 à mão; não há `@app.errorhandler` registrado.
Impact: Comportamento de erro inconsistente, duplicação e exceções de programação mascaradas como respostas comuns.
Recommendation: Exceções de domínio (`ValidationError`, `NotFoundError`) e error handlers centralizados registrados no app factory (P-10).

### [MEDIUM] Duplicação de código (AP-14)
File: models.py:12-21, models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, models.py:171-201, models.py:203-233
Description: O dicionário de produto é montado campo a campo três vezes; o de usuário, duas vezes; `get_pedidos_usuario` e `get_todos_pedidos` são idênticas exceto pelo `WHERE`.
Impact: Mudar um campo exige editar vários lugares; foi assim que `senha` vazou nas duas serializações de usuário.
Recommendation: Uma função `to_dict` por entidade no model e uma função única de carga de pedidos com filtro opcional (P-12).

### [LOW] `print` no lugar de logger (AP-20)
File: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248, controllers.py:250
Description: 19 chamadas `print(` registram eventos e simulam efeitos ("ENVIANDO EMAIL", "ENVIANDO SMS", "NOTIFICAÇÃO").
Impact: Sem nível, sem formato e sem como desligar por ambiente.
Recommendation: Módulo `logging` configurado no app factory e serviço de notificação que registra pelo logger (P-17).

### [LOW] Magic numbers e strings soltas (AP-18)
File: models.py:257-262, controllers.py:47-50, controllers.py:52, controllers.py:242, models.py:247, models.py:250, models.py:253, app.py:36, controllers.py:285
Description: Faixas de desconto `10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02` literais no relatório; limites de nome `2` e `200`; lista de categorias e de status literais no meio do handler; status `'pendente'`, `'aprovado'`, `'cancelado'` repetidos nas queries; versão `"1.0.0"` repetida.
Impact: Regras comerciais escondidas e listas que divergem entre arquivos.
Recommendation: Constantes nomeadas num módulo de domínio (`CATEGORIAS_VALIDAS`, `STATUS_PEDIDO`, `FAIXAS_DESCONTO`) (P-16).

### [LOW] Nomes pouco descritivos (AP-19)
File: controllers.py:14, controllers.py:56, controllers.py:64, controllers.py:98, controllers.py:136, controllers.py:160, models.py:24, models.py:54, models.py:65, models.py:89, models.py:187, models.py:191, models.py:219, models.py:223
Description: Parâmetros e variáveis chamados `id` sombreiam o builtin; cursores `cursor2`/`cursor3` não dizem o que consultam.
Impact: Legibilidade e risco de bug ao usar o builtin `id`.
Recommendation: Renomear para `produto_id`, `usuario_id` e eliminar os cursores aninhados com a correção do N+1 (P-16).

### [LOW] Imports não usados (AP-21)
File: database.py:2, models.py:2
Description: `import os` em database.py e `import sqlite3` em models.py não são usados.
Impact: Ruído e dependências aparentes que não existem.
Recommendation: Remover os imports mortos (P-17).

## Deprecated APIs
| Local | API | Equivalente moderno |
|-------|-----|---------------------|
| (nenhum) | Nenhuma API deprecated encontrada na stack detectada (busca por `utcnow(`, `query.get(`, `.query.`, `before_first_request`, `JSONEncoder`, `md5(` sem ocorrências). Auditoria de vulnerabilidade das dependências não executada: `pip-audit` não está instalado. | — |

## Endpoints mapped (baseline)
| Method | Path | Handler | Baseline status |
|--------|------|---------|-----------------|
| GET | / | app.py:index (33) | 200 |
| GET | /produtos | controllers.py:listar_produtos (5) | 200 |
| GET | /produtos/busca | controllers.py:buscar_produtos (111) | 200 |
| GET | /produtos/<int:id> | controllers.py:buscar_produto (14) | 200 / 404 |
| POST | /produtos | controllers.py:criar_produto (24) | 201 / 400 |
| PUT | /produtos/<int:id> | controllers.py:atualizar_produto (64) | 200 / 404 / 400 |
| DELETE | /produtos/<int:id> | controllers.py:deletar_produto (98) | 200 / 404 |
| GET | /usuarios | controllers.py:listar_usuarios (128) | 200 |
| GET | /usuarios/<int:id> | controllers.py:buscar_usuario (136) | 200 / 404 |
| POST | /usuarios | controllers.py:criar_usuario (146) | 201 / 400 |
| POST | /login | controllers.py:login (167) | 200 / 401 / 400 |
| POST | /pedidos | controllers.py:criar_pedido (188) | 201 / 400 |
| GET | /pedidos | controllers.py:listar_todos_pedidos (229) | 200 |
| GET | /pedidos/usuario/<int:usuario_id> | controllers.py:listar_pedidos_usuario (222) | 200 |
| PUT | /pedidos/<int:pedido_id>/status | controllers.py:atualizar_status_pedido (237) | 200 / 400 |
| GET | /relatorios/vendas | controllers.py:relatorio_vendas (257) | 200 |
| GET | /health | controllers.py:health_check (264) | 200 |
| POST | /admin/reset-db | app.py:reset_database (48) | 200 |
| POST | /admin/query | app.py:executar_query (60) | 200 / 400 |

================================
Total: 20 findings
================================
