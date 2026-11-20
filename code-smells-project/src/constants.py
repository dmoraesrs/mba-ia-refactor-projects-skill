"""Constantes de domínio nomeadas (valores de negócio)."""

APP_VERSION = "1.0.0"

CATEGORIA_PADRAO = "geral"
CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO = [STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO]

TIPO_CLIENTE = "cliente"
TIPO_ADMIN = "admin"

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))

PRODUTO_DESCONHECIDO = "Desconhecido"
