from flask import Flask, request, jsonify
from asaas_service import create_payment, list_payments, create_customer

app = Flask(__name__)

# Dicionário para traduzir as rotas do seu sistema para os tipos do Asaas
BILLING_TYPE_MAP = {
    'pix': 'PIX',
    'credit': 'CREDIT_CARD',
    'debit': 'DEBIT_CARD'
}

@app.route('/studentPayment/drivingLesson/<method>', methods=['POST'])
def student_payment(method):
    """ Rota para pagamento de aulas de direção por alunos """
    
    billing_type = BILLING_TYPE_MAP.get(method.lower())
    if not billing_type:
        return jsonify({"error": "Método de pagamento inválido"}), 400

    data = request.json
    
    # Montagem do payload padrão exigido pelo Asaas
    payload = {
        "customer": data.get("customer_id"), # ID do cliente no Asaas (cus_xxxx)
        "billingType": billing_type,
        "value": data.get("value"),
        "dueDate": data.get("due_date"),
        "description": "BePilot - Pagamento de Aula de Direção",
        "externalReference": "studentPayment" # Marcação para o BePilot
    }

    # Se for cartão, precisamos anexar os dados do cartão de crédito informados no front-end
    if billing_type == 'CREDIT_CARD':
        payload["creditCard"] = data.get("creditCard")
        payload["creditCardHolderInfo"] = data.get("creditCardHolderInfo")
        # Para compras com cartão de crédito direto via API, o Asaas também exige o IP do cliente
        payload["remoteIp"] = request.remote_addr 

    response, status_code = create_payment(payload)
    return jsonify(response), status_code


@app.route('/instructorPayment/monthlyFee/<method>', methods=['POST'])
def instructor_payment(method):
    """ Rota para pagamento da mensalidade da plataforma por instrutores """
    
    billing_type = BILLING_TYPE_MAP.get(method.lower())
    if not billing_type:
        return jsonify({"error": "Método de pagamento inválido"}), 400

    data = request.json
    
    payload = {
        "customer": data.get("customer_id"),
        "billingType": billing_type,
        "value": data.get("value"),
        "dueDate": data.get("due_date"),
        "description": "BePilot - Mensalidade Instrutor",
        "externalReference": "instructorPayment" # Marcação para o BePilot
    }

    if billing_type == 'CREDIT_CARD':
        payload["creditCard"] = data.get("creditCard")
        payload["creditCardHolderInfo"] = data.get("creditCardHolderInfo")
        payload["remoteIp"] = request.remote_addr

    response, status_code = create_payment(payload)
    return jsonify(response), status_code


@app.route('/getPayments/<origin>', methods=['GET'])
def get_payments(origin):
    """
    Busca pagamentos baseando-se na origem (studentPayment ou instructorPayment).
    A API do Asaas usará o externalReference para filtrar.
    """
    if origin not in ['studentPayment', 'instructorPayment']:
        return jsonify({"error": "Origem inválida. Use studentPayment ou instructorPayment"}), 400
        
    response, status_code = list_payments(external_reference=origin)
    return jsonify(response), status_code


# --- Rota Auxiliar ---
@app.route('/createCustomer', methods=['POST'])
def add_customer():
    """ 
    No Asaas, você não consegue gerar cobranças sem que a pessoa seja cadastrada.
    Essa rota serve para cadastrar o Aluno ou Instrutor antes de cobrar.
    """
    data = request.json
    response, status_code = create_customer(
        name=data.get("name"),
        cpf_cnpj=data.get("cpf_cnpj"),
        email=data.get("email")
    )
    return jsonify(response), status_code


if __name__ == '__main__':
    app.run(debug=True, port=5000)