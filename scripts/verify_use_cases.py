#!/usr/bin/env python3
"""
SE3002 Component 8 Audit: Use Case Specification Verification Script.
Audits docs/use-cases.md against course rubric:
- 6 Use Cases derived from requirements
- Complete Normal Flows (6)
- Complete Alternative Flows (12, 2 per UC)
- Complete Exception Flows (12, 2 per UC)
- Explicit Preconditions and Postconditions for all UCs
- Distribution across team members
"""
import os
import re
import sys

def audit_use_cases(file_path: str):
    print("======================================================================")
    print("SE3002 Component 8: Use Case Specification Audit (3 Marks, CLO3)")
    print("======================================================================")
    
    if not os.path.exists(file_path):
        print(f"[FAIL] Missing {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify 6 Use Cases
    ucs = re.findall(r"##\s+\d+\.\s+Use Case\s+(\d+):\s+([^\n]+)", content)
    print(f"--- [CHECK 1] Identified Use Cases ({len(ucs)} / 6) ---")
    for uc_num, uc_title in ucs:
        print(f"  [FOUND] UC{uc_num}: {uc_title.strip()}")
    
    assert len(ucs) == 6, f"Expected 6 Use Cases, found {len(ucs)}"

    # Audit each use case structure
    print("\n--- [CHECK 2] Auditing Preconditions, Postconditions & 30 Flows ---")
    total_nf = 0
    total_af = 0
    total_ef = 0

    uc_blocks = re.split(r"##\s+\d+\.\s+Use Case\s+\d+:", content)[1:]
    
    for idx, block in enumerate(uc_blocks, 1):
        # Preconditions
        pre = re.findall(r"Pre-Conditions?:(.*?)(?=Post-Conditions?:)", block, re.DOTALL)
        has_pre = bool(pre and len(re.findall(r"\d+\.", pre[0])) >= 2)
        
        # Postconditions
        post = re.findall(r"Post-Conditions?:(.*?)(?=### Flows of Events)", block, re.DOTALL)
        has_post = bool(post and len(re.findall(r"\d+\.", post[0])) >= 2)
        
        # Normal Flow
        nf = re.findall(r"Normal Flow.*?:(.*?)(?=\*\s+\*\*Alternative Flow)", block, re.DOTALL)
        has_nf = bool(nf and len(re.findall(r"\d+\.", nf[0])) >= 3)
        if has_nf: total_nf += 1

        # Alternative Flows
        afs = re.findall(r"Alternative Flow\s+(A\d+)", block)
        total_af += len(afs)

        # Exception Flows
        efs = re.findall(r"Exception Flow\s+(E\d+)", block)
        total_ef += len(efs)

        print(f"  UC{idx}: Preconditions={has_pre} | Postconditions={has_post} | NF={has_nf} | AFs={len(afs)} ({', '.join(afs)}) | EFs={len(efs)} ({', '.join(efs)})")
        
        assert has_pre, f"UC{idx} missing valid preconditions"
        assert has_post, f"UC{idx} missing valid postconditions"
        assert has_nf, f"UC{idx} missing valid normal flow"
        assert len(afs) >= 2, f"UC{idx} expected >=2 AFs, found {len(afs)}"
        assert len(efs) >= 2, f"UC{idx} expected >=2 EFs, found {len(efs)}"

    print(f"\nFlow Totals: Normal={total_nf}/6, Alternative={total_af}/12, Exception={total_ef}/12")
    total_flows = total_nf + total_af + total_ef
    print(f"Total Execution Flows: {total_flows} / 30")
    assert total_flows == 30, f"Expected 30 total flows, found {total_flows}"

    print("\n--- [CHECK 3] Verifying Team Distribution (2 UCs per member) ---")
    authors = re.findall(r"Author / Owner:\*\*\s+([^\n]+)", content)
    author_counts = {}
    for a in authors:
        a_clean = a.split("(")[0].strip()
        author_counts[a_clean] = author_counts.get(a_clean, 0) + 1
    
    for a, count in author_counts.items():
        print(f"  Owner: {a:12} -> {count} Use Cases")
        assert count == 2, f"Expected 2 UCs for {a}, found {count}"

    print("\n======================================================================")
    print("[SUCCESS] ALL USE CASE SPECIFICATION CRITERIA VERIFIED (3/3 MARKS)")
    print("======================================================================")
    return True

if __name__ == "__main__":
    audit_use_cases("docs/use-cases.md")
