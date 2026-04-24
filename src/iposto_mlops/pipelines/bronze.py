from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession

from iposto_mlops.schemas import BRONZE_JSON_SCHEMA


def load_bronze_dataset(
    spark: SparkSession,
    input_path: str,
    input_format: str = "json",
) -> DataFrame:
    if input_format == "json":
        return spark.read.schema(BRONZE_JSON_SCHEMA).json(input_path)

    return spark.read.format(input_format).load(input_path)
