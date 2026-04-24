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
from iposto_mlops.pipelines.gold import run_gold_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Gold feature layer from Silver data.")
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--input-format", default="delta")
    parser.add_argument("--output-format", default="delta")
    args = parser.parse_args()

    configure_logging()
    spark = SparkSession.builder.appName("iposto-mlops-silver-to-gold").getOrCreate()
    try:
        run_gold_pipeline(
            spark=spark,
            input_path=args.input_path,
            output_path=args.output_path,
            input_format=args.input_format,
            output_format=args.output_format,
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
