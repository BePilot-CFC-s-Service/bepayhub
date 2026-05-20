"""
Base Controller - Classe base para todos os controladores
"""
from flask import Blueprint, jsonify, request
from typing import Callable, Dict, Any
from errors import ApiError


class BaseController:
    """Classe base para controladores"""
    
    def __init__(self, name: str, url_prefix: str = ""):
        self.name = name
        self.url_prefix = url_prefix
        self.blueprint = Blueprint(name, __name__, url_prefix=url_prefix)
    
    def register_route(
        self,
        rule: str,
        methods: list,
        handler: Callable,
        name: str = None
    ) -> None:
        """
        Registra uma rota no blueprint
        
        Args:
            rule: Caminho da rota (ex: "/customers")
            methods: Métodos HTTP (GET, POST, etc)
            handler: Função que trata a rota
            name: Nome opcional da rota
        """
        name = name or handler.__name__
        self.blueprint.add_url_rule(
            rule,
            view_func=handler,
            methods=methods,
            endpoint=name
        )
    
    def get_blueprint(self) -> Blueprint:
        """Retorna o blueprint registrado"""
        return self.blueprint
