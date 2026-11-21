"""
Verification Suite for Dynamic OpenAPI 3.0 Contract Specification Parsing in Data Generator.
Author: M. Hasaam (24i-3107) | Core Technical Area 2
Rubric Component 7: "Build a generator that reads the spec and produces EP classes and 3-point BVA values... Expect an updated spec in the viva."
"""
import pytest
from tools.datagen.generator import load_constraints_from_openapi, DataGenerator, generate_bva_quantity

class TestOpenAPISpecDatagenIntegration:
    """Verifies that tools/datagen dynamically couples with OpenAPI 3.0 contract."""

    def test_generator_reads_baseline_openapi_contract(self):
        """Verifies generator dynamically extracts baseline constraints from openapi/team-spec.yaml."""
        spec_path = "openapi/team-spec.yaml"
        constraints = load_constraints_from_openapi(spec_path)

        assert constraints["quota_size"] == 10, "Quota capacity in spec must be 10"
        assert constraints["default_price"] == "50.00", "Default price in spec must be 50.00"
        assert constraints["organizer_slug"] == "sqe", "Organizer slug must match spec"
        assert constraints["event_slug"] == "sqe2026", "Event slug must match spec"
        assert constraints["currency"] == "EUR", "Currency must match spec"

    def test_dynamic_viva_regeneration_on_updated_spec(self, tmp_path):
        """
        Simulates the viva examination scenario where the professor modifies the OpenAPI spec.
        Proves that generator immediately synthesizes updated BVA boundary values without code modification.
        """
        updated_spec_content = """openapi: 3.0.3
info:
  title: pretix Updated Viva Spec
  version: 2.0.0
components:
  schemas:
    QuotaAvailability:
      type: object
      properties:
        total_size:
          type: integer
          example: 25
    Item:
      type: object
      properties:
        id:
          type: integer
          example: 2
        default_price:
          type: string
          example: "75.00"
        name:
          type: object
          properties:
            en:
              type: string
              example: "VIP Pass"
    Organizer:
      type: object
      properties:
        slug:
          type: string
          example: "sqe"
    Event:
      type: object
      properties:
        slug:
          type: string
          example: "sqe2026"
        currency:
          type: string
          example: "USD"
"""
        simulated_spec_file = tmp_path / "viva_updated_spec.yaml"
        simulated_spec_file.write_text(updated_spec_content, encoding="utf-8")

        # Generator dynamically loads from updated spec
        updated_constraints = load_constraints_from_openapi(str(simulated_spec_file))
        assert updated_constraints["quota_size"] == 25
        assert updated_constraints["default_price"] == "75.00"
        assert updated_constraints["currency"] == "USD"

        # Verify synthesized 3-point BVA values dynamically adapt
        gen = DataGenerator(updated_constraints)
        dataset = gen.generate(seed=42)

        # For capacity S = 25:
        # min-1=0, min=1, min+1=2, nom=12, max-1=24, max=25, max+1=26
        bva_quantities = [p["quantity"] for p in dataset["bva_quantity"]]
        assert bva_quantities == [0, 1, 2, 12, 24, 25, 26], "BVA boundaries must dynamically scale to S=25"

        # Verify boundary partition payload uses updated capacity 25
        upper_bound_case = next(c for c in dataset["equivalence_partitions"]["boundary_partition"] if c["case_id"] == "EP-BND-02")
        assert upper_bound_case["quantity"] == 25
        assert upper_bound_case["payload"]["positions"][0]["price"] == "75.00"
