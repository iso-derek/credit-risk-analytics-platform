import pandas as pd

from src.data_quality import duplicate_count, missing_columns, prepare_credit_dataset, validate_credit_dataset


def test_missing_columns_reports_required_fields() -> None:
    assert "default" in missing_columns(pd.DataFrame({"application_id": ["A1"]}))


def test_prepare_credit_dataset_adds_application_id_and_required_columns() -> None:
    prepared = prepare_credit_dataset(pd.DataFrame({"age": [35]}))
    assert "application_id" in prepared.columns
    assert "default" in prepared.columns
    assert len(prepared) == 1


def test_duplicate_count_detects_duplicate_application_ids() -> None:
    df = pd.DataFrame({"application_id": ["A1", "A1", "A2"]})
    assert duplicate_count(df) == 1


def test_validate_credit_dataset_returns_warnings() -> None:
    warnings = validate_credit_dataset(pd.DataFrame({"application_id": ["A1", "A1"]}))
    assert warnings
