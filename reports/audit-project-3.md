================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.1.9)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-11-19

## Summary
CRITICAL: 3 | HIGH: 5 | MEDIUM: 5 | LOW: 4

> Errata (início da Fase 3): o achado AP-17 "DELETE /categories deixa tasks órfãs" (routes/report_routes.py:211-223) foi retirado. Um teste no código original mostrou que o SQLAlchemy carrega `category.tasks` via backref e grava `category_id = NULL` no mesmo commit. A refatoração mantém esse comportamento e o torna explícito no service.

## Findings

### [CRITICAL] Exposição de dado sensível em resposta (AP-04)
File: models/user.py:16-25, routes/user_routes.py:33, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:209
Description: `User.to_dict()` inclui `'password': self.password` (models/user.py:21). Esse dicionário é devolvido em GET /users/<id>, POST /users, PUT /users/<id> e no campo `user` de POST /login. A linha de base confirma a chave `password` nas quatro respostas.
Impact: Qualquer cliente obtém o hash MD5 sem salt de qualquer usuário, que é revertido trivialmente por rainbow table (as senhas do seed têm 4 caracteres). Vazamento de credencial e de dado pessoal (LGPD).
Recommendation: Remover `password` da serialização do model e manter um único `to_dict` seguro (P-04).

### [CRITICAL] Credenciais e segredos hardcoded (AP-02)
File: app.py:13, services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'supe***'` literal no código. `NotificationService.__init__` fixa `email_user = 'task***'` e `email_password = 'senh***'` do SMTP do Gmail.
Impact: Quem lê o repositório ganha a chave de assinatura de sessão e a credencial do e-mail. Rotacionar exige deploy.
Recommendation: Criar módulo de config lendo `SECRET_KEY`, `DATABASE_URL` e `SMTP_*` de variáveis de ambiente, com `.env.example` sem valores reais (P-02).

### [CRITICAL] Rotas destrutivas sem autenticação e token falso (AP-05)
File: routes/user_routes.py:134-151, routes/task_routes.py:225-238, routes/report_routes.py:211-223, routes/user_routes.py:52, routes/user_routes.py:71, routes/user_routes.py:119-122, routes/user_routes.py:210
Description: DELETE /users/<id> (que apaga também todas as tasks do usuário), DELETE /tasks/<id> e DELETE /categories/<id> não verificam identidade nem papel. POST /users e PUT /users/<id> aceitam `role: 'admin'` de um cliente anônimo. POST /login devolve `'fake-jwt-token-' + str(user.id)`, um token previsível que nenhuma rota valida.
Impact: Qualquer cliente apaga usuários e dados em cascata ou se promove a admin. O "token" não autentica nada e pode ser forjado para qualquer id.
Recommendation: Emitir token assinado no login e exigir autenticação (e papel admin para DELETE /users e para mudança de role) via decorator nas rotas destrutivas (P-05).

### [HIGH] Hash de senha fraco (AP-06)
File: models/user.py:29, models/user.py:32, routes/user_routes.py:64, routes/user_routes.py:115
Description: `set_password` e `check_password` usam `hashlib.md5(pwd.encode()).hexdigest()`, sem salt. A senha mínima é de 4 caracteres.
Impact: Somado ao AP-04, o hash exposto é revertido em segundos. Mesmo sem a exposição, um vazamento do banco revela todas as senhas.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash`, com suporte de leitura ao hash MD5 legado para não quebrar o login dos usuários já cadastrados (P-06).

### [HIGH] Debug ligado e ambiente fixo no código (AP-10)
File: app.py:9-16, app.py:11, app.py:15, app.py:30-31, app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` expõe o debugger do Werkzeug na rede. A URI `sqlite:///tasks.db` é literal. `CORS(app)` libera todas as origens. A app é criada no import do módulo (sem factory) e `db.create_all()` roda como efeito colateral do import.
Impact: Execução remota de código pelo console de debug. A configuração não muda por ambiente. O import de `app` (feito pelo seed.py) já toca o banco, e testar com outro banco é impossível.
Recommendation: Usar application factory `create_app(config)` com debug, host, porta, URI e origens CORS vindos da config por ambiente (P-02).

