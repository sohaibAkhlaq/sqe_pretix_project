#!/usr/bin/env python3
"""
CLI Interface for Automated Test Data Generator.
Reads OpenAPI 3.0 specification YAML to dynamically synthesize test vectors.

Usage:
    python -m tools.datagen.cli --spec openapi/team-spec.yaml --output reports/api/generated_data.json
    python -m tools.datagen.cli --quota 15 --price 75.00 --output reports/api/regenerated_data.json
"""
import os
import sys
import json
import argparse
from tools.datagen.generator import DataGenerator, DEFAULT_CONSTRAINTS, load_constraints_from_openapi

def main():
    parser = argparse.ArgumentParser(description="pretix Quality Engineering Test Data Generator")
    parser.add_argument("--spec", type=str, default="openapi/team-spec.yaml", help="Path to OpenAPI 3.0 YAML spec contract")
    parser.add_argument("--config", type=str, help="Path to custom constraints config YAML")
    parser.add_argument("--quota", type=int, help="Override quota capacity constraint")
    parser.add_argument("--price", type=str, help="Override ticket price constraint")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--output", type=str, default="reports/api/generated_data.json", help="Output JSON path")
    args = parser.parse_args()

    # 1. Load constraints dynamically from OpenAPI specification
    if args.spec and os.path.exists(args.spec):
        print(f"[CONTRACT] Loading constraints dynamically from OpenAPI spec: {args.spec}")
        cfg = load_constraints_from_openapi(args.spec)
    elif args.config and os.path.exists(args.config):
        print(f"[CONFIG] Loading constraints from config YAML: {args.config}")
        cfg = load_constraints_from_openapi(args.config)
    else:
        print("[INFO] Using default system constraints.")
        cfg = DEFAULT_CONSTRAINTS.copy()

    # 2. Apply optional CLI overrides
    if args.quota:
        cfg["quota_size"] = args.quota
    if args.price:
        cfg["default_price"] = args.price

    print("======================================================================")
    print("SE3002 Automated Test Data Generator (tools/datagen)")
    print("Author: M. Hasaam (24i-3107) | Core Technical Area 2")
    print("======================================================================")
    print(f"Contract Schema Target: {args.spec}")
    print(f"Active Constraints: Quota Capacity={cfg['quota_size']}, Unit Price={cfg['default_price']} {cfg['currency']}")
    print(f"Event Scope: Organizer='{cfg['organizer_slug']}', Event='{cfg['event_slug']}'")

    gen = DataGenerator(cfg)
    dataset = gen.generate(seed=args.seed)

    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"[SUCCESS] Test dataset synthesized successfully: {output_path}")
    print(f"Summary: {len(dataset['bva_quantity'])} Quantity BVA points, {len(dataset['bva_price'])} Price BVA points.")
    print(f"Partitions: {len(dataset['equivalence_partitions']['valid_partition'])} Valid, "
          f"{len(dataset['equivalence_partitions']['invalid_partition'])} Invalid, "
          f"{len(dataset['equivalence_partitions']['boundary_partition'])} Boundary.")

if __name__ == "__main__":
    main()
