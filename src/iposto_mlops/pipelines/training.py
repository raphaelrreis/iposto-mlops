from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass

import pandas as pd
from pyspark.sql import DataFrame, SparkSession

from iposto_mlops.config import TrainingConfig
from iposto_mlops.schemas import (
    CATEGORICAL_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
)
from iposto_mlops.utils.exceptions import PipelineConfigurationError

LOGGER = logging.getLogger(__name__)

try:
    import mlflow
    import mlflow.sklearn
    from mlflow.models import infer_signature
    from mlflow.tracking import MlflowClient
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    from xgboost import XGBRegressor
except ImportError as import_error:  # pragma: no cover - environment-dependent
    mlflow = None
    MlflowClient = None
    infer_signature = None
    ColumnTransformer = None
    OneHotEncoder = None
    SimpleImputer = None
    mean_squared_error = None
    r2_score = None
    Pipeline = None
    XGBRegressor = None
    OPTIONAL_ML_IMPORT_ERROR = import_error
else:
    OPTIONAL_ML_IMPORT_ERROR = None


@dataclass(slots=True)
class TrainingOutcome:
    run_id: str
    rmse: float
    r2: float
    registered_model_version: str | None


def _configure_mlflow(config: TrainingConfig) -> None:
    if mlflow is None:
        raise PipelineConfigurationError(
            "ML dependencies are missing. Install iposto-mlops with the [ml] extra."
        ) from OPTIONAL_ML_IMPORT_ERROR
    mlflow.set_tracking_uri(config.tracking_uri)
    if config.registry_uri:
        mlflow.set_registry_uri(config.registry_uri)
    mlflow.set_experiment(config.experiment_name)


def _load_training_frame(gold_dataset: DataFrame) -> pd.DataFrame:
    selected = (
        gold_dataset.select(*MODEL_FEATURE_COLUMNS, "target_next_day_price", "effective_date")
        .dropna(
            subset=[
                "target_next_day_price",
                "avg_price",
                "moving_avg_7d",
                "moving_avg_30d",
                "lag_1d_price",
            ]
        )
        .orderBy("effective_date")
    )
    return selected.toPandas()


def _split_train_validation(
    training_frame: pd.DataFrame,
    validation_ratio: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if training_frame.empty:
        raise PipelineConfigurationError("Training dataset is empty after feature preparation.")

    if len(training_frame) < 10:
        raise PipelineConfigurationError(
            "At least 10 training rows are required for a stable split."
        )

    split_index = max(1, int(len(training_frame) * (1 - validation_ratio)))
    if split_index >= len(training_frame):
        split_index = len(training_frame) - 1

    return (
        training_frame.iloc[:split_index].copy(),
        training_frame.iloc[split_index:].copy(),
    )


def _build_model_pipeline(config: TrainingConfig) -> Pipeline:
    if ColumnTransformer is None or Pipeline is None or XGBRegressor is None:
        raise PipelineConfigurationError(
            "ML dependencies are missing. Install iposto-mlops with the [ml] extra."
        ) from OPTIONAL_ML_IMPORT_ERROR

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                CATEGORICAL_FEATURE_COLUMNS,
            ),
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                NUMERIC_FEATURE_COLUMNS,
            ),
        ],
        remainder="drop",
    )

    regressor = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=config.n_estimators,
        max_depth=config.max_depth,
        learning_rate=config.learning_rate,
        subsample=config.subsample,
        colsample_bytree=config.colsample_bytree,
        random_state=config.random_state,
    )

    return Pipeline(steps=[("preprocessor", preprocessor), ("regressor", regressor)])


def _latest_model_version(client: MlflowClient, registered_model_name: str) -> str | None:
    versions = client.search_model_versions(f"name = '{registered_model_name}'")
    if not versions:
        return None
    latest = max(versions, key=lambda version: int(version.version))
    return str(latest.version)


def train_model(
    gold_dataset: DataFrame,
    config: TrainingConfig | None = None,
) -> TrainingOutcome:
    effective_config = config or TrainingConfig()
    _configure_mlflow(effective_config)

    training_frame = _load_training_frame(gold_dataset)
    train_frame, validation_frame = _split_train_validation(
        training_frame=training_frame,
        validation_ratio=effective_config.validation_ratio,
    )

    feature_frame_train = train_frame[MODEL_FEATURE_COLUMNS]
    feature_frame_validation = validation_frame[MODEL_FEATURE_COLUMNS]
    target_train = train_frame["target_next_day_price"]
    target_validation = validation_frame["target_next_day_price"]

    pipeline = _build_model_pipeline(effective_config)
    mlflow.sklearn.autolog(log_models=False)

    with mlflow.start_run(run_name="iposto-mlops-training") as run:
        pipeline.fit(feature_frame_train, target_train)

        predictions = pipeline.predict(feature_frame_validation)
        rmse = float(mean_squared_error(target_validation, predictions, squared=False))
        r2 = float(r2_score(target_validation, predictions))

        mlflow.log_metrics({"rmse": rmse, "r2": r2})
        mlflow.log_dict(
            {
                "model_features": MODEL_FEATURE_COLUMNS,
                "categorical_features": CATEGORICAL_FEATURE_COLUMNS,
                "numeric_features": NUMERIC_FEATURE_COLUMNS,
            },
            "artifacts/feature_spec.json",
        )

        signature = infer_signature(feature_frame_validation, predictions)
        mlflow.sklearn.log_model(
            sk_model=pipeline,
            artifact_path="model",
            registered_model_name=(
                effective_config.registered_model_name
                if effective_config.register_model
                else None
            ),
            signature=signature,
            input_example=feature_frame_train.head(5),
        )

        registered_model_version: str | None = None
        if effective_config.register_model:
            client = MlflowClient()
            registered_model_version = _latest_model_version(
                client=client,
                registered_model_name=effective_config.registered_model_name,
            )
            if registered_model_version and effective_config.promote_to:
                client.transition_model_version_stage(
                    name=effective_config.registered_model_name,
                    version=registered_model_version,
                    stage=effective_config.promote_to,
                    archive_existing_versions=effective_config.promote_to.lower() == "production",
                )

        LOGGER.info("Training completed with rmse=%s r2=%s", rmse, r2)
        return TrainingOutcome(
            run_id=run.info.run_id,
            rmse=rmse,
            r2=r2,
            registered_model_version=registered_model_version,
        )


def train_model_from_path(
    spark: SparkSession,
    input_path: str,
    input_format: str = "parquet",
    config: TrainingConfig | None = None,
) -> TrainingOutcome:
    gold_dataset = spark.read.format(input_format).load(input_path)
    return train_model(gold_dataset=gold_dataset, config=config)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train the iposto-mlops price forecasting model."
    )
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--input-format", default="parquet")
    args = parser.parse_args()

    spark = SparkSession.builder.appName("iposto-mlops-train-model").getOrCreate()
    try:
        outcome = train_model_from_path(
            spark=spark,
            input_path=args.input_path,
            input_format=args.input_format,
        )
        LOGGER.info("Training outcome: %s", outcome)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
