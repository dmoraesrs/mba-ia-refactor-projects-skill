"""Validação de entrada centralizada. Mensagens mantidas iguais às da API original."""

from src.constants import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN
from src.errors import ValidationError


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def exigir_corpo(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    return dados


def validar_produto(dados):
    exigir_corpo(dados)
    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not _is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not _is_number(estoque):
        raise ValidationError("Estoque deve ser numérico")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def validar_filtros_busca(args):
    try:
        preco_min = float(args["preco_min"]) if args.get("preco_min") else None
        preco_max = float(args["preco_max"]) if args.get("preco_max") else None
    except ValueError:
        raise ValidationError("preco_min e preco_max devem ser numéricos") from None
    return {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria") or None,
        "preco_min": preco_min,
        "preco_max": preco_max,
    }


def validar_usuario(dados):
    exigir_corpo(dados)
    campos = [dados.get("nome", ""), dados.get("email", ""), dados.get("senha", "")]
    if not all(isinstance(valor, str) and valor for valor in campos):
        raise ValidationError("Nome, email e senha são obrigatórios")
    nome, email, senha = campos
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email, senha = dados.get("email", ""), dados.get("senha", "")
    if not (isinstance(email, str) and email and isinstance(senha, str) and senha):
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": email, "senha": senha}


def validar_pedido(dados):
    exigir_corpo(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _is_positive_int(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not isinstance(itens, list) or not all(
        isinstance(item, dict)
        and _is_positive_int(item.get("produto_id"))
        and _is_positive_int(item.get("quantidade"))
        for item in itens
    ):
        raise ValidationError("Cada item precisa de produto_id e quantidade inteiros positivos")
    return {
        "usuario_id": usuario_id,
        "itens": [{"produto_id": item["produto_id"], "quantidade": item["quantidade"]} for item in itens],
    }


def extrair_status(dados):
    dados = dados if isinstance(dados, dict) else {}
    return dados.get("status", "")
