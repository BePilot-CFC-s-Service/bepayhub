from repositories.supabase_repository import SupabaseRepository
from repositories.asaas_repository import AsaasRepository
from errors import ValidationError, NotFoundError
from utils.validators import validate_required_fields

class CustomerService:
    def __init__(self):
        self.supabase = SupabaseRepository
        self.asaas = AsaasRepository

    def create_customer(self, data: dict) -> str:
        """Cria customer no Asaas e atualiza o usuário correspondente."""
        validate_required_fields(data, ["user_type", "user_id"])

        user_type = data["user_type"].lower()
        user_id = data["user_id"]

        if user_type not in ("student", "instructor"):
            raise ValidationError("user_type deve ser 'student' ou 'instructor'", 400)

        # Busca usuário no Supabase
        user_data = self.supabase.fetch_one(user_type, {"id": user_id})
        if not user_data:
            raise NotFoundError(f"{user_type.capitalize()} não encontrado", 404)

        # Monta payload para Asaas
        customer_payload = {
            "name": f"{user_data['name']} {user_data.get('last_name', '')}".strip(),
            "cpfCnpj": user_data["cpf"],
            "email": user_data["email"],
            "phone": user_data["phone"],
        }

        # Adiciona endereço se existir
        address = self.supabase.fetch_one("address", {
            "owner_id": user_id,
            "owner_type": user_type.capitalize()
        })
        if address:
            customer_payload.update({
                "address": address.get("street"),
                "addressNumber": address.get("number"),
                "city": address.get("city"),
                "state": address.get("state"),
                "postalCode": address.get("zip_code"),
            })

        # Cria customer no Asaas
        asaas_response = self.asaas.create_customer(customer_payload)
        asaas_customer_id = asaas_response["id"]

        # Atualiza usuário no Supabase com o customer ID
        self.supabase.update(
            user_type,
            {"id": user_id},
            {"bepayhub_customer_id": asaas_customer_id}
        )

        return asaas_customer_id