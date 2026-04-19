# BePayHub

API de transações da BePayHub, focada em criacao e consulta de pagamentos com versionamento de rota, validacao de payload e integracao resiliente com Asaas.

## Sumario

- Visao geral
- Arquitetura DDD e BDD
- Estrutura do repositorio
- Configuracao de ambiente
- Como executar
- Endpoints v1
- Blocos copia e cola (curl)
- Parametros GET para consultas
- Regras de negocio
- Testes BDD
- Padrao de erros

## Visao geral

- Prefixo de versao da API: /api/v1
- Base URL local: http://localhost:5000/api/v1
- Integracao externa: Asaas API
- Objetivo principal: centralizar cobrancas de aluno (aula) e mensalidade de instrutor (assinatura)

## Arquitetura DDD (por camadas)

- Controllers (HTTP): [api/controllers/student_payments.py](api/controllers/student_payments.py), [api/controllers/instructor_payments.py](api/controllers/instructor_payments.py), [api/controllers/payments.py](api/controllers/payments.py), [api/controllers/customers.py](api/controllers/customers.py)
- Services (lógica de negócio): [api/services/payment_service.py](api/services/payment_service.py), [api/services/customer_service.py](api/services/customer_service.py)
- Application (validações): [api/application/validators.py](api/application/validators.py)
- Domain (regras de composição): [api/domain/payment_payload.py](api/domain/payment_payload.py)
- Repositories (abstração de dados): [api/repositories/payment_repository.py](api/repositories/payment_repository.py)
- Infrastructure (integração Asaas): [api/services/asaas_service.py](api/services/asaas_service.py)
- Bootstrap/config da API: [api/app.py](api/app.py), [api/config.py](api/config.py)
- OpenAPI (schemas automáticos): [api/openapi/models.py](api/openapi/models.py)

### BDD (Behavior-Driven)

Os testes foram escritos em estilo Given/When/Then para descrever comportamento.

- Cenarios BDD: [api/tests/test_routes.py](api/tests/test_routes.py)
- Fixtures de suporte: [api/tests/conftest.py](api/tests/conftest.py)

## Estrutura do repositório

```text
BePayHub/
  README.md
  api/
    app.py
    config.py
    errors.py
    requirements.txt
    openapi/
      models.py
    controllers/
      customers.py
      instructor_payments.py
      payments.py
      student_payments.py
    services/
      asaas_service.py
      customer_service.py
      payment_service.py
    application/
      validators.py
    domain/
      payment_payload.py
    repositories/
      payment_repository.py
    tests/
      conftest.py
      test_routes.py
```

## Configuracao de ambiente

Crie um .env na raiz do projeto:

```env
ASAAS_API_URL=https://sandbox.asaas.com/api/v3
ASAAS_API_KEY=sua_chave_aqui
ASAAS_REQUEST_TIMEOUT=10
FLASK_DEBUG=false
FLASK_TESTING=false
PORT=5000
API_PREFIX=/api/v1
```

## Como executar

### Copia e cola - setup

```bash
cd api/
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python app.py
```

### Swagger automático

O Swagger UI é montado a partir do OpenAPI gerado em runtime. Os schemas de request/response ficam em [api/openapi/models.py](api/openapi/models.py) (Pydantic).

- Para adicionar/remover campos que aparecem no Swagger: edite o model correspondente em [api/openapi/models.py](api/openapi/models.py)
- O endpoint `/api/v1/openapi.json` passa a refletir essas mudanças sem precisar editar `app.py`

## Endpoints v1

### Verificar Status da API

GET /api/v1/health

### Documentacao (Swagger / OpenAPI)

- Swagger UI: GET /api/v1/docs/
- OpenAPI JSON: GET /api/v1/openapi.json

### Criar Cliente

POST /api/v1/customers

### Criar Pagamento de Aluno (Aula)

POST /api/v1/payments/student/driving-lessons/{method}

method: pix | debit | credit

Payload base:

```json
{
  "customer_id": "cus_123",
  "value": 150.0,
  "due_date": "2026-04-10",
  "student_id": "stu_10",
  "lesson_id": "les_90"
}
```

Observacao:

- student_id e lesson_id sao opcionais, mas recomendados para melhorar rastreabilidade e filtros em consultas GET.

### Criar Mensalidade de Instrutor (Assinatura)

POST /api/v1/payments/instructor/monthly-fees

Regra de negocio: mensalidade aceita apenas cartao de credito.

Payload obrigatorio:

```json
{
  "customer_id": "cus_456",
  "value": 199.9,
  "due_date": "2026-04-10",
  "instructor_id": "ins_88",
  "creditCard": {
    "holderName": "Nome",
    "number": "4111111111111111",
    "expiryMonth": "12",
    "expiryYear": "2030",
    "ccv": "123"
  },
  "creditCardHolderInfo": {
    "name": "Nome",
    "email": "email@dominio.com",
    "cpfCnpj": "12345678900",
    "postalCode": "01001000",
    "addressNumber": "100",
    "phone": "11999999999"
  }
}
```

### Consultar Pagamentos

GET /api/v1/payments/{origin}

origin: student | instructor

## Parametros GET para consultas

Suportados em /api/v1/payments/{origin}:

- student_id: filtra referencia de pagamento de aluno
- lesson_id: filtra referencia de aula
- instructor_id: filtra referencia de instrutor
- customer: repassa filtro para Asaas
- status: repassa filtro para Asaas
- limit: repassa filtro para Asaas
- offset: repassa filtro para Asaas

Exemplos:

- /api/v1/payments/student?student_id=stu_10&lesson_id=les_90
- /api/v1/payments/instructor?instructor_id=ins_88&status=PENDING

## Blocos copia e cola (curl)

Observacao:

- No VS Code e no preview Markdown, use o botao Copy no canto superior direito de cada bloco de codigo para copiar em um clique.

### GET /api/v1/health

```bash
curl --request GET --url http://localhost:5000/api/v1/health
```

### POST /api/v1/customers

```bash
curl --request POST --url http://localhost:5000/api/v1/customers --header "Content-Type: application/json" --data '{"name":"Nome Completo","cpf_cnpj":"12345678900","email":"email@dominio.com"}'
```

### POST /api/v1/payments/student/driving-lessons/pix

```bash
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

## Regras de negocio

- Mensalidade de instrutor e assinatura: apenas cartao de credito.
- Pagamento de aluno: pix, debit e credit.
- Em pagamentos com cartao, creditCard e creditCardHolderInfo sao obrigatorios.
- origin valido em consultas: student ou instructor.

## Testes BDD

Executar:

```bash
pytest api/tests -q
```

Cenarios cobertos:

- Given valid pix payment, when creating student payment, then returns 200.
- Given invalid payment method, when creating student payment, then returns 400.
- Given credit payment without card data, when creating student payment, then returns 400.
- Given invalid origin, when listing payments, then returns 400.
- Given student origin with filters, when listing payments, then builds expected query.
- Given valid customer payload, when creating customer, then returns 200.
- Given Asaas timeout, when creating instructor monthly fee, then returns 504.
- Given monthly fee without card fields, when creating instructor monthly fee, then returns 400.

## Padrao de erros

Formato:

```json
{
  "error": "mensagem"
}
```

Quando houver detalhes:

```json
{
  "error": "Campos obrigatorios ausentes",
  "details": {
    "missing": ["campo1", "campo2"]
  }
}
```
