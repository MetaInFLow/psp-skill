#!/usr/bin/env python3
"""Validate PSP XML artifact structure without judging content truth."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


MATURITY_LEVELS = {"scaffold", "evidence-limited-v0", "public-v0", "research-grade", "avatar-grade"}
SUPPORTED_LANGUAGES = {"zh-CN", "en-US"}
MATURITY_ORDER = ("scaffold", "evidence-limited-v0", "public-v0", "research-grade", "avatar-grade")

REQUIRED_MODULES = (
    "language_contract",
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
    "language_contract": (
        "output_language",
        "content_language_policy",
        "mixed_language_policy",
        "failure_policy",
    ),
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

CONTENT_CORE_MODULES = {
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
}

CONTENT_MODULE_WEIGHTS = {
    "language_contract": 2,
    "metadata": 2,
    "evidence_maturity": 6,
    "source_inventory": 5,
    "evidence_boundary": 5,
    "ontology_map": 8,
    "kernel": 9,
    "cognition": 8,
    "decision_model": 10,
    "interaction_model": 7,
    "business_domain_model": 6,
    "language_fingerprint": 7,
    "best_state": 6,
    "delegation_boundary": 6,
    "runtime_instructions": 7,
    "validation_plan": 7,
    "confirmation_checklist": 5,
    "acceptance_criteria": 5,
    "confidence_by_section": 4,
    "missing_information": 4,
    "iteration_log": 3,
}

STATUS_SCORE = {
    "avatar-grade": 100,
    "research-grade": 90,
    "confirmed": 88,
    "public-v0": 72,
    "inferred": 68,
    "medium-high": 64,
    "medium_high": 64,
    "configured": 62,
    "append-only": 60,
    "candidate-public-v0": 58,
    "evidence-limited-v0": 45,
    "hypothesis": 42,
    "low": 30,
    "not_extractable": 22,
    "not-extractable": 22,
    "not_started": 18,
    "not-started": 18,
    "unassessed": 12,
    "empty": 8,
    "scaffold": 6,
}

CONFIDENCE_SCORE = {
    "high": 100,
    "medium-high": 80,
    "medium_high": 80,
    "medium": 62,
    "low-medium": 42,
    "low_medium": 42,
    "low": 28,
    "insufficient": 6,
}

SCAFFOLD_MARKERS = (
    "TODO",
    "todo",
    "scaffold",
    "unassessed",
    "not_started",
    "not-started",
    "empty",
    "none",
    "not-counted",
    "unknown",
    "尚未",
    "待补",
)

CONTENT_EXCLUDE_TAGS = {
    "question",
    "runtime_use",
    "missing_evidence",
    "missing_information",
}


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


def clean_text(value: str) -> str:
    return " ".join(value.split()).strip()


def element_text(element: ET.Element, exclude_tags: set[str] | None = None) -> str:
    exclude_tags = exclude_tags or set()
    parts: list[str] = []
    for descendant in element.iter():
        if descendant.tag in exclude_tags:
            continue
        text = text_of(descendant)
        if text:
            parts.append(text)
    return clean_text(" ".join(parts))


def substantive_evidence_text(element: ET.Element) -> str:
    parts: list[str] = []
    if element.get("evidence"):
        parts.append(element.get("evidence", ""))
    for descendant in element.iter():
        if descendant.tag == "evidence":
            parts.append(text_of(descendant))
    text = clean_text(" ".join(parts))
    if not text or text.lower() in {"none", "n/a", "na", "unknown"}:
        return ""
    return text


def confidence_value(raw: str | None) -> int:
    if not raw:
        return 0
    return CONFIDENCE_SCORE.get(raw.strip().lower(), 34)


def status_value(raw: str | None) -> int:
    if not raw:
        return 0
    return STATUS_SCORE.get(raw.strip().lower(), 40)


def missing_required_children(module_name: str, module: ET.Element) -> list[str]:
    missing = [name for name in NESTED_REQUIREMENTS.get(module_name, ()) if child(module, name) is None]
    if module_name == "ontology_map":
        dimensions = child(module, "dimensions")
        if dimensions is None:
            missing.append("dimensions")
        else:
            missing.extend(
                f"dimensions/{name}" for name in ONTOLOGY_DIMENSIONS if child(dimensions, name) is None
            )
    return missing


def required_child_score(module_name: str, module: ET.Element) -> int:
    required = list(NESTED_REQUIREMENTS.get(module_name, ()))
    if module_name == "ontology_map":
        dimensions = child(module, "dimensions")
        if dimensions is None:
            return 0
        required.extend(f"dimensions/{name}" for name in ONTOLOGY_DIMENSIONS)
        present = len(NESTED_REQUIREMENTS.get(module_name, ())) + sum(
            1 for name in ONTOLOGY_DIMENSIONS if child(dimensions, name) is not None
        )
        return round(present / len(required) * 100) if required else 100
    if not required:
        return 100
    present = sum(1 for name in required if child(module, name) is not None)
    return round(present / len(required) * 100)


def substance_score(module_name: str, module: ET.Element) -> int:
    text = element_text(module, CONTENT_EXCLUDE_TAGS)
    meaningful_children = [
        descendant
        for descendant in module.iter()
        if descendant is not module
        and descendant.tag not in CONTENT_EXCLUDE_TAGS
        and (text_of(descendant) or list(descendant))
    ]
    score = min(100, len(text) // 8 + len(meaningful_children) * 4)
    status = (module.get("status") or "").strip().lower()
    if status in {"scaffold", "unassessed", "empty", "not_started", "not-started"}:
        score = min(score, 35)
    if module_name == "language_fingerprint" and child(module, "measurable_features") is None:
        score = min(score, 65)
    return score


def module_content_score(module_name: str, module: ET.Element | None) -> dict[str, object]:
    if module is None:
        return {
            "score": 0,
            "status": "missing",
            "confidence": "missing",
            "has_evidence": False,
            "has_missing_evidence": False,
            "required_child_score": 0,
            "substance_score": 0,
            "missing_required_children": list(NESTED_REQUIREMENTS.get(module_name, ())),
            "gaps": ["module missing"],
        }

    status = (module.get("status") or "").strip().lower()
    confidence = (module.get("confidence") or "").strip().lower()
    required_score = required_child_score(module_name, module)
    evidence_text = substantive_evidence_text(module)
    has_real_evidence = bool(evidence_text)
    has_missing = has_missing_marker(module)
    substance = substance_score(module_name, module)

    score = round(
        status_value(status) * 0.22
        + confidence_value(confidence) * 0.20
        + (100 if has_real_evidence else 35 if has_missing else 0) * 0.18
        + (100 if has_missing else 55 if has_real_evidence else 0) * 0.10
        + required_score * 0.12
        + substance * 0.18
    )
    score = max(0, min(100, score))

    gaps: list[str] = []
    missing_children = missing_required_children(module_name, module)
    if missing_children:
        gaps.append("missing required children: " + ", ".join(missing_children))
    if not status:
        gaps.append("missing status")
    elif status in {"scaffold", "unassessed", "empty", "not_started", "not-started"}:
        gaps.append(f"status is {status}")
    if not confidence:
        gaps.append("missing confidence")
    elif confidence in {"insufficient", "low", "low_medium", "low-medium"}:
        gaps.append(f"confidence is {confidence}")
    if module_name in CONTENT_CORE_MODULES and not has_real_evidence:
        gaps.append("no substantive evidence")
    if not has_missing and module_name in CONTENT_CORE_MODULES:
        gaps.append("missing missing_evidence disclosure")
    if substance < 45 and module_name in CONTENT_CORE_MODULES:
        gaps.append("content too thin for this PSP module")

    return {
        "score": score,
        "status": status or "missing",
        "confidence": confidence or "missing",
        "has_evidence": has_real_evidence,
        "has_missing_evidence": has_missing,
        "required_child_score": required_score,
        "substance_score": substance,
        "missing_required_children": missing_children,
        "gaps": gaps,
    }


def level_from_score(score: int) -> str:
    if score >= 85:
        return "avatar-grade"
    if score >= 70:
        return "research-grade"
    if score >= 45:
        return "public-v0"
    if score >= 20:
        return "evidence-limited-v0"
    return "scaffold"


def cap_level(level: str, cap: str) -> str:
    if level not in MATURITY_ORDER:
        level = "scaffold"
    if cap not in MATURITY_ORDER:
        return level
    return MATURITY_ORDER[min(MATURITY_ORDER.index(level), MATURITY_ORDER.index(cap))]


def compute_content_maturity(root: ET.Element) -> dict[str, object]:
    module_scores = {
        name: module_content_score(name, child(root, name))
        for name in REQUIRED_MODULES
    }
    total_weight = sum(CONTENT_MODULE_WEIGHTS.get(name, 1) for name in REQUIRED_MODULES)
    weighted_score = round(
        sum(int(module_scores[name]["score"]) * CONTENT_MODULE_WEIGHTS.get(name, 1) for name in REQUIRED_MODULES)
        / total_weight
    )
    level = level_from_score(weighted_score)

    evidence_module = child(root, "evidence_maturity")
    declared_level = "unknown"
    if evidence_module is not None:
        declared_level = (text_of(child(evidence_module, "level")) or evidence_module.get("level") or "unknown").strip().lower()

    blocking_gaps: list[str] = []
    non_blocking_gaps: list[str] = []
    for module_name, result in module_scores.items():
        gaps = [str(gap) for gap in result["gaps"]]
        if not gaps:
            continue
        if module_name in CONTENT_CORE_MODULES and int(result["score"]) < 45:
            blocking_gaps.append(f"{module_name}: " + "; ".join(gaps[:3]))
        else:
            non_blocking_gaps.append(f"{module_name}: " + "; ".join(gaps[:2]))

    validation_score = int(module_scores["validation_plan"]["score"])
    fingerprint_score = int(module_scores["language_fingerprint"]["score"])
    source_score = int(module_scores["source_inventory"]["score"])
    if validation_score < 60:
        level = cap_level(level, "public-v0")
        blocking_gaps.append("validation_plan: blocks research/avatar-grade until holdout or blind validation is started")
    if fingerprint_score < 60:
        level = cap_level(level, "public-v0")
        blocking_gaps.append("language_fingerprint: blocks avatar-grade style fidelity until measured corpus evidence exists")
    if source_score < 55:
        level = cap_level(level, "public-v0")
        non_blocking_gaps.append("source_inventory: source provenance is not strong enough for research-grade")
    if declared_level in {"scaffold", "evidence-limited-v0", "public-v0", "research-grade", "avatar-grade"}:
        level = cap_level(level, declared_level)

    weak_modules = [
        {"module": name, "score": result["score"], "status": result["status"], "confidence": result["confidence"]}
        for name, result in module_scores.items()
        if int(result["score"]) < 55
    ]
    high_confidence_modules = [
        {"module": name, "score": result["score"], "status": result["status"], "confidence": result["confidence"]}
        for name, result in module_scores.items()
        if int(result["score"]) >= 75 and str(result["confidence"]) in {"high", "medium-high", "medium_high"}
    ]

    return {
        "level": level,
        "score": weighted_score,
        "score_out_of": 100,
        "declared_evidence_maturity_level": declared_level,
        "meaning": "PSP content maturity computed from the required PSP XML output structure; separate from schema completion.",
        "module_scores": module_scores,
        "weak_modules": weak_modules,
        "high_confidence_modules": high_confidence_modules,
        "blocking_gaps": blocking_gaps[:12],
        "non_blocking_gaps": non_blocking_gaps[:12],
    }


def validate_language_contract(root: ET.Element, issues: list[str], prefix: str = "") -> str:
    language = (root.get("language") or "").strip()
    if language not in SUPPORTED_LANGUAGES:
        issues.append(f"{prefix}root language must be one of {', '.join(sorted(SUPPORTED_LANGUAGES))}; got {language or 'missing'}")

    language_contract = child(root, "language_contract")
    contract_language = text_of(child(language_contract, "output_language")) if language_contract is not None else ""
    if not contract_language:
        issues.append(f"{prefix}language_contract/output_language missing")
    elif contract_language not in SUPPORTED_LANGUAGES:
        issues.append(f"{prefix}language_contract/output_language must be one of {', '.join(sorted(SUPPORTED_LANGUAGES))}; got {contract_language}")
    elif language and contract_language != language:
        issues.append(f"{prefix}root language and language_contract/output_language mismatch: {language} != {contract_language}")

    metadata = child(root, "metadata")
    metadata_language = text_of(child(metadata, "output_language")) if metadata is not None else ""
    if not metadata_language:
        issues.append(f"{prefix}metadata/output_language missing")
    elif metadata_language not in SUPPORTED_LANGUAGES:
        issues.append(f"{prefix}metadata/output_language must be one of {', '.join(sorted(SUPPORTED_LANGUAGES))}; got {metadata_language}")
    elif contract_language and metadata_language != contract_language:
        issues.append(f"{prefix}metadata/output_language and language_contract/output_language mismatch: {metadata_language} != {contract_language}")

    return language or contract_language or metadata_language or "unknown"


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
    output_language = validate_language_contract(root, issues)

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
        "output_language": output_language,
        "maturity_level": maturity,
        "structure_completion": structure_completion,
        "content_maturity": compute_content_maturity(root),
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
    output_language = validate_language_contract(root, issues, prefix="EVIDENCE_MATURITY.xml: ")
    required = (
        "language_contract",
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
        "output_language": output_language,
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
        print(f"- output_language: {result.get('output_language')}")
        print(f"- maturity_level: {result.get('maturity_level')}")
        print(f"- structure_completion: {result.get('structure_completion')}%")
        content_maturity = result.get("content_maturity")
        if isinstance(content_maturity, dict):
            print(
                "- content_maturity: "
                f"{content_maturity.get('level')} "
                f"({content_maturity.get('score')}/{content_maturity.get('score_out_of')})"
            )
            for gap in content_maturity.get("blocking_gaps", [])[:5]:
                print(f"- content_gap: {gap}")
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
