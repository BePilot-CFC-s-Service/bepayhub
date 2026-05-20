# BePayHub API - Sistema de Pagamentos da BePilot

API REST para gerenciamento de transações de pagamentos da plataforma BePilot, com integração com o sistema Asaas. Arquitetura em camadas seguindo princípios de POO.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura-em-camadas)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Executar a Aplicação](#executar-a-aplicação)
- [Endpoints](#endpoints)
- [Fluxo de Dados](#fluxo-de-dados)
- [Desenvolvimento](#desenvolvimento)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

**BePayHub** centraliza cobranças de:
- 👨‍🎓 **Alunos:** Pagamentos por aula (PIX, Débito, Cartão de Crédito)
- 👨‍🏫 **Instrutores:** Mensalidades/Assinaturas (Cartão de Crédito)

### Características Principais

✅ Arquitetura em camadas com POO  
✅ Sem Swagger (API limpa e simples)  
✅ Validações robustas  
✅ Integração com Asaas  
✅ Tratamento de erros estruturado  
✅ Fácil extensão e manutenção  

### Informações Técnicas

- **Base URL:** `http://localhost:10000/api/v1`
- **Versão:** 2.0.0
- **Framework:** Flask 3.0.0
- **Python:** 3.10+
- **Integração Externa:** [Asaas API](https://docs.asaas.com/)

---

## 🏗️ Arquitetura em Camadas

```
HTTP Request
    ↓
┌─────────────────────────────────────────┐
│ CONTROLLER (HTTP Routes)                │
│ - Valida entrada (JSON)                 │
│ - Chama service                         │
│ - Retorna resposta HTTP                 │
└─────────────────────┬───────────────────┘
                      ↓
┌─────────────────────────────────────────┐
│ SERVICE (Business Logic)                │
│ - Validações de negócio                 │
│ - Orquestração de ações                 │
│ - Transformação de dados                │
└─────────────────────┬───────────────────┘
                      ↓
┌─────────────────────────────────────────┐
│ REPOSITORY (Data Access)                │
│ - Comunicação com Asaas API             │
│ - Tratamento de erros de rede           │
│ - Serialização JSON                     │
└─────────────────────┬───────────────────┘
                      ↓
                  Asaas API
```

### Responsabilidades por Camada

| Camada | Responsabilidade | Exemplo |
|--------|-----------------|---------|
| **Controller** | HTTP routing | `CustomerController.create_customer()` |
| **Service** | Lógica de negócio | `CustomerService.create_customer(data)` |
| **Repository** | Acesso a dados | `AsaasRepository.create_customer(payload)` |

---

## 📁 Estrutura do Projeto

```
bepilot-payments/
├── README.md                           # Este arquivo
├── .env                                # Variáveis de ambiente (não comitar)
├── api/
│   ├── app.py                        # Entry point (inicializa e executa app)
│   ├── config.py                      # Configurações (Settings)
│   ├── errors.py                      # Exceções personalizadas
│   ├── requirements.txt               # Dependências Python
│   ├── __init__.py
│   │
│   ├── controllers/                   # Camada de Apresentação (HTTP Routes)
│   │   ├── __init__.py
│   │   ├── base_controller.py         # Classe base
│   │   ├── customer_controller.py     # Rotas de clientes (criação no Asaas)
│   │   ├── student_controller.py      # Rotas de aulas (pagamentos e consultas)
│   │   └── instructor_controller.py   # Rotas de instrutores (assinatura e consultas)
│   │
│   ├── services/                      # Camada de Lógica (Business Logic)
│   │   ├── __init__.py
│   │   ├── payment_services.py        # CustomerService, PaymentService (orquestração)
│   │   ├── validators.py              # Validações de entrada e regras de negócio
│   │   └── payload.py                 # Construtores de payload para Asaas API
│   │
│   ├── repositories/                  # Camada de Dados (Data Access)
│   │   ├── __init__.py
│   │   └── asaas_repository.py        # Comunicação com Asaas API
│   │
│   ├── dto/                           # DTOs - Data Transfer Objects (I/O)
│   │   ├── __init__.py
│   │   └── user_dto.py                # PaymentDTO, CustomerDTO (serialização)
│   │
│   └── models/                        # Models - Entidades (Type Safety)
│       ├── __init__.py
│       └── asaas.py                   # Customer, Payment, Subscription (representam dados Asaas)
```

---

## ⚙️ Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip
- git

### Passos

**1. Clone o repositório:**
```bash
git clone https://github.com/BePilot-CFC-s-Service/bepayhub.git
cd bepayhub
```

**2. Crie ambiente virtual:**
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**3. Instale dependências:**
```bash
cd api
pip install -r requirements.txt
```

**4. Configure `.env`:**
```bash
# Na raiz do projeto, crie arquivo .env:
FLASK_DEBUG=false
FLASK_TESTING=false
PORT=10000
API_PREFIX=/api/v1

# Asaas API
ASAAS_API_URL=https://sandbox.asaas.com/api/v3
ASAAS_API_KEY=sua_chave_api_aqui
ASAAS_REQUEST_TIMEOUT=10
```

---

## 🚀 Executar a Aplicação

**Inicie o servidor:**
```bash
cd api
python app.py
```

**Saída esperada:**
```
🚀 Iniciando BePayHub API na porta 10000
📌 Base URL: http://localhost:10000/api/v1
🔧 Debug: False
✅ API iniciada com sucesso!
 * Running on http://0.0.0.0:10000
```

A API está pronta em: **`http://localhost:10000/api/v1`**

---

## 📚 Endpoints

### Health Check

**GET** `/health`

```bash
curl http://localhost:10000/api/v1/health
```

Resposta:
```json
{"status": "ok"}
```

---

### Clientes

#### Criar Cliente

**POST** `/customers`

```bash
curl -X POST http://localhost:10000/api/v1/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@example.com",
    "cpf_cnpj": "12345678901234",
    "mobile_phone": "85987654321",
    "external_reference": {"student_id": 123},
    "address": "Rua A",
    "address_number": "100",
    "city": "Fortaleza",
    "state": "CE",
    "postal_code": "60000-000"
  }'
```

Campos obrigatórios:
- `name` - Nome do cliente
- `cpf_cnpj` - CPF ou CNPJ (válido)
- `email` - Email válido
- `mobile_phone` - Telefone celular
- `external_reference` - Objeto com `student_id` OU `instructor_id`

---

#### Listar Clientes

**GET** `/customers`

```bash
curl "http://localhost:10000/api/v1/customers?limit=100&offset=0"
```

---

### Pagamentos

#### Pagamento Estudante - PIX

**POST** `/payments/student/driving-lessons/pix`

```bash
curl -X POST http://localhost:10000/api/v1/payments/student/driving-lessons/pix \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cus_123",
    "value": 100.00,
    "due_date": "2026-06-30"
  }'
```

---

#### Pagamento Estudante - Cartão de Crédito

**POST** `/payments/student/driving-lessons/credit`

```bash
curl -X POST http://localhost:10000/api/v1/payments/student/driving-lessons/credit \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cus_456",
    "value": 150.00,
    "due_date": "2026-06-30",
    "creditCard": {
      "holderName": "João Silva",
      "number": "4111111111111111",
      "expiryMonth": "12",
      "expiryYear": "2027",
      "ccv": "123"
    },
    "creditCardHolderInfo": {
      "name": "João Silva",
      "email": "joao@example.com",
      "cpfCnpj": "12345678900",
      "phone": "85987654321",
      "addressNumber": "100",
      "postalCode": "60000-000"
    }
  }'
```

---

#### Pagamento Instrutor - Assinatura

**POST** `/payments/instructor/monthly-fees`

```bash
curl -X POST http://localhost:10000/api/v1/payments/instructor/monthly-fees \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cus_inst_001",
    "value": 1500.00,
    "due_date": "2026-06-01",
    "creditCard": {
      "holderName": "Prof Silva",
      "number": "4111111111111111",
      "expiryMonth": "12",
      "expiryYear": "2027",
      "ccv": "123"
    },
    "creditCardHolderInfo": {
      "name": "Prof Silva",
      "email": "prof@escola.com",
      "cpfCnpj": "98765432100",
      "phone": "85999999999",
      "addressNumber": "500",
      "postalCode": "60000-000"
    }
  }'
```

**Importante:** Mensalidades aceitam apenas cartão de crédito!

---

#### Listar Pagamentos

**GET** `/payments/{origin}`

- `origin`: `student` ou `instructor`

```bash
# Pagamentos de estudantes
curl "http://localhost:10000/api/v1/payments/student?student_id=123&limit=100"

# Pagamentos de instrutores
curl "http://localhost:10000/api/v1/payments/instructor?instructor_id=99&limit=100"
```

---

## 🎯 Controllers Detalhados

### CustomerController

**Arquivo:** [api/controllers/customer_controller.py](api/controllers/customer_controller.py)

**Responsabilidade:** Criar e listar clientes no Asaas

**Endpoints:**
- `POST /customers` - Criar novo cliente
- `GET /customers` - Listar clientes

```python
# Exemplo
from controllers import CustomerController

controller = CustomerController()
# Acessa rotas via blueprint
```

---

### StudentController

**Arquivo:** [api/controllers/student_controller.py](api/controllers/student_controller.py)

**Responsabilidade:** Gerenciar pagamentos de aulas para estudantes

**Endpoints:**
- `POST /payments/student/driving-lessons/<method>` - Criar pagamento de aula
  - `method`: `pix`, `credit`, ou `debit`
- `GET /payments/student` - Listar pagamentos de aulas

**Filtros disponíveis em GET:**
- `student_id` - ID do estudante
- `lesson_id` - ID da aula
- `customer` - ID do cliente no Asaas
- `status` - Status do pagamento (PENDING, CONFIRMED, etc.)
- `limit` - Limite de resultados (padrão: 100)
- `offset` - Deslocamento (padrão: 0)

```bash
# Criar pagamento PIX para aula
curl -X POST http://localhost:10000/api/v1/payments/student/driving-lessons/pix \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "cus_123", "value": 100.00, "due_date": "2026-06-30"}'

# Listar pagamentos de um estudante
curl "http://localhost:10000/api/v1/payments/student?student_id=123"
```

---

### InstructorController

**Arquivo:** [api/controllers/instructor_controller.py](api/controllers/instructor_controller.py)

**Responsabilidade:** Gerenciar assinaturas/mensalidades de instrutores

**Endpoints:**
- `POST /payments/instructor/monthly-fees` - Criar assinatura/mensalidade
- `GET /payments/instructor` - Listar assinaturas e pagamentos

**Filtros disponíveis em GET:**
- `instructor_id` - ID do instrutor
- `customer` - ID do cliente no Asaas
- `status` - Status da assinatura
- `limit` - Limite de resultados (padrão: 100)
- `offset` - Deslocamento (padrão: 0)

**Regras de Negócio:**
- Apenas cartão de crédito é aceito para assinatura
- Dados de cartão são obrigatórios

```bash
# Criar assinatura/mensalidade
curl -X POST http://localhost:10000/api/v1/payments/instructor/monthly-fees \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cus_inst_001",
    "value": 1500.00,
    "due_date": "2026-06-01",
    "creditCard": {...},
    "creditCardHolderInfo": {...}
  }'

# Listar assinaturas de um instrutor
curl "http://localhost:10000/api/v1/payments/instructor?instructor_id=99"
```

---

---

## 📚 Estrutura de Dados

### DTOs (Data Transfer Objects)

**Arquivo:** [api/dto/user_dto.py](api/dto/user_dto.py)

DTOs são usados para **transferência de dados** entre a API e clientes externos. Eles definem a forma dos dados que entram (requisições) e saem (respostas).

```python
# Exemplo - PaymentDTO
{
    "customer_id": "cus_123",
    "value": 100.00,
    "due_date": "2026-06-30",
    "billing_type": "pix",
    "student_id": 123,
    "lesson_id": 456
}
```

**Classes disponíveis:**
- `PaymentDTO` - Representa um pagamento de entrada
- `CustomerDTO` - Representa um cliente de entrada

---

### Models (Entity Representations)

**Arquivo:** [api/models/asaas.py](api/models/asaas.py)

Models representam **entidades do Asaas** para type safety e manipulação de dados. Transformam dicionários brutos em objetos tipados.

```python
# Exemplo - Customer Model
customer = Customer({
    "id": "cus_456",
    "name": "João Silva",
    "email": "joao@example.com",
    "cpfCnpj": "12345678901234"
})
```

**Classes disponíveis:**
- `Customer` - Representa um cliente do Asaas
- `Payment` - Representa um pagamento do Asaas
- `Subscription` - Representa uma assinatura do Asaas

---

### Payload Builders

**Arquivo:** [api/services/payload.py](api/services/payload.py)

Payload builders **transformam DTOs em payloads** que a API Asaas entende.

```python
# Exemplo - Construir payload de pagamento
payload = build_payment_payload(
    data=dto_data,
    billing_type="pix",
    description="Aula de direção",
    external_reference="student-123-lesson-456",
    remote_ip="192.168.1.1"
)
```

**Funções disponíveis:**
- `build_payment_payload()` - Constrói pagamento para Asaas
- `build_subscription_payload()` - Constrói assinatura para Asaas
- `build_customer_payload()` - Constrói cliente para Asaas
- `get_billing_type()` - Converte método de pagamento (pix → PIX)
- `build_external_reference()` - Constrói referência externa

---

### Validators (Input Validation)

**Arquivo:** [api/services/validators.py](api/services/validators.py)

Validadores garantem que os dados de **entrada estão corretos** antes de serem processados.

```python
# Exemplo - Validar pagamento
validate_payment_payload(
    data=request.json,
    billing_type="pix"
)
```

**Funções disponíveis:**
- `validate_payment_payload()` - Valida dados de pagamento
- `validate_customer_payload()` - Valida dados de cliente
- `validate_origin()` - Valida origem (student/instructor)
- `require_fields()` - Verifica campos obrigatórios
- `require_json_body()` - Valida JSON em request

---

## 🔄 Fluxo de Dados Detalhado

### Criar Pagamento (Student)

```
1. POST /api/v1/payments/student/driving-lessons/pix
   {
     "customer_id": "cus_123",
     "value": 100.00,
     "due_date": "2026-06-30"
   }

2. StudentController.create_pix_payment()
   ├─ require_json_body(request)           [Validators]
   └─ StudentPaymentService.create_payment()

3. StudentPaymentService.create_payment()
   ├─ validate_payment_payload(data)       [Validators]
   ├─ build_payment_payload(data, ...)     [Payload]
   └─ AsaasRepository.create_payment()

4. AsaasRepository.create_payment()
   ├─ POST https://sandbox.asaas.com/api/v3/payments
   ├─ return Payment(response_json)        [Models]
   └─ Convert to dict for response

5. HTTP Response (200 OK)
   {
     "id": "pay_456",
     "customer_id": "cus_123",
     "value": 100.00,
     "status": "PENDING"
   }
```

---

### Adicionar Novo Endpoint

**1. Controller:**
```python
class StudentController(BaseController):
    def novo_endpoint(self):
        data = require_json_body(request)  # Validar JSON
        response, status = self.service.nova_acao(data)
        return jsonify(response), status
```

**2. Service:**
```python
class PaymentService:
    def nova_acao(self, data):
        # Validar dados
        validate_payment_payload(data)
        # Transformar em payload
        payload = build_payment_payload(data, ...)
        # Acessar repository
        return self.repository.nova_acao(payload)
```

**3. Repository:**
```python
class AsaasRepository:
    @classmethod
    def nova_acao(cls, payload):
        response = requests.post(url, headers, json=payload)
        return Payment(response.json())  # Envolvido em Model
```

---

## 🔒 Tratamento de Erros

### Exemplo de Resposta de Erro

```json
{
  "error": "Campos obrigatorios ausentes",
  "details": {
    "missing": ["mobile_phone", "external_reference"]
  }
}
```

### Status Codes

| Code | Significado |
|------|------------|
| 200 | OK - Sucesso |
| 201 | Created - Recurso criado |
| 400 | Bad Request - Erro de validação |
| 404 | Not Found - Endpoint não existe |
| 500 | Internal Server Error - Erro do servidor |
| 504 | Gateway Timeout - Timeout na integração |

---

## 🔧 Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `FLASK_DEBUG` | false | Ativar modo debug |
| `FLASK_TESTING` | false | Ativar modo teste |
| `PORT` | 10000 | Porta do servidor |
| `API_PREFIX` | /api/v1 | Prefixo das rotas |
| `ASAAS_API_URL` | - | URL base do Asaas (obrigatório) |
| `ASAAS_API_KEY` | - | Chave de autenticação (obrigatório) |
| `ASAAS_REQUEST_TIMEOUT` | 10 | Timeout em segundos |

---

## 🐛 Troubleshooting

### "Variáveis de ambiente obrigatórias ausentes"

Verifique o arquivo `.env`:
```env
ASAAS_API_URL=https://sandbox.asaas.com/api/v3
ASAAS_API_KEY=sua_chave_valida
```

### "Timeout na integração com Asaas"

Aumentar timeout em `.env`:
```env
ASAAS_REQUEST_TIMEOUT=20  # 20 segundos
```

### "Customer inválido"

O customer_id não existe no Asaas. Crie um cliente primeiro:
```bash
POST /api/v1/customers
```

---

## 📝 Notas sobre a Arquitetura

### Separação de Responsabilidades

- **DTOs** - Definem formato de dados de entrada/saída (serialização)
- **Models** - Representam entidades Asaas com type safety
- **Validators** - Garantem dados válidos antes de processar
- **Payload Builders** - Transformam dados em formato esperado por Asaas
- **Services** - Orquestram lógica de negócio
- **Controllers** - Roteiam requisições HTTP
- **Repository** - Isola acesso à API Asaas

### Fluxo Padrão

```
Request (JSON)
    ↓
DTO (validação estrutura)
    ↓
Validator (validação negócio)
    ↓
Payload Builder (transformação)
    ↓
Repository (comunicação Asaas)
    ↓
Model (type safety resposta)
    ↓
Response (JSON)
```

---

## ✅ Checklist de Desenvolvimento

Ao adicionar novas funcionalidades:

- [ ] Criar/atualizar DTO em `dto/user_dto.py`
- [ ] Criar/atualizar validador em `services/validators.py`
- [ ] Criar/atualizar payload builder em `services/payload.py`
- [ ] Criar/atualizar model em `models/asaas.py`
- [ ] Adicionar método em repository
- [ ] Adicionar método em service
- [ ] Adicionar rota em controller
- [ ] Testar endpoint manualmente
- [ ] Verificar tratamento de erros
- [ ] Documentar em README
```

---

## 📖 Padrões de Design Utilizados

- ✅ **Repository Pattern** - Isolamento de dados
- ✅ **Service Layer** - Lógica de negócio centralizada
- ✅ **Dependency Injection** - Flexibilidade e testabilidade
- ✅ **Factory Pattern** - Criação de aplicação
- ✅ **Base Controller** - Reutilização de código

---

## 📚 Recursos Adicionais

- [Documentação Flask](https://flask.palletsprojects.com/)
- [API Asaas](https://docs.asaas.com/)
- [Python OOP](https://docs.python.org/3/tutorial/classes.html)

---

## 📄 Licença

MIT License - Veja LICENSE para detalhes

---

## 👥 Contribuição

1. Fork o repositório
2. Crie feature branch (`git checkout -b feature/new-feature`)
3. Commit mudanças (`git commit -m 'Add new feature'`)
4. Push branch (`git push origin feature/new-feature`)
5. Abra Pull Request

---

**Versão:** 2.0.0  
**Última Atualização:** 19 de maio de 2026  
**Status:** ✅ Produção
curl --request POST --url http://localhost:5000/api/v1/payments/student/driving-lessons/pix --header "Content-Type: application/json" --data '{"customer_id":"cus_123","value":150.0,"due_date":"2026-04-10","student_id":"stu_10","lesson_id":"les_90"}'
```

### POST /api/v1/payments/student/driving-lessons/debit

```bash
curl --request POST --url http://localhost:5000/api/v1/payments/student/driving-lessons/debit --header "Content-Type: application/json" --data '{"customer_id":"cus_123","value":150.0,"due_date":"2026-04-10","student_id":"stu_10","lesson_id":"les_90"}'
```

### POST /api/v1/payments/student/driving-lessons/credit

```bash
curl --request POST --url http://localhost:5000/api/v1/payments/student/driving-lessons/credit --header "Content-Type: application/json" --data '{"customer_id":"cus_123","value":150.0,"due_date":"2026-04-10","student_id":"stu_10","lesson_id":"les_90","creditCard":{"holderName":"Nome","number":"4111111111111111","expiryMonth":"12","expiryYear":"2030","ccv":"123"},"creditCardHolderInfo":{"name":"Nome","email":"email@dominio.com","cpfCnpj":"12345678900","postalCode":"01001000","addressNumber":"100","phone":"11999999999"}}'
```

### POST /api/v1/payments/instructor/monthly-fees

```bash
curl --request POST --url http://localhost:5000/api/v1/payments/instructor/monthly-fees --header "Content-Type: application/json" --data '{"customer_id":"cus_456","value":199.9,"due_date":"2026-04-10","instructor_id":"ins_88","creditCard":{"holderName":"Nome","number":"4111111111111111","expiryMonth":"12","expiryYear":"2030","ccv":"123"},"creditCardHolderInfo":{"name":"Nome","email":"email@dominio.com","cpfCnpj":"12345678900","postalCode":"01001000","addressNumber":"100","phone":"11999999999"}}'
```

### GET /api/v1/payments/student com filtros

```bash
curl --request GET --url "http://localhost:5000/api/v1/payments/student?student_id=stu_10&lesson_id=les_90&status=PENDING"
```

### GET /api/v1/payments/instructor com filtros

```bash
curl --request GET --url "http://localhost:5000/api/v1/payments/instructor?instructor_id=ins_88&status=PENDING"
```

## 📋 Regras de Negócio

- ✅ Mensalidade de instrutor e assinatura: apenas cartão de crédito
- ✅ Pagamento de aluno: PIX, débito e crédito
- ✅ Em pagamentos com cartão: `creditCard` e `creditCardHolderInfo` são obrigatórios
- ✅ Origin válido em consultas: `student` ou `instructor`

## ❌ Padrão de Erros

Formato:

```json
{
  "error": "mensagem"
}
```

Quando houver detalhes:

```json
{
  "error": "Campos obrigatórios ausentes",
  "details": {
    "missing": ["campo1", "campo2"]
  }
}
```
