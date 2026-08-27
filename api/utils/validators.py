
from errors import ValidationError

def validate_required_fields(data: dict, fields: list) -> None:
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValidationError(
            "Campos obrigatórios ausentes",
            status_code=400,
            details={"missing": missing},
        )
