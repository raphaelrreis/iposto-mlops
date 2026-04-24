from __future__ import annotations

import logging
from typing import Iterable

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.column import Column
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from iposto_mlops.pipelines.bronze import load_bronze_dataset
from iposto_mlops.validation.quality import enforce_minimum_rows, summarize_quality

LOGGER = logging.getLogger(__name__)

PRICE_BOUNDS: dict[tuple[str, str], tuple[float, float]] = {
    ("BR", "GASOLINE"): (3.0, 10.0),
    ("BR", "DIESEL"): (3.0, 9.0),
    ("BR", "ETHANOL"): (2.0, 8.0),
    ("US", "GASOLINE"): (2.0, 7.0),
    ("US", "DIESEL"): (2.0, 8.0),
}


def _build_price_guard() -> Column:
    guard: Column | None = None
    for (country_code, fuel_type), (min_price, max_price) in PRICE_BOUNDS.items():
        condition = (
            (F.col("country_code") == country_code)
            & (F.col("fuel_type") == fuel_type)
            & F.col("price").between(min_price, max_price)
        )
        guard = condition if guard is None else guard | condition

    if guard is None:
        raise ValueError("At least one price guard must be configured.")
    return guard


def _normalize_required_columns(dataset: DataFrame, columns: Iterable[str]) -> DataFrame:
    current = dataset
    for column_name in columns:
        current = current.withColumn(column_name, F.trim(F.upper(F.col(column_name))))
    return current


def transform_bronze_to_silver(bronze_dataset: DataFrame) -> DataFrame:
    required_columns = [
        "country_code",
        "region_code",
        "station_id",
        "brand",
        "fuel_type",
        "currency",
        "source_api",
    ]
    normalized = _normalize_required_columns(bronze_dataset, required_columns)
    typed = (
        normalized.withColumn("effective_date", F.to_date("effective_date"))
        .withColumn("collected_at_ts", F.to_timestamp("collected_at"))
        .withColumn("city", F.initcap(F.trim(F.col("city"))))
        .withColumn("event_id", F.trim(F.col("event_id")))
    )

    filtered = typed.dropna(
        subset=[
            "event_id",
            "effective_date",
            "collected_at_ts",
            "price",
            "latitude",
            "longitude",
        ]
    )

    dedupe_window = Window.partitionBy("event_id").orderBy(F.col("collected_at_ts").desc())
    deduplicated = (
        filtered.withColumn("row_number", F.row_number().over(dedupe_window))
        .filter(F.col("row_number") == 1)
        .drop("row_number")
    )

    silver_dataset = (
        deduplicated.filter(_build_price_guard())
        .withColumn("ingested_at", F.current_timestamp())
        .select(
            "event_id",
            "country_code",
            "region_code",
            "city",
            "station_id",
            "brand",
            "fuel_type",
            "currency",
            "price",
            "tax_percent",
            "latitude",
            "longitude",
            "effective_date",
            "collected_at_ts",
            "source_api",
            "ingested_at",
        )
    )

    summary = summarize_quality(silver_dataset)
    LOGGER.info("Silver summary: %s", summary)
    enforce_minimum_rows(silver_dataset, minimum_rows=1)
    return silver_dataset


def run_silver_pipeline(
    spark: SparkSession,
    input_path: str,
    output_path: str,
    input_format: str = "json",
    output_format: str = "parquet",
) -> DataFrame:
    bronze_dataset = load_bronze_dataset(
        spark=spark,
        input_path=input_path,
        input_format=input_format,
    )
    silver_dataset = transform_bronze_to_silver(bronze_dataset)
    silver_dataset.write.mode("overwrite").format(output_format).save(output_path)
    return silver_dataset