### [HIGH] Regra de negócio nas rotas (fat controller) (AP-07)
File: routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:273-299, routes/report_routes.py:12-101, routes/report_routes.py:103-155, routes/user_routes.py:134-151
Description: Os handlers calculam regras de domínio: "task atrasada" (overdue), taxa de conclusão, contagem por status e prioridade, dias de atraso, produtividade por usuário e exclusão em cascata das tasks do usuário. `summary_report` tem 90 linhas e `create_task` tem 70 linhas de validação e montagem.
Impact: As regras não são reaproveitáveis nem testáveis sem HTTP e já divergem entre rotas (ver AP-14).
Recommendation: Extrair TaskService e ReportService, com controllers que só orquestram e regras como `is_overdue` no model (P-07).

### [HIGH] Arquivos de rota acumulando responsabilidades (God File) (AP-03)
File: routes/task_routes.py:1-299, routes/report_routes.py:157-223
Description: `task_routes.py` (299 linhas) concentra roteamento, validação, regra de negócio, serialização campo a campo e persistência (`db.session.add/commit`). `report_routes.py` mistura dois domínios: relatórios e o CRUD completo de categorias no blueprint `reports`. A severidade foi rebaixada de CRITICAL para HIGH porque cada arquivo fica restrito a um blueprint e o acesso a dados passa pelo ORM, sem criação de schema nem SQL cru.
Impact: Mudar uma regra de categoria obriga a editar o módulo de relatórios. Nada é testável em isolamento.
Recommendation: Separar em routes, controllers, services e models por domínio (tasks, users, categories, reports) (P-03).

### [HIGH] Acoplamento forte sem injeção de dependência (AP-08)
File: routes/task_routes.py:2-5, routes/user_routes.py:2-4, routes/report_routes.py:2-5, services/notification_service.py:5-10, services/notification_service.py:15
Description: As rotas importam o `db` global e os models e chamam `db.session` diretamente. Não existe camada de serviço intermediária. `NotificationService` monta a configuração SMTP no construtor e instancia `smtplib.SMTP(...)` dentro de `send_email`.
Impact: Não dá para trocar o banco nem o transporte de e-mail por fakes em teste. A regra fica presa ao Flask-SQLAlchemy.
Recommendation: Controllers recebem services e services recebem dependências (sessão, notificador) montadas no composition root. O SMTP recebe a config injetada (P-08).

### [MEDIUM] Query N+1 e contagens redundantes (AP-11)
File: routes/task_routes.py:41-57, routes/user_routes.py:22, routes/report_routes.py:53-56, routes/report_routes.py:159-163, routes/report_routes.py:15-28, routes/task_routes.py:275-281
Description: GET /tasks faz `User.query.get` e `Category.query.get` para cada task (2N+1 queries). GET /users acessa o relacionamento lazy `len(u.tasks)` por usuário. `summary_report` faz uma query de tasks por usuário e 12 `count()` separados por status e prioridade. GET /categories faz um `count()` por categoria. `task_stats` faz 5 counts e mais um `all()`.
Impact: O número de queries cresce linearmente com os dados, e os endpoints de listagem e relatório degradam.
Recommendation: Usar eager loading (`joinedload`/`selectinload`) e agregações com `GROUP BY` (`func.count` agrupado por status, prioridade, user_id e category_id) (P-09).

### [MEDIUM] Tratamento de erro espalhado e genérico (AP-12)
File: routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:151, routes/task_routes.py:204, routes/task_routes.py:221, routes/task_routes.py:236, routes/user_routes.py:87, routes/user_routes.py:130, routes/user_routes.py:149, routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, utils/helpers.py:46, utils/helpers.py:49, utils/helpers.py:88, services/notification_service.py:23
Description: Há 16 blocos `try/except`, a maioria `except:` sem tipo, cada um montando a própria resposta 500. GET /tasks embrulha o handler inteiro num `except:` que engole qualquer erro. Não existe `@app.errorhandler`: exceções não tratadas (ver AP-13) viram a página HTML 500 do Werkzeug, fora do formato JSON da API.
Impact: Bugs ficam silenciosos, as respostas de erro são inconsistentes e a mesma lógica de rollback se repete 9 vezes.
Recommendation: Criar exceções de domínio (NotFound, ValidationError, Conflict) e error handlers globais que fazem rollback e devolvem `{'error': ...}` (P-10).

