from flask import Flask, jsonify
from config import Settings
from errors import ApiError
from controllers.health_controller import HealthController
from controllers.customer_controller import CustomerController
from controllers.payment_controller import PaymentController
from controllers.instructor_subaccount_controller import InstructorSubaccountController
from controllers.webhook_controller import WebhookController

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = Settings.DEBUG
    app.config["TESTING"] = Settings.TESTING

    _register_error_handlers(app)
    _register_controllers(app)

    return app

def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        payload = {"error": error.message}
        if error.details is not None:
            payload["details"] = error.details
        return jsonify(payload), error.status_code

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({"error": "Endpoint não encontrado"}), 404

    @app.errorhandler(500)
    def handle_500(error):
        return jsonify({"error": "Erro interno do servidor"}), 500

def _register_controllers(app: Flask) -> None:
    controllers = [
        HealthController(),
        CustomerController(),
        PaymentController(),
        InstructorSubaccountController(),
        WebhookController(),
    ]
    for controller in controllers:
        app.register_blueprint(
            controller.blueprint,
            url_prefix=Settings.API_PREFIX
        )

def main():
    try:
        Settings.validate()
    except RuntimeError as e:
        print(f"❌ Erro de configuração: {e}")
        exit(1)

    app = create_app()
    print(f"🚀 BePayHub API iniciando na porta {Settings.PORT}")
    print(f"📌 Base URL: http://localhost:{Settings.PORT}{Settings.API_PREFIX}")
    app.run(host="0.0.0.0", port=Settings.PORT, debug=Settings.DEBUG)

if __name__ == "__main__":
    main()