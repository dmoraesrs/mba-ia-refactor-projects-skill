"""Camada View: só mapeia método + URL para o controller."""

from flask import Blueprint


def build_blueprint(controllers, require_admin):
    produtos = controllers["produto"]
    usuarios = controllers["usuario"]
    pedidos = controllers["pedido"]
    relatorios = controllers["relatorio"]
    health = controllers["health"]
    admin = controllers["admin"]

    rules = [
        ("/", "index", health.index, ["GET"]),
        ("/health", "health_check", health.health, ["GET"]),

        ("/produtos", "listar_produtos", produtos.listar, ["GET"]),
        ("/produtos/busca", "buscar_produtos", produtos.pesquisar, ["GET"]),
        ("/produtos/<int:produto_id>", "buscar_produto", produtos.buscar, ["GET"]),
        ("/produtos", "criar_produto", produtos.criar, ["POST"]),
        ("/produtos/<int:produto_id>", "atualizar_produto", produtos.atualizar, ["PUT"]),
        ("/produtos/<int:produto_id>", "deletar_produto", produtos.deletar, ["DELETE"]),

        ("/usuarios", "listar_usuarios", usuarios.listar, ["GET"]),
        ("/usuarios/<int:usuario_id>", "buscar_usuario", usuarios.buscar, ["GET"]),
        ("/usuarios", "criar_usuario", usuarios.criar, ["POST"]),
        ("/login", "login", usuarios.login, ["POST"]),

        ("/pedidos", "criar_pedido", pedidos.criar, ["POST"]),
        ("/pedidos", "listar_todos_pedidos", pedidos.listar_todos, ["GET"]),
        ("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedidos.listar_por_usuario, ["GET"]),
        ("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedidos.atualizar_status, ["PUT"]),

        ("/relatorios/vendas", "relatorio_vendas", relatorios.vendas, ["GET"]),

        ("/admin/reset-db", "reset_database", require_admin(admin.reset_database), ["POST"]),
        ("/admin/query", "executar_query", require_admin(admin.executar_query), ["POST"]),
    ]

    blueprint = Blueprint("api", __name__)
    for path, endpoint, view, methods in rules:
        blueprint.add_url_rule(path, endpoint, view, methods=methods)
    return blueprint
