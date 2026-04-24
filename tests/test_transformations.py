from __future__ import annotations

from pyspark.sql import Row
from pyspark.sql import functions as F

from iposto_mlops.pipelines.gold import build_gold_features
from iposto_mlops.pipelines.silver import transform_bronze_to_silver


def test_transform_bronze_to_silver_filters_outliers_and_deduplicates(spark) -> None:
    bronze_rows = [
        Row(
            event_id="evt-1",
            country_code="br",
            region_code="df",
            city="brasilia",
            station_id="br-001",
            brand="ipiranga",
            fuel_type="gasoline",
            currency="brl",
            price=5.99,
            tax_percent=27.0,
            latitude=-15.793889,
            longitude=-47.882778,
            effective_date="2026-04-01",
            collected_at="2026-04-01T10:00:00",
            source_api="mock-api",
        ),
        Row(
            event_id="evt-1",
            country_code="br",
            region_code="df",
            city="brasilia",
            station_id="br-001",
            brand="ipiranga",
            fuel_type="gasoline",
            currency="brl",
            price=6.09,
            tax_percent=27.0,
            latitude=-15.793889,
            longitude=-47.882778,
            effective_date="2026-04-01",
            collected_at="2026-04-01T11:00:00",
            source_api="mock-api",
        ),
        Row(
            event_id="evt-2",
            country_code="br",
            region_code="df",
            city="brasilia",
            station_id="br-002",
            brand="shell",
            fuel_type="gasoline",
            currency="brl",
            price=50.0,
            tax_percent=27.0,
            latitude=-15.793000,
            longitude=-47.883000,
            effective_date="2026-04-01",
            collected_at="2026-04-01T10:00:00",
            source_api="mock-api",
        ),
    ]

    bronze_dataset = spark.createDataFrame(bronze_rows)
    silver_dataset = transform_bronze_to_silver(bronze_dataset)

    rows = silver_dataset.collect()
    assert len(rows) == 1
    assert rows[0]["price"] == 6.09
    assert rows[0]["country_code"] == "BR"
    assert rows[0]["brand"] == "IPIRANGA"


def test_build_gold_features_generates_rolling_metrics_and_target(spark) -> None:
    silver_rows = [
        Row(
            event_id=f"evt-{day}",
            country_code="US",
            region_code="UT",
            city="Lehi",
            station_id="US-001",
            brand="CHEVRON",
            fuel_type="GASOLINE",
            currency="USD",
            price=3.0 + (day * 0.1),
            tax_percent=9.0,
            latitude=40.391617,
            longitude=-111.850769,
            effective_date=f"2026-04-{day + 1:02d}",
            collected_at_ts=f"2026-04-{day + 1:02d}T08:00:00",
            source_api="mock-api",
            ingested_at=f"2026-04-{day + 1:02d}T08:05:00",
        )
        for day in range(8)
    ]

    silver_dataset = (
        spark.createDataFrame(silver_rows)
        .withColumn("effective_date", F.to_date("effective_date"))
        .withColumn("collected_at_ts", F.to_timestamp("collected_at_ts"))
        .withColumn("ingested_at", F.to_timestamp("ingested_at"))
    )

    gold_dataset = build_gold_features(silver_dataset)
    ordered_rows = gold_dataset.orderBy("effective_date").collect()

    assert round(float(ordered_rows[0]["target_next_day_price"]), 2) == 3.10
    assert round(float(ordered_rows[-1]["moving_avg_7d"]), 2) == 3.40
    assert ordered_rows[-1]["geohash"] is not None
