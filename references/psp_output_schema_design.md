# PSP XML Output Schema Design

Generated: 2026-06-09

## Purpose

PSP turns evidence about a real person into a runnable person model. The source artifact must be stable enough for LifeOS, avatar-description synthesis, runtime prompt generation, and validation workflows to consume without guessing.

The canonical source artifact is XML:

```text
current/PSP_REPORT.xml
versions/PSP_REPORT.<timestamp>.xml
current/EVIDENCE_MATURITY.xml
versions/EVIDENCE_MATURITY.<timestamp>.xml
```

Markdown or HTML renderings are optional derived artifacts. They are never the source of truth.

## Non-Goals

- Do not reduce PSP to a personality summary.
- Do not force high-confidence values when evidence is weak.
- Do not hard-code private raw material into public LifeOS output.
- Do not make the system prompt the PSP source of truth.
- Do not generate `SOUL.md` as a PSP artifact. PSP XML carries the person model, behavior boundaries, best-state profile, and runtime instructions directly.

## Output Principle

Every PSP claim field should expose:

- `status`: `confirmed`, `inferred`, `hypothesis`, `unassessed`, `empty`, or `not_extractable`.
- `confidence`: `high`, `medium`, `low`, or `insufficient`.
- `evidence`: source pointers or explicit `none`.
- `runtime_use`: how this field should or should not be used by an agent.
- `missing_evidence`: what would improve this field.

Fresh scaffolds therefore expose useful absence:

```xml
<decision_model status="unassessed" confidence="insufficient">
  ...
  <evidence>none</evidence>
  <missing_evidence>Decision cases with context, options, action, and outcome.</missing_evidence>
</decision_model>
```

## Required Artifact Set

Default PSP output:

```text
people/{person_id}/
├── ARTIFACTS.xml
├── current/
│   ├── PSP_REPORT.xml
│   └── EVIDENCE_MATURITY.xml
├── versions/
│   ├── PSP_REPORT.YYYYMMDD-HHMMSS.xml
│   └── EVIDENCE_MATURITY.YYYYMMDD-HHMMSS.xml
├── derived/
├── analysis/
├── raw_materials/
├── system_prompt-YYYYMMDD-HHMMSS.txt
└── validation/
```

LifeOS mode:

```text
identity/psp/{person_id}/
├── ARTIFACTS.xml
├── current/
│   ├── PSP_REPORT.xml
│   └── EVIDENCE_MATURITY.xml
├── versions/
│   ├── PSP_REPORT.YYYYMMDD-HHMMSS.xml
│   └── EVIDENCE_MATURITY.YYYYMMDD-HHMMSS.xml
├── derived/
├── current.yml
├── versions.yml
├── changelog.md
├── system_prompt-YYYYMMDD-HHMMSS.txt
└── validation/
```

## Required PSP XML Modules

`PSP_REPORT.xml` root:

```xml
<psp_report schema="psp.report.v1" person_id="" generated_at="" artifact_timestamp="">
  <metadata/>
  <evidence_maturity/>
  <source_inventory/>
  <evidence_boundary/>
  <ontology_map/>
  <kernel/>
  <cognition/>
  <decision_model/>
  <interaction_model/>
  <business_domain_model/>
  <language_fingerprint/>
  <best_state/>
  <delegation_boundary/>
  <runtime_instructions/>
  <validation_plan/>
  <confirmation_checklist/>
  <acceptance_criteria/>
  <confidence_by_section/>
  <missing_information/>
  <iteration_log/>
</psp_report>
```

Required module meanings:

| Module | Required content | Recommended presentation |
|---|---|---|
| `metadata` | person id, display name, protocol version, canonical paths, derived artifact policy, SOUL pause policy | text fields |
| `evidence_maturity` | maturity level, structure readiness, content maturity, source count/types, incomplete areas | enum + counts + list |
| `source_inventory` | approved source list, type, date range, privacy class, performance coefficient, coverage | table/list |
| `evidence_boundary` | allowed/excluded sources, privacy boundary, claim policy | policy text + lists |
| `ontology_map` | nine ontology dimensions: worldview, lifeview, values/bottom lines, role/mission, methodology/facts, decision/tradeoff, people/talent, business/customer or core domain, expression/organization | nine-dimension map |
| `kernel` | ultimate value order, boundaries, drivers, identity self-definition | ranked list + claims |
| `cognition` | world assumptions, attribution patterns, attention filter, analogy domains | claims + matrix/list |
| `decision_model` | decision style, information threshold, risk policy, conflict resolution, judgment patterns, pre-answer checks, forced downgrade rules | dimensions + situation-action tuples + rule list |
| `interaction_model` | communication style, relationship posture, disagreement style, questioning style | behavior pattern sentences |
| `business_domain_model` | person's core domain logic; for business figures this includes business, customer, talent, organization, data/metrics, execution loops | domain model tables/lists |
| `language_fingerprint` | sample size, measurable features, qualitative features, representative quotes | metrics + short examples |
| `best_state` | description, activation/avoid conditions, decision-quality markers | text + checklist |
| `delegation_boundary` | what the avatar can represent, cannot represent, must escalate, and must translate for public use | policy rules |
| `runtime_instructions` | must-follow, must-not-do, uncertainty policy, external knowledge pipeline | rule list |
| `validation_plan` | blind evaluation, judgment holdout, consistency scan, failure modes | test specs + thresholds |
| `confirmation_checklist` | owner confirmation questions for high-impact claims, original wording, internal-only phrases, and authorization | checklist |
| `acceptance_criteria` | concrete standards for judging whether the avatar acts like the person's judgment system, not a knowledge base | criteria list |
| `confidence_by_section` | confidence and reason per section | score/list |
| `missing_information` | targeted missing evidence prompts by module and priority | prioritized list |
| `iteration_log` | append-only update history | append-only entries |

