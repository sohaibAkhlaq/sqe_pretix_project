#!/usr/bin/env python3
"""
CLI Interface for Automated Test Data Generator.
Usage:
    python -m tools.datagen.cli --output reports/api/generated_data.json
    python -m tools.datagen.cli --quota 15 --price 75.00 --output reports/api/regenerated_data.json
"""
import os
import sys
import json
import argparse
from tools.datagen.generator import DataGenerator, DEFAULT_CONSTRAINTS

def load_config(config_path: str = None) -> dict:
    if config_path and os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("constraints", DEFAULT_CONSTRAINTS)
        except ImportError:
            print("[WARNING] 'pyyaml' is not installed in the active Python environment.")
            print("[INFO] Run with project virtualenv: .\\.venv\\Scripts\\python.exe -m tools.datagen.cli")
            print("[INFO] Defaulting to standard constraints.")
            return DEFAULT_CONSTRAINTS.copy()
    return DEFAULT_CONSTRAINTS.copy()

def main():
    parser = argparse.ArgumentParser(description="pretix Quality Engineering Test Data Generator")
    parser.add_argument("--config", type=str, help="Path to constraints config YAML")
    parser.add_argument("--quota", type=int, help="Override quota capacity constraint")
    parser.add_argument("--price", type=str, help="Override ticket price constraint")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--output", type=str, default="reports/api/generated_data.json", help="Output JSON path")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.quota:
        cfg["quota_size"] = args.quota
    if args.price:
        cfg["default_price"] = args.price

    print("======================================================================")
    print("SE3002 Automated Test Data Generator (tools/datagen)")
    print("======================================================================")
    print(f"Active Constraints: Quota Size={cfg['quota_size']}, Unit Price={cfg['default_price']} EUR")

    gen = DataGenerator(cfg)
    dataset = gen.generate(seed=args.seed)

    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"[SUCCESS] Dataset generated successfully: {output_path}")
    print(f"Summary: {len(dataset['bva_quantity'])} Quantity BVA points, {len(dataset['bva_price'])} Price BVA points.")
    print(f"Partitions: {len(dataset['equivalence_partitions']['valid_partition'])} Valid, "
          f"{len(dataset['equivalence_partitions']['invalid_partition'])} Invalid, "
          f"{len(dataset['equivalence_partitions']['boundary_partition'])} Boundary.")

if __name__ == "__main__":
    main()
