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
from iposto_mlops.pipelines.inference import score_latest_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Run batch inference for the latest Gold snapshot.")
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--model-uri", required=True)
    parser.add_argument("--input-format", default="delta")
    parser.add_argument("--output-format", default="delta")
    args = parser.parse_args()

    configure_logging()
    spark = SparkSession.builder.appName("iposto-mlops-batch-inference").getOrCreate()
    try:
        score_latest_snapshot(
            spark=spark,
            input_path=args.input_path,
            output_path=args.output_path,
            model_uri=args.model_uri,
            input_format=args.input_format,
            output_format=args.output_format,
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
