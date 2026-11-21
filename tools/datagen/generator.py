"""
Core Data Generation Engine for pretix Order & Quota Testing.
Implements 3-Point Boundary Value Analysis (BVA) and Equivalence Partitioning (EP).
Supports dynamic OpenAPI 3.0 specification contract parsing (YAML).
"""
import os
import re
import random
import uuid
from decimal import Decimal
from typing import Dict, List, Any

DEFAULT_CONSTRAINTS = {
    "organizer_slug": "sqe",
    "event_slug": "sqe2026",
    "item_id": 1,
    "item_name": "Conference Admission Ticket",
    "quota_size": 10,
    "default_price": "50.00",
    "currency": "EUR",
    "locale": "en",
    "sales_channel": "web"
}

def load_constraints_from_openapi(spec_path: str = "openapi/team-spec.yaml") -> Dict[str, Any]:
    """
    Parses OpenAPI 3.0 specification YAML to dynamically extract schema constraints,
    boundary limits, and default parameters.
    Falls back gracefully to DEFAULT_CONSTRAINTS if pyyaml is unavailable or file not found.
    """
    constraints = DEFAULT_CONSTRAINTS.copy()
    if not os.path.exists(spec_path):
        return constraints

    try:
        import yaml
        with open(spec_path, "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)

        schemas = spec.get("components", {}).get("schemas", {})
        
        # 1. Quota Capacity Constraint from QuotaAvailability schema
        if "QuotaAvailability" in schemas:
            quota_props = schemas["QuotaAvailability"].get("properties", {})
            if "total_size" in quota_props and "example" in quota_props["total_size"]:
                constraints["quota_size"] = int(quota_props["total_size"]["example"])
            elif "available_number" in quota_props and "example" in quota_props["available_number"]:
                constraints["quota_size"] = int(quota_props["available_number"]["example"])

        # 2. Ticket Pricing & Item Constraints from Item schema
        if "Item" in schemas:
            item_props = schemas["Item"].get("properties", {})
            if "id" in item_props and "example" in item_props["id"]:
                constraints["item_id"] = int(item_props["id"]["example"])
            if "default_price" in item_props and "example" in item_props["default_price"]:
                constraints["default_price"] = str(item_props["default_price"]["example"])
            if "name" in item_props and "properties" in item_props["name"]:
                en_name = item_props["name"]["properties"].get("en", {}).get("example")
                if en_name:
                    constraints["item_name"] = str(en_name)

        # 3. Organizer and Event Slugs from schemas
        if "Organizer" in schemas:
            org_slug = schemas["Organizer"].get("properties", {}).get("slug", {}).get("example")
            if org_slug:
                constraints["organizer_slug"] = str(org_slug)

        if "Event" in schemas:
            ev_props = schemas["Event"].get("properties", {})
            if "slug" in ev_props and "example" in ev_props["slug"]:
                constraints["event_slug"] = str(ev_props["slug"]["example"])
            if "currency" in ev_props and "example" in ev_props["currency"]:
                constraints["currency"] = str(ev_props["currency"]["example"])

        # 4. Request payload constraints
        if "OrderCreatePayload" in schemas:
            payload_props = schemas["OrderCreatePayload"].get("properties", {})
            if "locale" in payload_props and "example" in payload_props["locale"]:
                constraints["locale"] = str(payload_props["locale"]["example"])
            if "sales_channel" in payload_props and "example" in payload_props["sales_channel"]:
                constraints["sales_channel"] = str(payload_props["sales_channel"]["example"])

    except Exception:
        # Fallback to regex parser if pyyaml fails or schema format varies
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                content = f.read()
            m_quota = re.search(r"total_size:.*?example:\s*(\d+)", content, re.DOTALL)
            if m_quota:
                constraints["quota_size"] = int(m_quota.group(1))
            m_price = re.search(r"default_price:.*?example:\s*[\"']?([\d\.]+)[\"']?", content, re.DOTALL)
            if m_price:
                constraints["default_price"] = str(m_price.group(1))
        except Exception:
            pass

    return constraints

def generate_bva_quantity(quota_size: int) -> List[Dict[str, Any]]:
    """
    Computes 3-Point Boundary Value Analysis on order quantity:
    Points: min-1, min, min+1, nominal, max-1, max, max+1
    For S=10: [0, 1, 2, 5, 9, 10, 11]
    """
    min_val = 1
    max_val = quota_size
    nom_val = max(1, quota_size // 2)

    points = [
        {"point": "min - 1", "quantity": min_val - 1, "valid": False, "category": "Underflow Boundary"},
        {"point": "min",     "quantity": min_val,     "valid": True,  "category": "Minimum Valid Boundary"},
        {"point": "min + 1", "quantity": min_val + 1, "valid": True,  "category": "Just Above Minimum"},
        {"point": "nominal", "quantity": nom_val,     "valid": True,  "category": "Nominal Operating Value"},
        {"point": "max - 1", "quantity": max_val - 1, "valid": True,  "category": "Just Below Maximum"},
        {"point": "max",     "quantity": max_val,     "valid": True,  "category": "Maximum Capacity Boundary"},
        {"point": "max + 1", "quantity": max_val + 1, "valid": False, "category": "Overflow Boundary"},
    ]
    return points

def generate_bva_price(base_price_str: str) -> List[Dict[str, Any]]:
    """
    Computes Boundary Value Analysis on ticket unit price:
    Points: min-1, min, min+1, nominal, max-1, max, max+1
    Valid domain: [0.00, 10000.00]
    """
    base = Decimal(base_price_str)
    points = [
        {"point": "min - 1", "price": "-0.01",   "valid": False, "category": "Negative Price Boundary"},
        {"point": "min",     "price": "0.00",    "valid": True,  "category": "Free Ticket Boundary"},
        {"point": "min + 1", "price": "0.01",    "valid": True,  "category": "Minimal Cent Boundary"},
        {"point": "nominal", "price": str(base), "valid": True,  "category": "Nominal Ticket Price"},
        {"point": "max - 1", "price": "9999.99", "valid": True,  "category": "High End Tier Boundary"},
        {"point": "max",     "price": "10000.00","valid": True,  "category": "Maximum Allowed Price Boundary"},
        {"point": "max + 1", "price": "10000.01","valid": False, "category": "Overflow Price Boundary"},
    ]
    return points

def build_order_payload(item_id: int, price: str, quantity: int, email: str = "attendee@example.com") -> Dict[str, Any]:
    """Constructs a pretix REST API compliant POST /orders/ payload."""
    positions = []
    for i in range(quantity):
        positions.append({
            "item": item_id,
            "price": price,
            "attendee_name": f"Attendee Test {i+1}",
            "attendee_email": email
        })
    return {
        "email": email,
        "locale": "en",
        "sales_channel": "web",
        "positions": positions
    }

def generate_ep_datasets(config: Dict[str, Any] = None, seed: int = 42) -> Dict[str, List[Dict[str, Any]]]:
    """Generates Equivalence Partitioning test cases across valid, invalid, and boundary partitions."""
    random.seed(seed)
    cfg = config or DEFAULT_CONSTRAINTS
    item_id = cfg["item_id"]
    price = cfg["default_price"]
    quota = cfg["quota_size"]

    # 1. Valid Partition (Expected HTTP 201)
    valid_cases = [
        {
            "case_id": "EP-VAL-01",
            "description": "Standard Single Ticket Purchase",
            "quantity": 1,
            "expected_status": 201,
            "payload": build_order_payload(item_id, price, 1, "john.doe@example.com")
        },
        {
            "case_id": "EP-VAL-02",
            "description": "Multi-ticket Purchase (Nominal Quantity)",
            "quantity": 2,
            "expected_status": 201,
            "payload": build_order_payload(item_id, price, 2, "multi.buyer@example.com")
        },
        {
            "case_id": "EP-VAL-03",
            "description": "Bulk Order Consuming Full Available Quota",
            "quantity": quota,
            "expected_status": 201,
            "payload": build_order_payload(item_id, price, quota, "vip.delegation@example.com")
        }
    ]

    # 2. Invalid Partition (Expected HTTP 400)
    invalid_cases = [
        {
            "case_id": "EP-INV-01",
            "description": "Empty Positions Array (Zero Tickets)",
            "quantity": 0,
            "expected_status": 400,
            "payload": {
                "email": "zero.tickets@example.com",
                "locale": "en",
                "sales_channel": "web",
                "positions": []
            }
        },
        {
            "case_id": "EP-INV-02",
            "description": "Order Exceeding Total Quota Capacity",
            "quantity": quota + 1,
            "expected_status": 400,
            "payload": build_order_payload(item_id, price, quota + 1, "overbook@example.com")
        },
        {
            "case_id": "EP-INV-03",
            "description": "Malformed Customer Email Format",
            "quantity": 1,
            "expected_status": 400,
            "payload": {
                "email": "invalid-email-format-without-at",
                "locale": "en",
                "sales_channel": "web",
                "positions": [{"item": item_id, "price": price, "attendee_name": "Bad Email"}]
            }
        },
        {
            "case_id": "EP-INV-04",
            "description": "Non-Existent Item ID Reference",
            "quantity": 1,
            "expected_status": 400,
            "payload": {
                "email": "ghost.item@example.com",
                "locale": "en",
                "sales_channel": "web",
                "positions": [{"item": 999999, "price": price, "attendee_name": "Ghost"}]
            }
        }
    ]

    # 3. Boundary Partition
    boundary_cases = [
        {
            "case_id": "EP-BND-01",
            "description": "Lower Boundary (Quantity = 1)",
            "quantity": 1,
            "expected_status": 201,
            "payload": build_order_payload(item_id, price, 1, "lower.bound@example.com")
        },
        {
            "case_id": "EP-BND-02",
            "description": "Upper Boundary (Quantity = Quota Capacity)",
            "quantity": quota,
            "expected_status": 201,
            "payload": build_order_payload(item_id, price, quota, "upper.bound@example.com")
        },
        {
            "case_id": "EP-BND-03",
            "description": "Immediate Overflow Boundary (Quantity = Quota Capacity + 1)",
            "quantity": quota + 1,
            "expected_status": 400,
            "payload": build_order_payload(item_id, price, quota + 1, "overflow@example.com")
        }
    ]

    return {
        "valid_partition": valid_cases,
        "invalid_partition": invalid_cases,
        "boundary_partition": boundary_cases
    }

def generate_full_dataset(config: Dict[str, Any] = None, seed: int = 42) -> Dict[str, Any]:
    """Assembles comprehensive test data package for API test runner consumption."""
    cfg = config or DEFAULT_CONSTRAINTS
    return {
        "metadata": {
            "generator": "SE3002 Automated Data Generator v1.0",
            "constraints": cfg,
            "seed": seed
        },
        "bva_quantity": generate_bva_quantity(cfg["quota_size"]),
        "bva_price": generate_bva_price(cfg["default_price"]),
        "equivalence_partitions": generate_ep_datasets(cfg, seed)
    }

class DataGenerator:
    """Class wrapper for datagen."""
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DEFAULT_CONSTRAINTS

    def generate(self, seed: int = 42) -> Dict[str, Any]:
        return generate_full_dataset(self.config, seed=seed)
