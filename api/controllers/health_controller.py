from flask import jsonify
from .base_controller import BaseController

class HealthController(BaseController):
    def __init__(self):
        super().__init__("health", url_prefix="")
        self.register_route("/health", ["GET"], self.health)

    def health(self):
        return jsonify({"status": "ok"}), 200