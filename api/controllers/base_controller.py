
from flask import Blueprint

class BaseController:
    def __init__(self, name: str, url_prefix: str = ""):
        self.blueprint = Blueprint(name, __name__, url_prefix=url_prefix)

    def register_route(self, rule, methods, handler, endpoint=None):
        endpoint = endpoint or handler.__name__
        self.blueprint.add_url_rule(
            rule,
            view_func=handler,
            methods=methods,
            endpoint=endpoint
        )
