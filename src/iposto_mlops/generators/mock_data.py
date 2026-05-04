from __future__ import annotations

import argparse
import json
import math
import random
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StationProfile:
    country_code: str
    region_code: str
    city: str
    station_id: str
    brand: str
    fuel_type: str
    currency: str
    latitude: float
    longitude: float
    base_price: float
    tax_percent: float


STATIONS = [
    StationProfile(
        "BR", "DF", "Brasilia", "BR-001", "IPIRANGA", "GASOLINE", "BRL",
        -15.793889, -47.882778, 5.89, 27.0
    ),
    StationProfile(
        "BR", "DF", "Brasilia", "BR-002", "SHELL", "DIESEL", "BRL",
        -15.794100, -47.890000, 5.79, 18.0
    ),
    StationProfile(
        "BR", "SP", "Sao Paulo", "BR-003", "PETROBRAS", "ETHANOL", "BRL",
        -23.550520, -46.633308, 4.19, 12.0
    ),
    StationProfile(
        "US", "UT", "Lehi", "US-001", "CHEVRON", "GASOLINE", "USD",
        40.391617, -111.850769, 3.49, 9.0
    ),
    StationProfile(
        "US", "UT", "Lehi", "US-002", "MAVERIK", "DIESEL", "USD",
        40.394000, -111.850100, 3.69, 7.0
    ),
    StationProfile(
        "US", "AZ", "Phoenix", "US-003", "CIRCLE_K", "GASOLINE", "USD",
        33.448376, -112.074036, 3.59, 8.0
    ),
]


def _seasonal_multiplier(current_date: date) -> float:
    day_of_year = current_date.timetuple().tm_yday
    return 1.0 + (math.sin(day_of_year / 365 * 2 * math.pi) * 0.035)


def _price_for_station(
    profile: StationProfile,
    current_date: date,
    random_generator: random.Random
) -> float:
    seasonal_component = _seasonal_multiplier(current_date)
    weekday_component = 1.0 + (0.01 if current_date.weekday() in {4, 5} else -0.005)
    noise = random_generator.uniform(-0.06, 0.06)
    raw_price = profile.base_price * seasonal_component * weekday_component + noise

    if random_generator.random() < 0.015:
        raw_price *= 3.5

    return round(raw_price, 3)


def generate_mock_records(
    output_dir: str,
    days: int,
    seed: int = 42,
    start_date: date | None = None,
) -> int:
    random_generator = random.Random(seed)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    first_date = start_date or (date.today() - timedelta(days=days - 1))
    record_count = 0

    for day_index in range(days):
        effective_date = first_date + timedelta(days=day_index)
        partition_dir = root / f"effective_date={effective_date.isoformat()}"
        partition_dir.mkdir(parents=True, exist_ok=True)
        output_file = partition_dir / f"fuel_prices_{effective_date.isoformat()}.json"

        with output_file.open("w", encoding="utf-8") as handle:
            for station in STATIONS:
                payload = {
                    "event_id": str(uuid.uuid4()),
                    "country_code": station.country_code,
                    "region_code": station.region_code,
                    "city": station.city,
                    "station_id": station.station_id,
                    "brand": station.brand,
                    "fuel_type": station.fuel_type,
                    "currency": station.currency,
                    "price": _price_for_station(station, effective_date, random_generator),
                    "tax_percent": station.tax_percent,
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                    "effective_date": effective_date.isoformat(),
                    "collected_at": datetime.combine(
                        effective_date, datetime.min.time()
                    ).isoformat(),
                    "source_api": "mock-station-simulator",
                }
                handle.write(json.dumps(payload) + "\n")
                record_count += 1

    return record_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Bronze mock data for iposto-mlops.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    generated_rows = generate_mock_records(
        output_dir=args.output_dir,
        days=args.days,
        seed=args.seed,
    )
    print(f"Generated {generated_rows} Bronze rows in {args.output_dir}.")


if __name__ == "__main__":
    main()
