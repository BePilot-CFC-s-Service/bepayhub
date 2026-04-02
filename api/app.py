from flask import Flask, jsonify

from api.config import Settings
from api.errors import ApiError
from api.routes.customers import customers_bp
from api.routes.instructor_payment import instructor_payment_bp
from api.routes.payments import payments_bp
from api.routes.student_payment import student_payment_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = Settings.DEBUG
    app.config["TESTING"] = Settings.TESTING
    api_prefix = Settings.API_PREFIX

    app.register_blueprint(student_payment_bp, url_prefix=api_prefix)
    app.register_blueprint(instructor_payment_bp, url_prefix=api_prefix)
    app.register_blueprint(payments_bp, url_prefix=api_prefix)
    app.register_blueprint(customers_bp, url_prefix=api_prefix)

    @app.get(f"{api_prefix}/health")
    def health_check():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        payload = {"error": error.message}
        if error.details is not None:
            payload["details"] = error.details
        return jsonify(payload), error.status_code

    @app.errorhandler(Exception)
    def handle_generic_error(_error: Exception):
        return jsonify({"error": "Erro interno do servidor"}), 500

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=Settings.DEBUG, port=Settings.PORT)
