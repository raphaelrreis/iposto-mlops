from __future__ import annotations

import argparse
import logging

import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from iposto_mlops.config import InferenceConfig
from iposto_mlops.schemas import MODEL_FEATURE_COLUMNS
from iposto_mlops.utils.exceptions import PipelineConfigurationError

LOGGER = logging.getLogger(__name__)

try:
    import mlflow.pyfunc
except ImportError as import_error:  # pragma: no cover - environment-dependent
    mlflow = None
    OPTIONAL_ML_IMPORT_ERROR = import_error
else:
    OPTIONAL_ML_IMPORT_ERROR = None

IDENTIFIER_COLUMNS = [
    "effective_date",
    "country_code",
    "fuel_type",
    "brand",
    "geohash",
]


def _latest_snapshot(gold_dataset: DataFrame) -> DataFrame:
    max_date = gold_dataset.select(F.max("effective_date").alias("max_date")).collect()[0]["max_date"]
    if max_date is None:
        raise PipelineConfigurationError("Gold dataset does not contain any effective_date values.")
    return gold_dataset.filter(F.col("effective_date") == F.lit(max_date))


def score_latest_snapshot(
    spark: SparkSession,
    input_path: str,
    output_path: str,
    model_uri: str,
    input_format: str = "parquet",
    output_format: str = "parquet",
) -> DataFrame:
    gold_dataset = spark.read.format(input_format).load(input_path)
    snapshot = _latest_snapshot(gold_dataset).select(*IDENTIFIER_COLUMNS, *MODEL_FEATURE_COLUMNS)
    feature_frame = snapshot.select(*MODEL_FEATURE_COLUMNS).toPandas()
    if feature_frame.empty:
        raise PipelineConfigurationError("No rows available for batch inference.")
    if OPTIONAL_ML_IMPORT_ERROR is not None:
        raise PipelineConfigurationError(
            "ML dependencies are missing. Install iposto-mlops with the [ml] extra."
        ) from OPTIONAL_ML_IMPORT_ERROR

    model = mlflow.pyfunc.load_model(model_uri)
    predictions = model.predict(feature_frame)

    output_frame = snapshot.select(*IDENTIFIER_COLUMNS).toPandas()
    output_frame["prediction_for_date"] = pd.to_datetime(output_frame["effective_date"]) + pd.Timedelta(
        days=1
    )
    output_frame["predicted_price_next_day"] = predictions
    output_frame["model_uri"] = model_uri

    prediction_dataset = spark.createDataFrame(output_frame)
    prediction_dataset.write.mode("overwrite").format(output_format).save(output_path)
    return prediction_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Run batch inference for iposto-mlops.")
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--model-uri", default=InferenceConfig().model_uri)
    parser.add_argument("--input-format", default="parquet")
    parser.add_argument("--output-format", default="parquet")
    args = parser.parse_args()

    spark = SparkSession.builder.appName("iposto-mlops-batch-inference").getOrCreate()
    try:
        prediction_dataset = score_latest_snapshot(
            spark=spark,
            input_path=args.input_path,
            output_path=args.output_path,
            model_uri=args.model_uri,
            input_format=args.input_format,
            output_format=args.output_format,
        )
        LOGGER.info("Wrote %s prediction rows.", prediction_dataset.count())
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
