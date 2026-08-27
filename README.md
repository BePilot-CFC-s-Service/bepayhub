
# 💳 BePayHub API - Sistema de Pagamentos BePilot

API REST para gerenciamento de pagamentos de aulas, subcontas de instrutores (**Split**) e repasses, integrada ao **Asaas** e **Supabase**.

---

## 🏗️ Arquitetura

A aplicação segue o padrão de **arquitetura em camadas**:

* **Controllers**: responsáveis pelo roteamento HTTP e pela chamada dos serviços.
* **Services**: responsáveis pelas regras de negócio, validações e orquestração.
* **Repositories**: responsáveis pelo acesso aos dados via Supabase e pela integração com o Asaas.
* **Models/DTOs**: responsáveis pela definição de enums e estruturas de dados.

---

## ✨ Novas Funcionalidades

### 👤 Subconta (Wallet) para Instrutores

Permite criar uma subconta **White Label** no Asaas para cada instrutor (MEI).

Ao criar uma subconta:

* É gerado um `walletId` exclusivo.
* É gerada uma `apiKey` exclusiva.
* O `walletId` é armazenado no campo `asaas_wallet_id` da tabela `instructor`.
* A `apiKey` é armazenada no campo `asaas_api_key` da tabela `instructor`.

### 💰 Split de Pagamento

Todo pagamento de aula, seja via **PIX** ou **Cartão de Crédito**, utiliza automaticamente o sistema de split.

A divisão definida é:

| Destino               | Percentual |
| --------------------- | ---------: |
| 🏢 Plataforma BePilot |    **10%** |
| 👨‍🏫 Instrutor       |    **90%** |

O instrutor recebe os **90% diretamente em sua subconta (wallet)** no Asaas.

---

# 📡 Endpoints

## 🟢 Health Check

### `GET /health`

Verifica se a API está funcionando corretamente.

**URL completa:**

```text
http://localhost:10000/api/v1/health
```

### Exemplo com cURL

```bash
curl --request GET \
  --url http://localhost:10000/api/v1/health
```

### Resposta

```json
{
  "status": "ok"
}
```

---

# 👤 Customers

## Criar Customer

### `POST /customers`

Cria um **Customer** no Asaas para um usuário existente (`student` ou `instructor`).

### Body

```json
{
  "user_type": "student",
  "user_id": 123
}
```

### `user_type`

Os valores possíveis são:

* `student`
* `instructor`

### Exemplo com cURL

```bash
curl --request POST \
  --url http://localhost:10000/api/v1/customers \
  --header 'Content-Type: application/json' \
  --data '{
    "user_type": "student",
    "user_id": 1
  }'
```

### Resposta

```json
{
  "customer_id": "cus_000005123456"
}
```

---

# 🏦 Subcontas de Instrutores

## Criar Subconta (Wallet) do Instrutor

### `POST /instructors/{instructor_id}/subaccount`

Cria uma subconta do instrutor no Asaas utilizando o modelo **BaaS White Label**.

> ⚠️ O instrutor deve ser **MEI** para utilizar esta funcionalidade.

### Exemplo

```bash
curl --request POST \
  --url http://localhost:10000/api/v1/instructors/1/subaccount
```

### Resposta `201 Created`

```json
{
  "wallet_id": "123456",
  "api_key": "sk_live_abc123"
}
```

### ⚠️ Observação

Esta rota deve ser chamada **apenas uma vez por instrutor**.

Caso o instrutor já possua uma subconta, a API retornará um erro `400`.

---

# 💳 Pagamentos

## Pagamento de Aula com Split

### `POST /lessons/{lesson_id}/pay`

Realiza o pagamento de uma aula com divisão automática dos valores:

* **90%** para o instrutor.
* **10%** para a plataforma BePilot.

O endpoint suporta:

* PIX
* Cartão de Crédito

---

## 🔑 Pagamento via PIX

### Body

