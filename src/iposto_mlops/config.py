from __future__ import annotations

import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y"}


@dataclass(slots=True)
class StorageConfig:
    bronze_path: str = os.getenv("IPOSTO_BRONZE_PATH", "data/bronze/fuel_prices")
    silver_path: str = os.getenv("IPOSTO_SILVER_PATH", "data/silver/fuel_prices")
    gold_path: str = os.getenv("IPOSTO_GOLD_PATH", "data/gold/fuel_price_features")
    predictions_path: str = os.getenv("IPOSTO_PREDICTIONS_PATH", "data/gold/predictions")


@dataclass(slots=True)
class TrainingConfig:
    tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "databricks")
    registry_uri: str | None = os.getenv("MLFLOW_REGISTRY_URI")
    experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "/Shared/iposto-mlops")
    registered_model_name: str = os.getenv(
        "IPOSTO_REGISTERED_MODEL_NAME",
        "iposto_mlops_next_day_price",
    )
    validation_ratio: float = float(os.getenv("IPOSTO_VALIDATION_RATIO", "0.2"))
    random_state: int = int(os.getenv("IPOSTO_RANDOM_STATE", "42"))
    n_estimators: int = int(os.getenv("IPOSTO_XGB_N_ESTIMATORS", "300"))
    max_depth: int = int(os.getenv("IPOSTO_XGB_MAX_DEPTH", "6"))
    learning_rate: float = float(os.getenv("IPOSTO_XGB_LEARNING_RATE", "0.05"))
    subsample: float = float(os.getenv("IPOSTO_XGB_SUBSAMPLE", "0.9"))
    colsample_bytree: float = float(os.getenv("IPOSTO_XGB_COLSAMPLE_BYTREE", "0.8"))
    register_model: bool = _get_bool("IPOSTO_REGISTER_MODEL", True)
    promote_to: str = os.getenv("IPOSTO_PROMOTE_TO", "Staging")


@dataclass(slots=True)
class InferenceConfig:
    model_uri: str = os.getenv(
        "IPOSTO_MODEL_URI",
        "models:/iposto_mlops_next_day_price/Staging",
    )