### [MEDIUM] Validação ausente e duplicada (AP-13)
File: routes/task_routes.py:92-100, routes/task_routes.py:113, routes/task_routes.py:182, routes/task_routes.py:261, routes/task_routes.py:264, routes/user_routes.py:115, routes/report_routes.py:196-197, routes/task_routes.py:110, routes/task_routes.py:177, utils/helpers.py:75, models/task.py:39, routes/user_routes.py:61, routes/user_routes.py:106, utils/helpers.py:21, routes/user_routes.py:71, routes/user_routes.py:120
Description: Não há checagem de tipo: `priority < 1` com `"2"` (string) e `len(title)` com número lançam TypeError (500). `int(request.args['priority'])` em /tasks/search lança ValueError (500). PUT /categories sem corpo faz `'name' in None` (500). PUT /categories e PUT /users aceitam `name`/`color`/`active` sem validar. As listas de status, roles e o regex de e-mail estão copiados entre create/update e `utils/helpers.py`. `process_task_data` existe, mas nunca é usada.
Impact: Entradas malformadas derrubam a requisição com 500 em HTML, e as regras divergem entre criar e atualizar.
Recommendation: Centralizar a validação num módulo de validators por entidade, usado por create e update, com constantes únicas (P-11).

### [MEDIUM] Duplicação de serialização e de regras (AP-14)
File: routes/task_routes.py:17-28, routes/user_routes.py:15-23, routes/user_routes.py:162-169, routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-37, routes/report_routes.py:132-135, models/task.py:50-60, routes/task_routes.py:296, routes/report_routes.py:67, routes/report_routes.py:151
Description: O dicionário da task é remontado campo a campo em GET /tasks e em GET /users/<id>/tasks, em vez de usar `Task.to_dict`. A regra "atrasada" (due_date no passado e status diferente de done/cancelled) aparece 6 vezes, enquanto `Task.is_overdue()` existe e não é chamado. A taxa de conclusão `round(done/total*100, 2)` aparece 3 vezes.
Impact: Mudar a regra ou um campo exige editar vários lugares, com risco de divergência.
Recommendation: Concentrar a serialização no model (com variantes explícitas) e a regra em `Task.is_overdue` e num helper de percentual (P-12).

### [MEDIUM] Uso de API deprecated (AP-15)
File: routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:227, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, routes/report_routes.py:105, routes/report_routes.py:192, routes/report_routes.py:213, models/task.py:15-16, models/task.py:52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, routes/task_routes.py:72, routes/task_routes.py:215, routes/task_routes.py:285, routes/user_routes.py:172, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:133, utils/helpers.py:38, services/notification_service.py:35, seed.py:66-74
Description: `Model.query.get(id)` emite `LegacyAPIWarning` no SQLAlchemy 2.x, e `datetime.utcnow()` emite `DeprecationWarning` no Python 3.12. Os dois avisos foram confirmados em runtime na linha de base.
Impact: Os avisos poluem o log, e as APIs estão marcadas para remoção futura.
Recommendation: Trocar por `db.session.get(Model, id)` e por um helper `utcnow()` baseado em `datetime.now(timezone.utc)` (sem tzinfo, para manter o formato serializado) (P-13).

### [LOW] Magic numbers e strings soltas (AP-18)
File: routes/task_routes.py:96, routes/task_routes.py:99, routes/task_routes.py:113, routes/task_routes.py:167-169, routes/task_routes.py:182, routes/user_routes.py:64, routes/user_routes.py:115, routes/report_routes.py:45, routes/report_routes.py:129, routes/report_routes.py:180
Description: Os limites 3/200 do título, a faixa de prioridade 1..5, a senha mínima 4, a janela de 7 dias, "alta prioridade" `<= 2` e a cor `'#000000'` aparecem como literais. As constantes de `utils/helpers.py:110-116` existem, mas não são usadas.
Impact: Mudar uma regra exige caçar os literais pelo código.
Recommendation: Criar um módulo de constantes único, usado por validators e services (P-16).

