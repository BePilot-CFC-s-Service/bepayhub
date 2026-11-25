from repositories.supabase_repository import SupabaseRepository
from repositories.asaas_repository import AsaasRepository
from errors import ValidationError, NotFoundError, IntegrationError

class SubaccountService:
    def __init__(self):
        self.supabase = SupabaseRepository
        self.asaas = AsaasRepository

    def create_subaccount(self, instructor_id: int) -> dict:
        """
        Cria uma subconta (wallet) no Asaas para o instrutor.
        O instrutor deve ser MEI (Pessoa Jurídica) e possuir CNPJ válido.
        """
        # Busca instrutor no Supabase
        instructor = self.supabase.fetch_one("instructor", {"id": instructor_id})
        if not instructor:
            raise NotFoundError("Instrutor não encontrado", 404)

        # Verifica se já possui subconta
        if instructor.get("asaas_wallet_id"):
            raise ValidationError("Instrutor já possui subconta (wallet)", 400)

        # Valida se possui CNPJ para MEI
        cnpj = instructor.get("cnpj")
        if not cnpj:
            raise ValidationError(
                "Instrutor não possui CNPJ cadastrado. Necessário para criação de subconta MEI.",
                400
            )

        # Monta payload base (campos obrigatórios para MEI)
        payload = {
            "name": f"{instructor['name']} {instructor.get('last_name', '')}".strip(),
            "email": instructor["email"],
            "cpfCnpj": cnpj,
            "phone": instructor.get("phone", ""),
            "mobilePhone": instructor.get("phone", ""),  # Asaas exige mobilePhone
            "companyType": "MEI",
        }

        # Adiciona birthDate somente se existir (não obrigatório para MEI)
        if instructor.get("birth_date"):
            payload["birthDate"] = instructor["birth_date"]

        # Adiciona incomeValue somente se existir (campo opcional)
        if instructor.get("incomeValue") is not None:
            payload["incomeValue"] = instructor["incomeValue"]

        # Adiciona endereço se disponível (colunas de endereço ficam na própria linha do instrutor)
        if instructor.get("street"):
            payload.update({
                "address": instructor.get("street"),
                "addressNumber": instructor.get("number"),
                "complement": instructor.get("complement") or "",
                "province": instructor.get("province", ""),
                "postalCode": instructor.get("zip_code"),
                "city": instructor.get("city"),
                "state": instructor.get("state"),
            })

        # Chama API Asaas para criar subconta
        asaas_response = self.asaas.create_subaccount(payload)

        # O id identifica a subconta; walletId é usado em splits e transferências.
        wallet_id = asaas_response.get("walletId")
        access_token = asaas_response.get("accessToken")
        api_key = (
            access_token.get("apiKey")
            if isinstance(access_token, dict)
            else None
        ) or asaas_response.get("apiKey")
        if not wallet_id or not api_key:
            raise IntegrationError("Resposta inválida da Asaas ao criar subconta", 500)

        # Atualiza instrutor no Supabase com os novos dados
        self.supabase.update(
            "instructor",
            {"id": instructor_id},
            {
                "asaas_wallet_id": wallet_id,
                "asaas_api_key": api_key,
            }
        )

        return {
            "wallet_id": wallet_id,
            "api_key": api_key,
        }