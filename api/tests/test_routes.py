from errors import ServiceIntegrationError


API_PREFIX = "/api/v1"


def test_given_valid_pix_payment_when_creating_student_payment_then_returns_200(
    client, monkeypatch
):
    def fake_create_payment(payload):
        assert payload["billingType"] == "PIX"
        assert payload["externalReference"] == "studentPayment"
        return {"id": "pay_123"}, 200

    def fake_get_payment_billing_info(payment_id: str):
        assert payment_id == "pay_123"
        return {"pix": {"payload": "000201..."}}, 200

    monkeypatch.setattr(
        "api.repositories.payment_repository.create_payment",
        fake_create_payment,
    )

    monkeypatch.setattr(
        "api.repositories.payment_repository.get_payment_billing_info",
        fake_get_payment_billing_info,
    )

    response = client.post(
        f"{API_PREFIX}/payments/student/driving-lessons/pix",
        json={
            "customer_id": "cus_1",
            "value": 100,
            "due_date": "2026-04-10",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["id"] == "pay_123"
    assert response.get_json()["pix"]["payload"] == "000201..."


def test_given_invalid_payment_method_when_creating_student_payment_then_returns_400(
    client,
):
    response = client.post(
        f"{API_PREFIX}/payments/student/driving-lessons/bitcoin",
        json={
            "customer_id": "cus_1",
            "value": 100,
            "due_date": "2026-04-10",
        },
    )

    assert response.status_code == 400


def test_given_credit_payment_without_card_data_when_creating_student_payment_then_returns_400(
    client,
):
    response = client.post(
        f"{API_PREFIX}/payments/student/driving-lessons/credit",
        json={
            "customer_id": "cus_1",
            "value": 100,
            "due_date": "2026-04-10",
        },
    )

    assert response.status_code == 400


def test_given_invalid_origin_when_listing_payments_then_returns_400(client):
    response = client.get(f"{API_PREFIX}/payments/otherOrigin")
    assert response.status_code == 400


def test_given_student_origin_with_filters_when_listing_payments_then_builds_expected_query(
    client, monkeypatch
):
    captured = {}

    def fake_list_payments(external_reference=None, extra_params=None):
        captured["external_reference"] = external_reference
        captured["extra_params"] = extra_params
        return {"data": []}, 200

    monkeypatch.setattr(
        "api.repositories.payment_repository.list_payments",
        fake_list_payments,
    )

    response = client.get(
        f"{API_PREFIX}/payments/student?student_id=stu_10&lesson_id=les_90&status=PENDING"
    )

    assert response.status_code == 200
    assert captured["external_reference"] == "studentPayment:student=stu_10:lesson=les_90"
    assert captured["extra_params"] == {"status": "PENDING"}


def test_given_valid_customer_payload_when_creating_customer_then_returns_200(
    client, monkeypatch
):
    monkeypatch.setattr(
        "api.repositories.payment_repository.create_customer",
        lambda payload: ({"id": "cus_123", **payload}, 200),
    )

    response = client.post(
        f"{API_PREFIX}/customers",
        json={
            "name": "Joao",
            "cpf_cnpj": "12345678900",
            "email": "joao@email.com",
            "mobile_phone": "11999999999",
            "external_reference": {"student_id": 10},
        },
    )

    assert response.status_code == 200
    assert response.get_json()["id"] == "cus_123"


def test_given_asaas_timeout_when_creating_instructor_monthly_fee_then_returns_504(
    client, monkeypatch
):
    def fake_create_subscription(_payload):
        raise ServiceIntegrationError(
            "Tempo limite excedido na integracao com Asaas", status_code=504
        )

    monkeypatch.setattr(
        "api.repositories.payment_repository.create_subscription",
        fake_create_subscription,
    )

    response = client.post(
        f"{API_PREFIX}/payments/instructor/monthly-fees",
        json={
            "customer_id": "cus_1",
            "value": 99.9,
            "due_date": "2026-04-10",
            "creditCard": {
                "holderName": "Nome",
                "number": "4111111111111111",
                "expiryMonth": "12",
                "expiryYear": "2030",
                "ccv": "123",
            },
            "creditCardHolderInfo": {
                "name": "Nome",
                "email": "email@dominio.com",
                "cpfCnpj": "12345678900",
                "postalCode": "01001000",
                "addressNumber": "100",
                "phone": "11999999999",
            },
        },
    )

    assert response.status_code == 504


def test_given_monthly_fee_without_card_fields_when_creating_instructor_monthly_fee_then_returns_400(
    client,
):
    response = client.post(
        f"{API_PREFIX}/payments/instructor/monthly-fees",
        json={
            "customer_id": "cus_1",
            "value": 99.9,
            "due_date": "2026-04-10",
        },
    )

    assert response.status_code == 400


def test_openapi_json_is_available(client):
    response = client.get(f"{API_PREFIX}/openapi.json")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["openapi"].startswith("3.")
    assert "/customers" in payload["paths"]


def test_swagger_ui_is_available(client):
    response = client.get(f"{API_PREFIX}/docs/")

    assert response.status_code == 200