## Required Nested Modules

`kernel`:

- `ultimate_value_order`
- `boundaries`
- `drivers`
- `identity_self_definition`

`ontology_map.dimensions`:

- `worldview`
- `lifeview`
- `values_and_bottom_lines`
- `role_and_mission`
- `methodology_and_fact_view`
- `decision_and_tradeoff_view`
- `human_and_talent_view`
- `business_and_customer_view`
- `expression_and_organization_view`

`cognition`:

- `world_assumptions`
- `attribution_patterns`
- `attention_filter`
- `analogy_domains`

`decision_model`:

- `decision_style`
- `information_threshold`
- `risk_policy`
- `conflict_resolution`
- `judgment_patterns`
- `pre_answer_checks`
- `forced_downgrade_rules`

`interaction_model`:

- `communication_style`
- `relationship_posture`
- `disagreement_style`
- `questioning_style`

`business_domain_model`:

- `business_logic`
- `customer_logic`
- `talent_logic`
- `organization_logic`
- `data_and_metrics`
- `execution_loops`

`delegation_boundary`:

- `cannot_represent`
- `can_represent`
- `private_information_policy`
- `external_translation_policy`

`runtime_instructions`:

- `must_follow`
- `must_not_do`
- `uncertainty_policy`

`validation_plan`:

- `blind_evaluation`
- `judgment_holdout`
- `consistency_scan`

`confirmation_checklist`:

- `items`

## Evidence Maturity XML

`EVIDENCE_MATURITY.xml` root:

```xml
<evidence_maturity_report schema="psp.evidence-maturity.v1" person_id="" generated_at="">
  <metadata/>
  <maturity level="scaffold|evidence-limited-v0|public-v0|research-grade|avatar-grade"/>
  <evidence_sources/>
  <unavailable_sources/>
  <incomplete_areas/>
  <failed_sources/>
  <final_disclosure/>
  <iteration_log/>
</evidence_maturity_report>
```

Allowed maturity levels:

- `scaffold`: structure exists, no evidence body has been analyzed.
- `evidence-limited-v0`: some evidence exists, but major PSP modules remain weak.
- `public-v0`: public-safe model exists with explicit limits.
- `research-grade`: broad, multi-context evidence supports most claims.
- `avatar-grade`: validation has passed enough to support production avatar behavior.

## LifeOS Mapping

| PSP XML field | LifeOS consumer |
|---|---|
| `kernel.ultimate_value_order` | runtime decision policy, avatar-description boundaries |
| `kernel.boundaries` | `security/permissions.yml`, behavior boundary rows |
| `ontology_map` | avatar ontology map and owner confirmation checklist |
| `cognition.attention_filter` | avatar operating mode |
| `decision_model.decision_style` | runtime handbook / agent response policy |
| `decision_model.pre_answer_checks` | runtime pre-answer checklist |
| `decision_model.forced_downgrade_rules` | runtime downgrade/escalation policy |
| `interaction_model.communication_style` | avatar-description communication style |
| `interaction_model.questioning_style` | runtime follow-up question policy |
| `business_domain_model` | domain-specific decision frames and execution loops |
| `language_fingerprint` | validation workflows and style fidelity disclosure |
| `best_state` | system prompt generation |
| `delegation_boundary` | authorization and public/private output boundary |
| `runtime_instructions.must_not_do` | anti-blunting and guardrail prompts |
| `validation_plan` | `identity/psp/{person_id}/validation/` |
| `confirmation_checklist` | owner alignment loop before confirming high-impact claims |
| `acceptance_criteria` | PSP acceptance review |
| `evidence_maturity` / `EVIDENCE_MATURITY.xml` | LifeOS progress and output disclosure |

## Status Rules

- Use `confirmed` only when repeated behavior across contexts supports the claim.
- Use `inferred` when multiple weak signals point in the same direction.
- Use `hypothesis` when a useful model exists but owner/reviewer alignment is pending.
- Use `unassessed` when the submodel has not been evaluated.
- Use `empty` when no content exists but the field is structurally required.
- Use `not_extractable` when available material cannot support the field.

## Runtime Safety Rules

- If `evidence_maturity.level` is `scaffold`, the agent must not imitate personality, language fingerprint, or value ordering.
- If `language_fingerprint.status` is not `confirmed` or `inferred`, the agent must not claim style fidelity.
- If `kernel.ultimate_value_order.confidence` is `insufficient`, the agent must not make high-stakes decisions as the person.
- If contradictions exist, runtime output must disclose uncertainty instead of choosing the more convenient story.

## Acceptance Criteria

A PSP run is schema-complete when:

- `scripts/psp_doctor.py <person_artifact_dir>` passes.
- `PSP_REPORT.xml` validates against `psp.report.v1` module requirements.
- `EVIDENCE_MATURITY.xml` exposes a valid maturity level.
- Every non-empty model claim has evidence pointers.
- Every unassessed or not-extractable field has `missing_evidence`.
- Language fingerprint includes sample size and confidence.
- Runtime instructions explicitly separate `must_follow` from `must_not_do`.
- Validation plan exists before any system prompt is treated as production-ready.