```json
{
  "payment_method": "pix"
}
```

### Exemplo com cURL

```bash
curl --request POST \
  --url http://localhost:10000/api/v1/lessons/1/pay \
  --header 'Content-Type: application/json' \
  --data '{
    "payment_method": "pix"
  }'
```

---

## 💳 Pagamento via Cartão de Crédito

### Body

```json
{
  "payment_method": "credit_card",
  "credit_card": {
    "holderName": "João Silva",
    "number": "4111111111111111",
    "expiryMonth": "12",
    "expiryYear": "2030",
    "ccv": "123"
  },
  "credit_card_holder_info": {
    "name": "João Silva",
    "email": "joao@example.com",
    "cpfCnpj": "12345678900",
    "postalCode": "01001000",
    "addressNumber": "100",
    "phone": "11999999999"
  }
}
```

### Exemplo com cURL

```bash
curl --request POST \
  --url http://localhost:10000/api/v1/lessons/1/pay \
  --header 'Content-Type: application/json' \
  --data '{
    "payment_method": "credit_card",
    "credit_card": {
      "holderName": "João Silva",
      "number": "4111111111111111",
      "expiryMonth": "12",
      "expiryYear": "2030",
      "ccv": "123"
    },
    "credit_card_holder_info": {
      "name": "João Silva",
      "email": "joao@example.com",
      "cpfCnpj": "12345678900",
      "postalCode": "01001000",
      "addressNumber": "100",
      "phone": "11999999999"
    }
  }'
```

### Resposta

```json
{
  "success": true
}
```

### ⚠️ Pré-requisito

Antes de realizar o pagamento de uma aula, o instrutor vinculado precisa possuir uma subconta no Asaas.

Ou seja, o campo:

```text
asaas_wallet_id
```

deve estar preenchido.

Caso contrário, a API retornará um erro `400`.

---

# 🔎 Status de Pagamento

## Consultar Status de Pagamento

### `GET /lessons/{lesson_id}/payment-status`

Consulta o status atual do pagamento de uma aula.

### Exemplo com cURL

```bash
curl --request GET \
  --url http://localhost:10000/api/v1/lessons/1/payment-status
```

### Resposta

```json
{
  "status": "pending"
}
```

### Status possíveis

| Status      | Descrição           |
| ----------- | ------------------- |
| `paid`      | Pagamento realizado |
| `pending`   | Pagamento pendente  |
| `cancelled` | Pagamento cancelado |
| `refunded`  | Pagamento estornado |

---

# 👨‍🏫 Aulas do Instrutor

## Aulas Pagas

### `GET /instructors/{instructor_id}/lessons/paid`

Retorna todas as aulas pagas associadas ao instrutor.

### Exemplo com cURL

```bash
curl --request GET \
  --url http://localhost:10000/api/v1/instructors/1/lessons/paid
```

### Resposta

```json
[
  {
    "instructor_id": 1,
    "lesson_id": 2,
    "payment_status": "paid"
  }
]
```

---

## Aulas Não Pagas

### `GET /instructors/{instructor_id}/lessons/unpaid`

Retorna todas as aulas que ainda não foram pagas.

### Exemplo com cURL

```bash
curl --request GET \
  --url http://localhost:10000/api/v1/instructors/1/lessons/unpaid
```

### Resposta

```json
[
  {
    "instructor_id": 1,
    "lesson_id": 3,
    "payment_status": "pending"
  }
]
```

---

# 💸 Transferências

## Transferência (Payout)

### `POST /instructors/{instructor_id}/payout`

Realiza uma transferência manual para o instrutor.

> ℹ️ Esta funcionalidade continua disponível, mas **não é o foco principal desta atualização**, uma vez que os pagamentos já utilizam o sistema de split do Asaas.

### Body

```json
{
  "amount": 100.00
}
```

### Exemplo com cURL

