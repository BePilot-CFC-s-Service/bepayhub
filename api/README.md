# BePayHub API - Sistema de Pagamentos BePilot

API REST para gerenciar pagamentos de aulas e repasses a instrutores, integrada ao **Asaas** e **Supabase**.

## Arquitetura

A aplicação segue o padrão de arquitetura em camadas:

* **Controllers**: responsáveis pelo roteamento HTTP e pela chamada dos serviços.
* **Services**: responsáveis pelas regras de negócio, validações e orquestração.
* **Repositories**: responsáveis pelo acesso aos dados via Supabase e pela integração com o Asaas.
* **Models/DTOs**: responsáveis pela definição de enums e estruturas de dados.

## Endpoints

### Health Check

```http
GET /health
```

Verifica se a API está funcionando corretamente.

---

### Clientes

```http
POST /customers
```

Cria um customer no Asaas para um usuário existente (`student` ou `instructor`).

**Body:**

```json
{
  "user_type": "student",
  "user_id": 123
}
```

`user_type` pode ser:

* `student`
* `instructor`

**Retorno:**

```json
{
  "customer_id": "cus_..."
}
```

---

### Pagamento de Aula

```http
POST /lessons/{lesson_id}/pay
```

Realiza o pagamento de uma aula.

**Body:**

```json
{
  "payment_method": "pix"
}
```

Ou, para cartão de crédito:

```json
{
  "payment_method": "credit_card",
  "credit_card": {},
  "credit_card_holder_info": {}
}
```

`payment_method` pode ser:

* `pix`
* `credit_card`

**Retorno:**

```json
{
  "success": true
}
```

---

### Status de Pagamento

```http
GET /lessons/{lesson_id}/payment-status
```

Consulta o status do pagamento de uma aula.

**Retorno:**

```json
{
  "status": "paid"
}
```

Status possíveis:

* `paid`
* `pending`
* `cancelled`
* `refunded`

---

### Aulas Pagas do Instrutor

```http
GET /instructors/{instructor_id}/lessons/paid
```

Retorna as aulas pagas associadas ao instrutor.

**Retorno:**

```json
[
  {
    "instructor_id": 123,
    "lesson_id": 456,
    "payment_status": "paid"
  }
]
```

---

### Aulas Não Pagas do Instrutor

```http
GET /instructors/{instructor_id}/lessons/unpaid
```

Retorna as aulas que ainda não foram pagas ao instrutor.

**Retorno:**

```json
[
  {
    "instructor_id": 123,
    "lesson_id": 456,
    "payment_status": "pending"
  }
]
```

---

### Transferência (Payout)

```http
POST /instructors/{instructor_id}/payout
```

Realiza uma transferência para o instrutor.

**Body:**

```json
{
  "amount": 100.00
}
```

**Retorno:**

```json
{
  "success": true,
  "transfer_id": "...",
  "amount": 100.00,
  "status": "pending"
}
```

---

### Saldo do Instrutor

```http
GET /instructors/{instructor_id}/balance
```

Consulta o saldo financeiro do instrutor.

**Retorno:**

```json
{
  "total_earned": 0,
  "available_amount": 0,
  "pending_amount": 0
}
```

## Configuração

Antes de executar a aplicação, copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Em seguida, preencha as variáveis de ambiente necessárias para a conexão com o **Supabase** e o **Asaas**.

> No Windows, também é possível simplesmente copiar o arquivo `.env.example`, renomeá-lo para `.env` e preencher os valores.

## Execução

Instale as dependências do projeto:

```bash
pip install -r requirements.txt
```

Execute a aplicação:

```bash
python app.py
```

Após iniciar, a API estará disponível em:

```text
http://localhost:10000/api/v1
```

## Integrações

### Supabase

O **Supabase** é utilizado como camada de persistência dos dados da aplicação.

A comunicação com o banco é realizada através dos repositories, mantendo o acesso aos dados separado das regras de negócio.

### Asaas

O **Asaas** é utilizado para:

* Criação de customers;
* Processamento de pagamentos;
* Pagamentos via PIX;
* Pagamentos via cartão de crédito;
* Transferências para instrutores.

## Considerações Finais

* A implementação utiliza **Supabase** para persistência e **Asaas** para processamento de pagamentos e transferências.
* As rotas seguem os requisitos fornecidos, com retornos mínimos e objetivos.
* Para pagamentos via cartão de crédito, são esperados os campos `credit_card` e `credit_card_holder_info` no corpo da requisição.
* A transferência (`payout`) assume que o instrutor possui uma chave PIX cadastrada.
* O fluxo de transferência pode ser ajustado conforme as regras de negócio e os requisitos da integração com o Asaas.
* O mapeamento dos status retornados pelo Asaas para os enums utilizados no banco é simplificado e pode ser refinado conforme a necessidade do projeto.

Esta implementação serve como uma base completa para o sistema de pagamentos do **BePilot**, permitindo evoluções incrementais conforme novos requisitos sejam adicionados.
