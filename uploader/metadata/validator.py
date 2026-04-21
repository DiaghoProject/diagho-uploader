from pydantic import ValidationError
from .payload_schema import MetadataPayload


class MetadataValidationError(Exception):
    pass


def validate_payload(payload: dict) -> dict:
    try:
        model = MetadataPayload.model_validate(payload)
    except ValidationError as e:
        raise MetadataValidationError(str(e)) from e

    # business rules not expressible in schema
    enforce_rules(model)

    return model.model_dump(mode="json", exclude_none=True)


def enforce_rules(model: MetadataPayload):
    for interp in model.interpretations:
        indexes = [
            s for d in interp.datas for s in d.samples if s.isAffected
        ]
        if not indexes:
            raise MetadataValidationError(
                f"Interpretation '{interp.title}' has no index case"
            )
