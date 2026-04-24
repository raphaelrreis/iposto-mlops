from __future__ import annotations

from dataclasses import dataclass

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from iposto_mlops.utils.exceptions import DataQualityError


@dataclass(slots=True)
class ValidationSummary:
    total_rows: int
    null_price_rows: int
    duplicate_event_ids: int
    distinct_stations: int


def summarize_quality(dataset: DataFrame) -> ValidationSummary:
    total_rows = dataset.count()
    null_price_rows = dataset.filter(F.col("price").isNull()).count()
    duplicate_event_ids = (
        dataset.groupBy("event_id")
        .count()
        .filter(F.col("count") > 1)
        .count()
    )
    distinct_stations = dataset.select("station_id").distinct().count()

    return ValidationSummary(
        total_rows=total_rows,
        null_price_rows=null_price_rows,
        duplicate_event_ids=duplicate_event_ids,
        distinct_stations=distinct_stations,
    )


def enforce_minimum_rows(dataset: DataFrame, minimum_rows: int) -> None:
    row_count = dataset.count()
    if row_count < minimum_rows:
        raise DataQualityError(
            f"Dataset below minimum row threshold: expected {minimum_rows}, got {row_count}."
        )
