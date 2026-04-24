from __future__ import annotations

import logging

import geohash2
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from pyspark.sql.window import Window

LOGGER = logging.getLogger(__name__)


def _encode_geohash(latitude, longitude):
    if latitude is None or longitude is None:
        return None
    return geohash2.encode(latitude, longitude, precision=5)


geohash_udf = F.udf(_encode_geohash, StringType())


def build_gold_features(silver_dataset: DataFrame) -> DataFrame:
    grouped = (
        silver_dataset.withColumn("geohash", geohash_udf("latitude", "longitude"))
        .groupBy("effective_date", "country_code", "fuel_type", "brand", "geohash")
        .agg(
            F.avg("price").alias("avg_price"),
            F.stddev_pop("price").alias("station_price_stddev"),
            F.countDistinct("station_id").alias("stations_count"),
        )
    )

    partition_columns = ["country_code", "fuel_type", "brand", "geohash"]
    ordered_window = Window.partitionBy(*partition_columns).orderBy("effective_date")
    rolling_7d_window = ordered_window.rowsBetween(-6, 0)
    rolling_30d_window = ordered_window.rowsBetween(-29, 0)

    gold_dataset = (
        grouped.withColumn("moving_avg_7d", F.avg("avg_price").over(rolling_7d_window))
        .withColumn("moving_avg_30d", F.avg("avg_price").over(rolling_30d_window))
        .withColumn("volatility_7d", F.stddev_pop("avg_price").over(rolling_7d_window))
        .withColumn("lag_1d_price", F.lag("avg_price", 1).over(ordered_window))
        .withColumn(
            "target_next_day_price",
            F.lead("avg_price", 1).over(ordered_window),
        )
        .withColumn("day_of_week", F.dayofweek("effective_date"))
        .withColumn("is_weekend", F.when(F.dayofweek("effective_date").isin(1, 7), 1).otherwise(0))
        .fillna({"station_price_stddev": 0.0, "volatility_7d": 0.0})
    )

    LOGGER.info("Gold dataset created with %s rows.", gold_dataset.count())
    return gold_dataset


def run_gold_pipeline(
    spark: SparkSession,
    input_path: str,
    output_path: str,
    input_format: str = "parquet",
    output_format: str = "parquet",
) -> DataFrame:
    silver_dataset = spark.read.format(input_format).load(input_path)
    gold_dataset = build_gold_features(silver_dataset)
    gold_dataset.write.mode("overwrite").format(output_format).save(output_path)
    return gold_dataset
