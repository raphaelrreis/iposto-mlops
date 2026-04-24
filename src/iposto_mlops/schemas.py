from __future__ import annotations

from pyspark.sql.types import DoubleType, StringType, StructField, StructType

BRONZE_JSON_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), nullable=False),
        StructField("country_code", StringType(), nullable=False),
        StructField("region_code", StringType(), nullable=False),
        StructField("city", StringType(), nullable=False),
        StructField("station_id", StringType(), nullable=False),
        StructField("brand", StringType(), nullable=False),
        StructField("fuel_type", StringType(), nullable=False),
        StructField("currency", StringType(), nullable=False),
        StructField("price", DoubleType(), nullable=False),
        StructField("tax_percent", DoubleType(), nullable=True),
        StructField("latitude", DoubleType(), nullable=False),
        StructField("longitude", DoubleType(), nullable=False),
        StructField("effective_date", StringType(), nullable=False),
        StructField("collected_at", StringType(), nullable=False),
        StructField("source_api", StringType(), nullable=False),
    ]
)

MODEL_FEATURE_COLUMNS = [
    "country_code",
    "fuel_type",
    "brand",
    "geohash",
    "avg_price",
    "moving_avg_7d",
    "moving_avg_30d",
    "volatility_7d",
    "lag_1d_price",
    "stations_count",
    "day_of_week",
    "is_weekend",
]

CATEGORICAL_FEATURE_COLUMNS = ["country_code", "fuel_type", "brand", "geohash"]

NUMERIC_FEATURE_COLUMNS = [
    feature
    for feature in MODEL_FEATURE_COLUMNS
    if feature not in CATEGORICAL_FEATURE_COLUMNS
]
