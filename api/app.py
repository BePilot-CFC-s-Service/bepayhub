from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

from api.config import Settings
from api.errors import ApiError
from api.presentation.routes.customers import customers_bp
from api.presentation.routes.instructor_payment import instructor_payment_bp
from api.presentation.routes.payments import payments_bp
from api.presentation.routes.student_payment import student_payment_bp


def _build_openapi_spec(api_prefix: str) -> dict:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "BePayHub",
            "version": "1.0.0",
            "description": "API de transacoes da BePayHub (Asaas)",
        },
        "servers": [{"url": api_prefix}],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthResponse"}
                                }
                            },
                        }
                    },
                }
            },
            "/customers": {
                "post": {
                    "summary": "Criar cliente",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/CreateCustomerRequest"
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Cliente criado no Asaas",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object", "additionalProperties": True}
                                }
                            },
                        },
                        "400": {
                            "description": "Erro de validacao",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "500": {
                            "description": "Erro interno",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "504": {
                            "description": "Timeout na integracao",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/payments/student/driving-lessons/{method}": {
                "post": {
                    "summary": "Criar pagamento de aluno (aula)",
                    "parameters": [
                        {
                            "name": "method",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "enum": ["pix", "debit", "credit"]},
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/StudentPaymentRequest"
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Pagamento criado no Asaas",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object", "additionalProperties": True}
                                }
                            },
                        },
                        "400": {
                            "description": "Erro de validacao",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "500": {
                            "description": "Erro interno",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "504": {
                            "description": "Timeout na integracao",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/payments/instructor/monthly-fees": {
                "post": {
                    "summary": "Criar mensalidade de instrutor (assinatura)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/InstructorMonthlyFeeRequest"
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Pagamento criado no Asaas",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object", "additionalProperties": True}
                                }
                            },
                        },
                        "400": {
                            "description": "Erro de validacao",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "500": {
                            "description": "Erro interno",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "504": {
                            "description": "Timeout na integracao",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
            "/payments/{origin}": {
                "get": {
                    "summary": "Consultar pagamentos",
                    "parameters": [
                        {
                            "name": "origin",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "enum": ["student", "instructor"]},
                        },
                        {"name": "student_id", "in": "query", "schema": {"type": "string"}},
                        {"name": "lesson_id", "in": "query", "schema": {"type": "string"}},
                        {
                            "name": "instructor_id",
                            "in": "query",
                            "schema": {"type": "string"},
                        },
                        {"name": "customer", "in": "query", "schema": {"type": "string"}},
                        {"name": "status", "in": "query", "schema": {"type": "string"}},
                        {"name": "limit", "in": "query", "schema": {"type": "string"}},
                        {"name": "offset", "in": "query", "schema": {"type": "string"}},
                    ],
                    "responses": {
                        "200": {
                            "description": "Lista retornada pelo Asaas",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object", "additionalProperties": True}
                                }
                            },
                        },
                        "400": {
                            "description": "Erro de validacao",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "500": {
                            "description": "Erro interno",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                        "504": {
                            "description": "Timeout na integracao",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            },
                        },
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "HealthResponse": {
                    "type": "object",
                    "properties": {"status": {"type": "string", "example": "ok"}},
                    "required": ["status"],
                    "additionalProperties": False,
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "details": {"type": "object", "additionalProperties": True},
                    },
                    "required": ["error"],
                    "additionalProperties": False,
                },
                "CreateCustomerRequest": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "cpf_cnpj": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                    "required": ["name", "cpf_cnpj", "email"],
                    "additionalProperties": False,
                },
                "StudentPaymentRequest": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "value": {"type": "number"},
                        "due_date": {"type": "string", "example": "2026-04-10"},
                        "student_id": {"type": "string"},
                        "lesson_id": {"type": "string"},
                        "creditCard": {"$ref": "#/components/schemas/CreditCard"},
                        "creditCardHolderInfo": {
                            "$ref": "#/components/schemas/CreditCardHolderInfo"
                        },
                    },
                    "required": ["customer_id", "value", "due_date"],
                    "additionalProperties": False,
                },
                "InstructorMonthlyFeeRequest": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"},
                        "value": {"type": "number"},
                        "due_date": {"type": "string", "example": "2026-04-10"},
                        "instructor_id": {"type": "string"},
                        "creditCard": {"$ref": "#/components/schemas/CreditCard"},
                        "creditCardHolderInfo": {
                            "$ref": "#/components/schemas/CreditCardHolderInfo"
                        },
                    },
                    "required": [
                        "customer_id",
                        "value",
                        "due_date",
                        "creditCard",
                        "creditCardHolderInfo",
                    ],
                    "additionalProperties": False,
                },
                "CreditCard": {
                    "type": "object",
                    "properties": {
                        "holderName": {"type": "string"},
                        "number": {"type": "string"},
                        "expiryMonth": {"type": "string"},
                        "expiryYear": {"type": "string"},
                        "ccv": {"type": "string"},
                    },
                    "required": [
                        "holderName",
                        "number",
                        "expiryMonth",
                        "expiryYear",
                        "ccv",
                    ],
                    "additionalProperties": False,
                },
                "CreditCardHolderInfo": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "cpfCnpj": {"type": "string"},
                        "postalCode": {"type": "string"},
                        "addressNumber": {"type": "string"},
                        "phone": {"type": "string"},
                    },
                    "required": [
                        "name",
                        "email",
                        "cpfCnpj",
                        "postalCode",
                        "addressNumber",
                        "phone",
                    ],
                    "additionalProperties": False,
                },
            }
        },
    }


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = Settings.DEBUG
    app.config["TESTING"] = Settings.TESTING
    api_prefix = Settings.API_PREFIX

    app.register_blueprint(student_payment_bp, url_prefix=api_prefix)
    app.register_blueprint(instructor_payment_bp, url_prefix=api_prefix)
    app.register_blueprint(payments_bp, url_prefix=api_prefix)
    app.register_blueprint(customers_bp, url_prefix=api_prefix)

    @app.get(f"{api_prefix}/openapi.json")
    def openapi_json():
        return jsonify(_build_openapi_spec(api_prefix)), 200

    docs_url = f"{api_prefix}/docs"
    openapi_url = f"{api_prefix}/openapi.json"
    swaggerui_bp = get_swaggerui_blueprint(
        docs_url,
        openapi_url,
        config={"app_name": "BePayHub"},
    )
    app.register_blueprint(swaggerui_bp, url_prefix=docs_url)

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
