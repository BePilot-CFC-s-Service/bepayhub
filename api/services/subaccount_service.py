from repositories.supabase_repository import SupabaseRepository
from repositories.asaas_repository import AsaasRepository
from errors import ValidationError, NotFoundError, IntegrationError

class SubaccountService:
    def __init__(self):
        self.supabase = SupabaseRepository
        self.asaas = AsaasRepository

    @staticmethod
    def _generate_alias_email(email: str) -> str:
        """
        Gera um e-mail alias para evitar conflito de cadastro no Asaas.
        Exemplo: instrutor@gmail.com -> instrutor+bepilot@gmail.com
        Funciona com Gmail e Outlook (mensagens chegam na mesma caixa).
        """
        if not email or "@" not in email:
            return email
        local, domain = email.split("@", 1)
        # Se já possui alias, retorna sem duplicar
        if "+bepilot" in local:
            return email
        return f"{local}+bepilot@{domain}"

    def create_subaccount(self, instructor_id: int) -> dict:
        """
        Cria uma subconta (wallet) no Asaas para o instrutor.
        O instrutor deve ser MEI (Pessoa Jurídica) e possuir CNPJ válido.
        Utiliza um alias de e-mail para reutilizar o mesmo endereço sem conflitos.
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

        # Gera alias de e-mail para evitar duplicidade no Asaas
        alias_email = self._generate_alias_email(instructor["email"])

        # Busca endereço do instrutor
        address = self.supabase.fetch_one("address", {
            "owner_id": instructor_id,
            "owner_type": "Instructor"
        })
        if not address:
            address = {}

        # Monta payload base (campos obrigatórios para MEI)
        payload = {
            "name": f"{instructor['name']} {instructor.get('last_name', '')}".strip(),
            "email": alias_email,
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

        # Adiciona endereço se disponível
        if address:
            payload.update({
                "address": address.get("street"),
                "addressNumber": address.get("number"),
                "complement": address.get("complement", ""),
                "province": address.get("province", ""),
                "postalCode": address.get("zip_code"),
                "city": address.get("city"),
                "state": address.get("state"),
            })

        # Chama API Asaas para criar subconta
        asaas_response = self.asaas.create_subaccount(payload)

        # Extrai walletId e apiKey da resposta
        wallet_id = asaas_response.get("id")
        api_key = asaas_response.get("apiKey")
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