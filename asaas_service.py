import os
import requests
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

ASAAS_URL = os.getenv("ASAAS_API_URL")
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")

def _get_headers():
    return {
        "access_token": ASAAS_API_KEY,
        "Content-Type": "application/json"
    }

def create_payment(payload):
    """
    Cria uma cobrança no Asaas.
    O payload deve conter 'customer', 'billingType', 'value', 'dueDate', etc.
    """
    url = f"{ASAAS_URL}/payments"
    response = requests.post(url, json=payload, headers=_get_headers())
    return response.json(), response.status_code

def list_payments(external_reference=None):
    """
    Lista cobranças. Usamos o externalReference para filtrar se 
    é pagamento de aluno ou de instrutor no ecossistema BePilot.
    """
    url = f"{ASAAS_URL}/payments"
    params = {}
    if external_reference:
        params["externalReference"] = external_reference
        
    response = requests.get(url, params=params, headers=_get_headers())
    return response.json(), response.status_code

def create_customer(name, cpf_cnpj, email):
    """
    Gera um cliente no Asaas. Necessário pois toda cobrança
    precisa de um ID de cliente (cus_00000X).
    """
    url = f"{ASAAS_URL}/customers"
    payload = {
        "name": name,
        "cpfCnpj": cpf_cnpj,
        "email": email
    }
    response = requests.post(url, json=payload, headers=_get_headers())
    return response.json(), response.status_code