### [LOW] Nomes pouco descritivos (AP-19)
File: routes/report_routes.py:24-28, models/category.py:14, models/user.py:27, models/task.py:45, routes/user_routes.py:13, routes/task_routes.py:16
Description: Os nomes `p1..p5`, `d`, `pwd`, `p`, `u` e `t` são usados fora de laços curtos.
Impact: Prejudicam a leitura.
Recommendation: Renomear para nomes de domínio (P-16).

### [LOW] `print` no lugar de logger (AP-20)
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39, utils/helpers.py:41
Description: Eventos e erros são registrados com `print`. O `str(e)` vai para o stdout sem nível nem contexto. Os `print` de `seed.py` são saída de um script de CLI e não entram no achado.
Impact: Sem nível, sem formatação e sem como filtrar ou enviar o log para um coletor.
Recommendation: Usar `logging` configurado no composition root (P-17).

### [LOW] Imports e código morto (AP-21)
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:3-7, utils/helpers.py:9-116, services/notification_service.py:1-48, models/task.py:38-48, models/user.py:34-38, requirements.txt:4-6
Description: Imports sem uso: `os, sys, json` em app.py, `json, os, sys, time` em task_routes.py, `hashlib, json` em user_routes.py, `json, format_date, calculate_percentage` em report_routes.py e `json` em models/task.py. Nenhuma função de `utils/helpers.py` é chamada. `NotificationService` nunca é importado. `Task.validate_status`, `Task.validate_priority` e `User.is_admin` não têm chamadas. `marshmallow`, `requests` e `python-dotenv` estão no requirements sem uso.
Impact: Ruído, falsa impressão de que existe validação e serviço de notificação, e dependências inúteis.
Recommendation: Remover o que não é usado e reaproveitar o que faz sentido (validações, `is_overdue`) na camada correta (P-17).

## Deprecated APIs
| Local | API | Equivalente moderno |
|-------|-----|---------------------|
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 | `Model.query.get(id)` (LegacyAPIWarning, SQLAlchemy 2.x) | `db.session.get(Model, id)` |
| models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; utils/helpers.py:38; services/notification_service.py:35; seed.py:66, 67, 69, 70, 74 | `datetime.utcnow()` (DeprecationWarning, Python 3.12) | `datetime.now(timezone.utc)` |
| models/user.py:29, 32 | `hashlib.md5` para senha (inseguro) | `werkzeug.security.generate_password_hash` / `check_password_hash` |

## Endpoints mapped (baseline)
| Method | Path | Handler | Baseline status |
|--------|------|---------|-----------------|
| GET | / | app.py:index | 200 |
| GET | /health | app.py:health | 200 |
| GET | /tasks | routes/task_routes.py:get_tasks | 200 |
| GET | /tasks/<id> | routes/task_routes.py:get_task | 200, 404 |
| POST | /tasks | routes/task_routes.py:create_task | 201, 400, 404 |
| PUT | /tasks/<id> | routes/task_routes.py:update_task | 200, 400, 404 |
| DELETE | /tasks/<id> | routes/task_routes.py:delete_task | 200, 404 |
| GET | /tasks/search | routes/task_routes.py:search_tasks | 200 |
| GET | /tasks/stats | routes/task_routes.py:task_stats | 200 |
| GET | /users | routes/user_routes.py:get_users | 200 |
| GET | /users/<id> | routes/user_routes.py:get_user | 200, 404 |
| POST | /users | routes/user_routes.py:create_user | 201, 400, 409 |
| PUT | /users/<id> | routes/user_routes.py:update_user | 200, 400, 404, 409 |
| DELETE | /users/<id> | routes/user_routes.py:delete_user | 200, 404 |
| GET | /users/<id>/tasks | routes/user_routes.py:get_user_tasks | 200, 404 |
| POST | /login | routes/user_routes.py:login | 200, 400, 401, 403 |
| GET | /reports/summary | routes/report_routes.py:summary_report | 200 |
| GET | /reports/user/<id> | routes/report_routes.py:user_report | 200, 404 |
| GET | /categories | routes/report_routes.py:get_categories | 200 |
| POST | /categories | routes/report_routes.py:create_category | 201, 400 |
| PUT | /categories/<id> | routes/report_routes.py:update_category | 200, 404 |
| DELETE | /categories/<id> | routes/report_routes.py:delete_category | 200, 404 |

================================
Total: 17 findings
================================