```bash
curl --request POST \
  --url http://localhost:10000/api/v1/instructors/1/payout \
  --header 'Content-Type: application/json' \
  --data '{
    "amount": 100.00
  }'
```

### Resposta

```json
{
  "success": true,
  "transfer_id": "...",
  "amount": 100.00,
  "status": "pending"
}
```

---

# 💰 Saldo do Instrutor

## Consultar Saldo

### `GET /instructors/{instructor_id}/balance`

Consulta o saldo financeiro do instrutor.

### Exemplo com cURL

```bash
curl --request GET \
  --url http://localhost:10000/api/v1/instructors/1/balance
```

### Resposta

```json
{
  "total_earned": 0,
  "available_amount": 0,
  "pending_amount": 0
}
```

### Campos

| Campo              | Descrição                      |
| ------------------ | ------------------------------ |
| `total_earned`     | Total acumulado pelo instrutor |
| `available_amount` | Valor atualmente disponível    |
| `pending_amount`   | Valor ainda pendente           |

---

# ⚙️ Configuração

## Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Depois, preencha as variáveis de ambiente necessárias para o funcionamento da aplicação.

Exemplo:

```env
ASAAS_API_KEY=your_asaas_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

> ⚠️ Nunca versione o arquivo `.env` contendo credenciais reais.

---

# 🚀 Execução

## 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

## 2. Executar a Aplicação

```bash
python app.py
```

Após iniciar, a API estará disponível em:

```text
http://localhost:10000/api/v1
```

---

# 📋 Resumo dos Endpoints

| Método | Endpoint                           | Descrição                    |
| ------ | ---------------------------------- | ---------------------------- |
| `GET`  | `/health`                          | Verifica a saúde da API      |
| `POST` | `/customers`                       | Cria um Customer no Asaas    |
| `POST` | `/instructors/{id}/subaccount`     | Cria subconta do instrutor   |
| `POST` | `/lessons/{id}/pay`                | Realiza pagamento com Split  |
| `GET`  | `/lessons/{id}/payment-status`     | Consulta status do pagamento |
| `GET`  | `/instructors/{id}/lessons/paid`   | Lista aulas pagas            |
| `GET`  | `/instructors/{id}/lessons/unpaid` | Lista aulas não pagas        |
| `POST` | `/instructors/{id}/payout`         | Realiza transferência manual |
| `GET`  | `/instructors/{id}/balance`        | Consulta saldo do instrutor  |

---

# 🔄 Fluxo de Pagamento

O fluxo principal para pagamento de uma aula é:

```text
┌─────────────────────┐
│      Aluno          │
└──────────┬──────────┘
           │
           │ Pagamento da aula
           ▼
┌─────────────────────┐
│   BePayHub API      │
└──────────┬──────────┘
           │
           │ Criação do pagamento
           ▼
┌─────────────────────┐
│       Asaas         │
└──────────┬──────────┘
           │
           │ Split automático
           ▼
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌──────────────┐
│ BePilot │ │  Instrutor   │
│   10%   │ │     90%      │
└─────────┘ └──────────────┘
                 │
                 ▼
          Wallet Asaas
