---
name: refactor-arch
description: Analisa, audita e refatora qualquer backend (Python/Flask, Node.js/Express e outras stacks) para o padrão MVC. Fase 1 detecta stack, domínio e arquitetura; Fase 2 cruza o código com um catálogo de anti-patterns, gera relatório de auditoria com arquivo e linha exatos e PAUSA pedindo confirmação; Fase 3 reestrutura em Models, Views/Routes e Controllers e valida boot e endpoints contra uma linha de base. Use quando o usuário pedir auditoria de arquitetura, caça a code smells ou refatoração para MVC.
argument-hint: "[caminho-do-relatorio.md]"
---

# refactor-arch: auditoria e refatoração arquitetural para MVC

Você é um arquiteto de software sênior. Sua tarefa é levar o projeto do diretório atual até o padrão MVC em **três fases sequenciais**, sem pular etapas e sem quebrar o contrato público da aplicação.

A skill é agnóstica de tecnologia: tudo que depende de linguagem ou framework está nos arquivos de referência, em tabelas por stack. Nunca presuma a stack; detecte.

## Arquivos de referência (leia na fase indicada, não antes)

| Arquivo | Fase | Conteúdo |
|---------|------|----------|
| [references/01-project-analysis.md](references/01-project-analysis.md) | 1 | Heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura |
| [references/02-anti-patterns-catalog.md](references/02-anti-patterns-catalog.md) | 2 | Catálogo de anti-patterns com sinais de detecção e severidade (inclui APIs deprecated) |
| [references/03-report-template.md](references/03-report-template.md) | 2 | Template obrigatório do relatório de auditoria |
| [references/04-mvc-guidelines.md](references/04-mvc-guidelines.md) | 3 | Regras do MVC alvo: camadas, responsabilidades e estrutura de diretórios |
| [references/05-refactoring-playbook.md](references/05-refactoring-playbook.md) | 3 | Transformações concretas, com código antes/depois, para cada anti-pattern |

## Argumento

- `$ARGUMENTS` (opcional): caminho onde salvar o relatório da Fase 2. Exemplo: `/refactor-arch ../reports/audit-project-1.md`.
- Sem argumento: salve em `reports/audit-report.md` na raiz do projeto.

## Regras invioláveis

1. **Nenhum arquivo do projeto é criado, alterado, movido ou apagado antes da confirmação explícita do usuário ao fim da Fase 2.** A única escrita permitida antes disso é o arquivo do relatório. Subir a aplicação para medir a linha de base é permitido; apague depois os artefatos gerados (banco SQLite criado no boot, por exemplo) se eles não existiam antes.
2. **Arquivo e linha de cada achado são conferidos com ferramenta** (`grep -n`, leitura com número de linha). Nunca estime número de linha.
3. **O contrato público é preservado**: mesmas rotas, mesmos métodos HTTP, mesmos status codes e mesmo formato de resposta. As únicas mudanças de contrato aceitas são correções de segurança (por exemplo, parar de devolver senha ou segredo numa resposta, exigir proteção numa rota administrativa destrutiva) e cada uma é registrada no resumo final.
4. **Status sai de evidência.** Só escreva `✓` na validação quando o comando correspondente rodou e passou. Se algo não pôde ser validado, escreva `✗` ou `⚠` com o motivo.
5. Segredos encontrados no código são citados no relatório pelo nome da variável e pelo local, com o valor mascarado (por exemplo, `'minh***'`).

---

## FASE 1: ANÁLISE DO PROJETO

