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
        if not interp.indexCase:
            raise MetadataValidationError(
                f"Interpretation '{interp.title}' has no index case"
            )
        for data in interp.datas:
            dataset_indexes = [s for s in data.samples if s.isDatasetIndex]
            if len(dataset_indexes) > 1:
                raise MetadataValidationError(
                    f"DataBlock '{data.title}' in interpretation '{interp.title}' "
                    f"has multiple isDatasetIndex samples"
                )
