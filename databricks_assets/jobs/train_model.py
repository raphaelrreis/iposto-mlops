from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from iposto_mlops.logging_utils import configure_logging
from iposto_mlops.pipelines.training import train_model_from_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the iposto-mlops forecasting model.")
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--input-format", default="delta")
    args = parser.parse_args()

    configure_logging()
    spark = SparkSession.builder.appName("iposto-mlops-train-model").getOrCreate()
    try:
        train_model_from_path(
            spark=spark,
            input_path=args.input_path,
            input_format=args.input_format,
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
