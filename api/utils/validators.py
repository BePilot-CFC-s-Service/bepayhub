
from errors import ValidationError

def normalize_phone(value) -> str:
    phone = "".join(character for character in str(value or "") if "0" <= character <= "9")
    if len(phone) not in (10, 11):
        raise ValidationError("Telefone cadastrado deve conter DDD e 10 ou 11 dígitos", status_code=400)
    return phone

def validate_required_fields(data: dict, fields: list) -> None:
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValidationError(
            "Campos obrigatórios ausentes",
            status_code=400,
            details={"missing": missing},
        )
