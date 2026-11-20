# 03: Template do relatório de auditoria (Fase 2)

O relatório é impresso no terminal **e** salvo em Markdown no caminho do argumento da skill. Use exatamente esta estrutura, na ordem abaixo. Todo texto entre `<...>` é substituído; nada fica como placeholder.

## Regras de preenchimento

1. **Summary** soma os achados por severidade; o total do rodapé é a soma do Summary.
2. **Findings** em ordem: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da severidade, maior impacto primeiro.
3. **File** usa caminho relativo à raiz do projeto e linha exata (`models.py:28`) ou intervalo (`models.py:47-50`). Várias ocorrências do mesmo problema: separe por vírgula (`models.py:28, models.py:92, models.py:110`).
4. **Description** diz o que o código faz, com o trecho ou o nome concreto (função, variável, rota). Segredo aparece mascarado.
5. **Impact** diz a consequência real (segurança, teste, manutenção, performance).
6. **Recommendation** diz o que fazer e cita o padrão do playbook (`P-xx`).
7. A seção **Deprecated APIs** é obrigatória: liste as encontradas ou escreva "Nenhuma API deprecated encontrada na stack detectada".
8. Sem achados genéricos ("código ruim"): cada achado aponta um local verificável.

## Template

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório>
Stack:   <linguagem> + <framework versão>
Files:   <N> analyzed | ~<L> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern> (<AP-xx>)
File: <arquivo:linha[, arquivo:linha]>
Description: <o que o código faz, concreto>
Impact: <consequência>
Recommendation: <o que fazer> (<P-xx>)

### [HIGH] <...> (<AP-xx>)
File: ...
Description: ...
Impact: ...
Recommendation: ...

<... demais achados, em ordem de severidade ...>

## Deprecated APIs
| Local | API | Equivalente moderno |
|-------|-----|---------------------|
| <arquivo:linha> | <api> | <substituta> |

## Endpoints mapped (baseline)
| Method | Path | Handler | Baseline status |
|--------|------|---------|-----------------|
| <GET> | </rota> | <arquivo:função> | <200> |

================================
Total: <N> findings
================================
```

## Exemplo de achado bem preenchido

```markdown
### [CRITICAL] Hardcoded Credentials (AP-02)
File: app.py:7, controllers.py:289
Description: SECRET_KEY definido como literal 'minh***' em app.py e devolvido no JSON do GET /health.
Impact: Quem lê o repositório ou chama /health obtém a chave usada para assinar sessões.
Recommendation: Ler SECRET_KEY de variável de ambiente no módulo de config e remover o campo da resposta do health check (P-02, P-04).
```