```

---

# ⚠️ Observações Importantes

### Subconta obrigatória

Para utilizar o sistema de **Split**, o instrutor precisa possuir uma subconta criada no Asaas.

O campo abaixo deve estar preenchido:

```text
instructor.asaas_wallet_id
```

### Divisão automática

A plataforma retém automaticamente **10%** do valor da aula.

Os **90% restantes** são direcionados para a wallet do instrutor.

### Saques

Não existem, nesta implementação, rotinas automáticas de saque ou transferência para conta bancária.

A funcionalidade de `payout` permanece disponível para transferências manuais.

### Segurança

As credenciais do Asaas e Supabase devem ser armazenadas exclusivamente em variáveis de ambiente.

Não coloque chaves de API diretamente no código-fonte ou no repositório Git.

---

# 🛠️ Tecnologias

* **Python**
* **REST API**
* **Asaas**
* **Supabase**
* **PostgreSQL**
* **JSON**
* **cURL**
* **Environment Variables**

---

# 📦 Integrações

## Asaas

Responsável por:

* Criação de Customers.
* Criação de subcontas.
* Geração de Wallets.
* Geração de API Keys.
* Processamento de pagamentos.
* Pagamentos via PIX.
* Pagamentos via Cartão.
* Split de pagamentos.
* Transferências.

## Supabase

Responsável por:

* Persistência dos dados.
* Consulta de usuários.
* Consulta de instrutores.
* Consulta de aulas.
* Armazenamento das informações relacionadas às contas Asaas.

---

# 📌 Regras de Negócio

1. Cada instrutor pode possuir apenas uma subconta Asaas.
2. A subconta do instrutor deve ser criada antes do pagamento da aula.
3. O instrutor deve ser MEI para criação da subconta.
4. Todo pagamento de aula deve utilizar o split configurado.
5. A plataforma recebe 10% do valor da aula.
6. O instrutor recebe 90% do valor da aula.
7. O pagamento pode ser realizado via PIX ou Cartão de Crédito.
8. O status do pagamento pode ser consultado posteriormente.
9. Aulas podem ser filtradas entre pagas e não pagas.
10. Transferências manuais podem ser realizadas através do endpoint de `payout`.

---

# 📁 Estrutura Conceitual

```text
BePayHub API
│
├── Controllers
│   └── Rotas HTTP
│
├── Services
│   ├── Regras de negócio
│   ├── Validações
│   └── Orquestração
│
├── Repositories
│   ├── Supabase
│   └── Asaas
│
├── Models
│   └── Estruturas de dados
│
├── DTOs
│   └── Objetos de transferência
│
├── app.py
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🧪 Exemplos de Fluxo

## 1. Criar subconta do instrutor

```bash
curl --request POST \
  --url http://localhost:10000/api/v1/instructors/1/subaccount
```

## 2. Realizar pagamento da aula

```bash
curl --request POST \
  --url http://localhost:10000/api/v1/lessons/1/pay \
  --header 'Content-Type: application/json' \
  --data '{
    "payment_method": "pix"
  }'
```

## 3. Consultar status

```bash
curl --request GET \
  --url http://localhost:10000/api/v1/lessons/1/payment-status
```

## 4. Consultar aulas pagas

```bash
curl --request GET \
  --url http://localhost:10000/api/v1/instructors/1/lessons/paid
```

## 5. Consultar saldo

```bash
curl --request GET \
  --url http://localhost:10000/api/v1/instructors/1/balance
```

---

# 📄 Licença

Este projeto faz parte do ecossistema **BePilot**.

---

## 📌 Versão

**Versão:** `2.1.0`
**Última atualização:** `26 de agosto de 2026`

---

# ✅ Considerações Finais

A **BePayHub API** foi estruturada para centralizar o gerenciamento de pagamentos da plataforma BePilot, utilizando o **Asaas** para processamento financeiro e o **Supabase** para persistência dos dados.

A implementação contempla:

* ✅ Criação de Customers.
* ✅ Criação de subcontas para instrutores.
* ✅ Wallets individuais no Asaas.
* ✅ Split automático de pagamentos.
* ✅ Retenção de 10% para a plataforma.
* ✅ Repasse de 90% para o instrutor.
* ✅ Pagamentos via PIX.
* ✅ Pagamentos via Cartão de Crédito.
* ✅ Consulta de status de pagamentos.
* ✅ Consulta de aulas pagas e não pagas.
* ✅ Consulta de saldo.
* ✅ Transferências manuais.
* ✅ Integração com Supabase.
* ✅ Integração com Asaas.

A API está preparada para ser integrada ao restante do ecossistema **BePilot**, mantendo uma arquitetura organizada, modular e orientada à separação de responsabilidades.

