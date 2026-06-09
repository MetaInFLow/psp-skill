#!/usr/bin/env python3
"""Validate PSP XML artifact structure without judging content truth."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


MATURITY_LEVELS = {"scaffold", "evidence-limited-v0", "public-v0", "research-grade", "avatar-grade"}

REQUIRED_MODULES = (
    "metadata",
    "evidence_maturity",
    "source_inventory",
    "evidence_boundary",
    "ontology_map",
    "kernel",
    "cognition",
    "decision_model",
    "interaction_model",
    "business_domain_model",
    "language_fingerprint",
    "best_state",
    "delegation_boundary",
    "runtime_instructions",
    "validation_plan",
    "confirmation_checklist",
    "acceptance_criteria",
    "confidence_by_section",
    "missing_information",
    "iteration_log",
)

NESTED_REQUIREMENTS = {
    "kernel": (
        "ultimate_value_order",
        "boundaries",
        "drivers",
        "identity_self_definition",
    ),
    "ontology_map": (
        "dimensions",
    ),
    "cognition": (
        "world_assumptions",
        "attribution_patterns",
        "attention_filter",
        "analogy_domains",
    ),
    "decision_model": (
        "decision_style",
        "information_threshold",
        "risk_policy",
        "conflict_resolution",
        "judgment_patterns",
        "pre_answer_checks",
        "forced_downgrade_rules",
    ),
    "interaction_model": (
        "communication_style",
        "relationship_posture",
        "disagreement_style",
        "questioning_style",
    ),
    "business_domain_model": (
        "business_logic",
        "customer_logic",
        "talent_logic",
        "organization_logic",
        "data_and_metrics",
        "execution_loops",
    ),
    "delegation_boundary": (
        "cannot_represent",
        "can_represent",
        "private_information_policy",
        "external_translation_policy",
    ),
    "runtime_instructions": (
        "must_follow",
        "must_not_do",
        "uncertainty_policy",
    ),
    "validation_plan": (
        "blind_evaluation",
        "judgment_holdout",
        "consistency_scan",
    ),
    "confirmation_checklist": (
        "items",
    ),
}

ONTOLOGY_DIMENSIONS = (
    "worldview",
    "lifeview",
    "values_and_bottom_lines",
    "role_and_mission",
    "methodology_and_fact_view",
    "decision_and_tradeoff_view",
    "human_and_talent_view",
    "business_and_customer_view",
    "expression_and_organization_view",
)


def resolve_report_path(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = (
        path / "current" / "PSP_REPORT.xml",
        path / "PSP_REPORT.xml",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    versioned = sorted((path / "versions").glob("PSP_REPORT.*.xml"))
    if versioned:
        return versioned[-1]
    raise FileNotFoundError(f"Cannot find PSP_REPORT.xml under {path}")


def resolve_evidence_path(report_path: Path) -> Path | None:
    if report_path.parent.name == "current":
        candidate = report_path.parent / "EVIDENCE_MATURITY.xml"
        if candidate.exists():
            return candidate
        versioned = sorted((report_path.parent.parent / "versions").glob("EVIDENCE_MATURITY.*.xml"))
        return versioned[-1] if versioned else None
    candidate = report_path.parent / "EVIDENCE_MATURITY.xml"
    return candidate if candidate.exists() else None


def child(element: ET.Element, name: str) -> ET.Element | None:
    return element.find(name)


def text_of(element: ET.Element | None) -> str:
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def has_evidence_marker(element: ET.Element) -> bool:
    if element.get("evidence"):
        return True
    direct = child(element, "evidence")
    if direct is not None and text_of(direct):
        return True
    return any(descendant.tag == "evidence" and text_of(descendant) for descendant in element.iter())


def has_missing_marker(element: ET.Element) -> bool:
    direct = child(element, "missing_evidence")
    if direct is not None and text_of(direct):
        return True
    return any(descendant.tag == "missing_evidence" and text_of(descendant) for descendant in element.iter())


def validate_report(root: ET.Element) -> dict[str, object]:
    issues: list[str] = []
    warnings: list[str] = []

    if root.tag != "psp_report":
        issues.append(f"root tag must be psp_report, got {root.tag}")
    if root.get("schema") != "psp.report.v1":
        issues.append("root schema must be psp.report.v1")
    if not root.get("person_id"):
        issues.append("root missing person_id")
    if not root.get("generated_at"):
        issues.append("root missing generated_at")

    module_results: dict[str, dict[str, object]] = {}
    for module_name in REQUIRED_MODULES:
        module = child(root, module_name)
        result = {"exists": module is not None, "missing_children": []}
        if module is None:
            issues.append(f"missing module: {module_name}")
            module_results[module_name] = result
            continue

        if module_name not in {"metadata", "iteration_log"}:
            if not module.get("status"):
                issues.append(f"{module_name} missing status attribute")
            if not module.get("confidence"):
                issues.append(f"{module_name} missing confidence attribute")

        if module_name in NESTED_REQUIREMENTS:
            missing_children = [name for name in NESTED_REQUIREMENTS[module_name] if child(module, name) is None]
            if missing_children:
                issues.append(f"{module_name} missing children: {', '.join(missing_children)}")
            result["missing_children"] = missing_children

        if module_name == "ontology_map":
            dimensions = child(module, "dimensions")
            if dimensions is not None:
                missing_dimensions = [name for name in ONTOLOGY_DIMENSIONS if child(dimensions, name) is None]
                if missing_dimensions:
                    issues.append("ontology_map.dimensions missing: " + ", ".join(missing_dimensions))
                result["missing_dimensions"] = missing_dimensions

        if module_name in {
            "kernel",
            "ontology_map",
            "cognition",
            "decision_model",
            "interaction_model",
            "business_domain_model",
            "language_fingerprint",
            "best_state",
            "delegation_boundary",
            "runtime_instructions",
            "validation_plan",
            "confirmation_checklist",
            "acceptance_criteria",
        }:
            if not has_evidence_marker(module):
                warnings.append(f"{module_name} has no evidence marker")
            if not has_missing_marker(module):
                warnings.append(f"{module_name} has no missing_evidence marker")

        module_results[module_name] = result

    maturity = "unknown"
    evidence_maturity = child(root, "evidence_maturity")
    if evidence_maturity is not None:
        maturity = text_of(child(evidence_maturity, "level")) or evidence_maturity.get("level") or "unknown"
        maturity = maturity.strip().lower()
        if maturity not in MATURITY_LEVELS:
            issues.append(
                "evidence_maturity level must be one of "
                + ", ".join(sorted(MATURITY_LEVELS))
                + f"; got {maturity}"
            )

    confidence = child(root, "confidence_by_section")
    if confidence is not None and not confidence.findall("section"):
        issues.append("confidence_by_section must contain at least one section element")

    missing = child(root, "missing_information")
    if missing is not None and not missing.findall("item"):
        issues.append("missing_information must contain at least one item element")

    iteration = child(root, "iteration_log")
    if iteration is not None and not iteration.findall("entry"):
        issues.append("iteration_log must contain at least one entry element")

    acceptance = child(root, "acceptance_criteria")
    if acceptance is not None and not acceptance.findall("criterion"):
        issues.append("acceptance_criteria must contain at least one criterion element")

    checklist = child(root, "confirmation_checklist")
    if checklist is not None:
        items = child(checklist, "items")
        if items is None or not items.findall("item"):
            issues.append("confirmation_checklist.items must contain at least one item element")

    required_count = len(REQUIRED_MODULES)
    present_count = sum(1 for name in REQUIRED_MODULES if child(root, name) is not None)
    structure_completion = round(present_count / required_count * 100)

    return {
        "passed": not issues,
        "schema": root.get("schema"),
        "person_id": root.get("person_id"),
        "maturity_level": maturity,
        "structure_completion": structure_completion,
        "modules": module_results,
        "issues": issues,
        "warnings": warnings,
    }


def validate_evidence_maturity(root: ET.Element) -> dict[str, object]:
    issues: list[str] = []
    warnings: list[str] = []
    if root.tag != "evidence_maturity_report":
        issues.append(f"root tag must be evidence_maturity_report, got {root.tag}")
    if root.get("schema") != "psp.evidence-maturity.v1":
        issues.append("root schema must be psp.evidence-maturity.v1")
    if not root.get("person_id"):
        issues.append("root missing person_id")
    required = (
        "metadata",
        "maturity",
        "evidence_sources",
        "unavailable_sources",
        "incomplete_areas",
        "failed_sources",
        "final_disclosure",
        "iteration_log",
    )
    for name in required:
        if child(root, name) is None:
            issues.append(f"evidence maturity missing module: {name}")

    maturity = child(root, "maturity")
    level = maturity.get("level", "").strip().lower() if maturity is not None else ""
    if level not in MATURITY_LEVELS:
        issues.append(
            "evidence maturity level must be one of "
            + ", ".join(sorted(MATURITY_LEVELS))
            + f"; got {level or 'missing'}"
        )
    incomplete = child(root, "incomplete_areas")
    if incomplete is not None and not incomplete.findall("area"):
        warnings.append("evidence maturity incomplete_areas has no area entries")
    return {
        "passed": not issues,
        "schema": root.get("schema"),
        "maturity_level": level or "unknown",
        "issues": issues,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="PSP_REPORT.xml path or person artifact directory")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report_path = resolve_report_path(Path(args.target).expanduser().resolve())
        root = ET.parse(report_path).getroot()
    except Exception as exc:
        result = {
            "passed": False,
            "target": args.target,
            "issues": [str(exc)],
            "warnings": [],
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"[PSP doctor] FAIL: {exc}")
        return 1

    result = validate_report(root)
    result["path"] = str(report_path)
    evidence_path = resolve_evidence_path(report_path)
    if evidence_path is None:
        result["passed"] = False
        result["evidence_maturity_file"] = {
            "passed": False,
            "path": None,
            "issues": ["missing current/EVIDENCE_MATURITY.xml or versions/EVIDENCE_MATURITY.<timestamp>.xml"],
            "warnings": [],
        }
    else:
        try:
            evidence_result = validate_evidence_maturity(ET.parse(evidence_path).getroot())
            evidence_result["path"] = str(evidence_path)
            result["evidence_maturity_file"] = evidence_result
            if not evidence_result["passed"]:
                result["passed"] = False
                result["issues"].extend(f"EVIDENCE_MATURITY.xml: {issue}" for issue in evidence_result["issues"])
        except Exception as exc:
            result["passed"] = False
            result["evidence_maturity_file"] = {
                "passed": False,
                "path": str(evidence_path),
                "issues": [str(exc)],
                "warnings": [],
            }
            result["issues"].append(f"EVIDENCE_MATURITY.xml: {exc}")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[PSP doctor] {status}: {report_path}")
        print(f"- schema: {result.get('schema')}")
        print(f"- person_id: {result.get('person_id')}")
        print(f"- maturity_level: {result.get('maturity_level')}")
        print(f"- structure_completion: {result.get('structure_completion')}%")
        evidence_result = result.get("evidence_maturity_file")
        if isinstance(evidence_result, dict):
            print(f"- evidence_maturity_file: {evidence_result.get('path')}")
        for issue in result["issues"]:
            print(f"- issue: {issue}")
        for warning in result["warnings"]:
            print(f"- warning: {warning}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