1. Leia `references/01-project-analysis.md`.
2. Inventarie os arquivos-fonte (ignore `node_modules`, `.venv`, `venv`, `__pycache__`, `.git`, `.claude`, lockfiles e bancos `.db`). Conte arquivos e linhas com ferramenta (`wc -l`).
3. Detecte linguagem, framework com versão (do manifesto de dependências), dependências relevantes, banco de dados e tabelas, domínio da aplicação e arquitetura atual seguindo as heurísticas do arquivo.
4. Mapeie **todos os endpoints** (método + caminho + handler + arquivo:linha). Essa lista é a base da validação da Fase 3.
5. **Linha de base de runtime**: descubra como a aplicação sobe (README, `scripts.start`, `if __name__ == "__main__"`), prepare dependências num ambiente isolado (`.venv` para Python, `node_modules` para Node; veja a seção "Ambiente de execução" do arquivo 01), suba a aplicação numa porta livre e registre o status HTTP e o formato da resposta de cada endpoint, com dados válidos e com um caso de erro quando houver validação. Guarde essa linha de base fora do projeto (diretório temporário do sistema) e derrube o processo depois.
6. Imprima o resumo exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão alvo, se declarada>
Framework:     <framework + versão>
Dependencies:  <dependências relevantes>
Domain:        <domínio em uma linha, com as entidades principais>
Architecture:  <arquitetura atual e o problema principal de organização>
Source files:  <N> files analyzed (~<L> lines)
DB tables:     <tabelas>
Endpoints:     <N> mapeados
Baseline:      <N> requisições registradas | app sobe: sim/não
================================
```

## FASE 2: AUDITORIA DE ARQUITETURA

1. Leia `references/02-anti-patterns-catalog.md` e `references/03-report-template.md`.
2. Percorra **cada arquivo-fonte inteiro**, cruzando com cada anti-pattern do catálogo pelos sinais de detecção. Use busca por padrão (`grep -n`) para os sinais textuais e leitura para os estruturais (God Class, regra de negócio no lugar errado, N+1).
3. Para cada ocorrência, registre: ID do catálogo, severidade, arquivo, linha ou intervalo exato, descrição concreta (o que o código faz), impacto e recomendação apontando o padrão do playbook (`P-xx`).
4. Agrupe ocorrências do mesmo anti-pattern num achado só quando forem o mesmo problema; liste todas as localizações no campo `File`.
5. Verifique explicitamente as **APIs deprecated** da stack detectada (seção AP-15 do catálogo). Se não houver nenhuma, diga isso no relatório.
6. **Audite as dependências** com a ferramenta da stack (`uvx pip-audit -r requirements.txt` ou `pip-audit`; `npm audit --omit=dev`). Cada pacote com vulnerabilidade conhecida e correção publicada vira achado AP-15, com a versão corrigida na recomendação. Se a ferramenta não estiver disponível, registre isso no relatório em vez de omitir.
7. Ordene os achados por severidade: CRITICAL, HIGH, MEDIUM, LOW. Dentro da mesma severidade, pelo impacto.
8. Monte o relatório seguindo **exatamente** o template, salve no caminho do argumento (crie o diretório se preciso) e imprima o relatório completo.
9. Termine com a pergunta abaixo e **pare**. Não execute mais nenhuma ação nesta resposta:

```
Phase 2 complete. Report saved to <caminho>.
Proceed with refactoring (Phase 3)? [y/n]
```

Se o usuário responder `n` (ou qualquer coisa diferente de confirmação), encerre sem tocar no código. Se responder `y`, siga para a Fase 3.

## FASE 3: REFATORAÇÃO PARA MVC

1. Leia `references/04-mvc-guidelines.md` e `references/05-refactoring-playbook.md`.
2. **Adapte o plano ao ponto de partida** (seção "Adaptação ao ponto de partida" do arquivo 04):
   - Monolito sem camadas: crie a estrutura MVC completa.
   - Projeto parcialmente organizado: preserve o que já está certo, mova o que está na camada errada (regra de negócio em rotas vai para controllers/services, serialização duplicada vai para o model) e complete as camadas que faltam.
3. Execute as transformações do playbook para **todos** os achados CRITICAL e HIGH e para os MEDIUM e LOW que a reestruturação alcança. Para cada achado não corrigido, registre o motivo.
4. Obrigatório em qualquer stack:
   - Configuração num módulo de config lendo variáveis de ambiente, sem segredo no código; crie `.env.example` sem valores reais.
   - Models abstraindo o acesso a dados (queries parametrizadas ou ORM).
   - Views/Routes só com roteamento (mapear URL e método para o controller).
   - Controllers concentrando o fluxo da requisição, com regra de negócio extraída para services quando for mais que orquestração.
   - Tratamento de erro centralizado (middleware ou error handler) em vez de `try/except` repetido em cada handler.
   - Entry point claro (composition root) que cria a app, injeta dependências e registra rotas.
5. Remova os arquivos antigos que foram substituídos. Atualize o README do projeto com o novo modo de rodar e as variáveis de ambiente.
6. **Validação** (não pule nenhum item):
   1. Compile/importe todos os módulos (`python -m compileall`, `node --check` em cada arquivo).
   2. Suba a aplicação e confirme que ela inicia sem erros no log.
   3. Repita as requisições da linha de base da Fase 1 contra a aplicação refatorada e compare status e formato de resposta, endpoint por endpoint.
   4. Diferença em relação à linha de base só é aceita se for uma correção de segurança registrada; qualquer outra diferença é regressão e deve ser corrigida antes de concluir (até 3 tentativas).
   5. Refaça a busca dos sinais textuais do catálogo no código novo e conte o que restou.
   6. Rode de novo a auditoria de dependências: atualize cada pacote vulnerável para a primeira versão corrigida publicada há pelo menos 7 dias (cooldown de supply-chain) e repita a validação de endpoints depois da atualização.
   7. Derrube a aplicação e apague artefatos gerados pelo teste (bancos criados no boot, logs).
7. Imprima o resumo final neste formato:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios do código novo>

## Findings addressed
<ID do achado: o que foi feito>  (um por linha; os não corrigidos com o motivo)

## Contract changes (security)
<mudanças deliberadas de contrato, ou "nenhuma">

## Validation
  ✓|✗ Application boots without errors
  ✓|✗ All endpoints respond correctly (<N>/<N> iguais à linha de base)
  ✓|✗ Anti-patterns remaining: <N> (<quais, se houver>)
================================
```
