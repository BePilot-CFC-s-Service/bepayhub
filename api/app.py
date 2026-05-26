"""
BePayHub API - Main Entry Point
Arquitetura em camadas: Controllers -> Services -> Repositories
"""
from flask import Flask, jsonify
from config import Settings, validate_settings
from errors import ApiError
from controllers.customer_controller import CustomerController
from controllers.student_controller import StudentController
from controllers.instructor_controller import InstructorController


def create_app() -> Flask:
    """
    Factory function para criar a aplicação Flask
    
    Returns:
        Aplicação Flask configurada
    """
    app = Flask(__name__)
    app.config["DEBUG"] = Settings.DEBUG
    app.config["TESTING"] = Settings.TESTING
    
    # Registra manipuladores de erro globais
    _register_error_handlers(app)
    
    # Registra blueprints dos controladores
    _register_controllers(app)
    
    # Registra endpoint de health check
    _register_health_check(app)
    
    return app


def _register_error_handlers(app: Flask) -> None:
    """Registra manipuladores de erro globais"""
    
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
    """Registra blueprints dos controladores"""
    
    # Instancia controladores
    customer_controller = CustomerController()
    student_controller = StudentController()
    instructor_controller = InstructorController()
    
    # Registra blueprints
    app.register_blueprint(
        customer_controller.get_blueprint(),
        url_prefix=Settings.API_PREFIX
    )
    app.register_blueprint(
        student_controller.get_blueprint(),
        url_prefix=Settings.API_PREFIX
    )
    app.register_blueprint(
        instructor_controller.get_blueprint(),
        url_prefix=Settings.API_PREFIX
    )


def _register_health_check(app: Flask) -> None:
    """Registra endpoint de health check"""
    
    @app.route(f"{Settings.API_PREFIX}/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"}), 200


def main():
    """Função principal para executar a aplicação"""
    # Valida configurações necessárias
    try:
        validate_settings()
    except RuntimeError as e:
        print(f"❌ Erro de configuração: {e}")
        exit(1)
    
    # Cria aplicação
    app = create_app()
    
    # Executa servidor
    port = Settings.PORT
    print(f"🚀 Iniciando BePayHub API na porta {port}")
    print(f"📌 Base URL: http://localhost:{port}{Settings.API_PREFIX}")
    print(f"🔧 Debug: {Settings.DEBUG}")
    print(f"✅ API iniciada com sucesso!")
    
    app.run(host="0.0.0.0", port=port, debug=Settings.DEBUG)


if __name__ == "__main__":
    main()
