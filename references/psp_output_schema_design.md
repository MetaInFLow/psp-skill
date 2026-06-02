# PSP Output Schema Design

Generated: 2026-06-02

## Purpose

PSP turns evidence about a real person into a runnable person model. The existing PSP template defines rich sections, but downstream systems need a fixed contract for what a PSP report always exposes.

This design defines the fixed output schema for PSP artifacts so LifeOS Catalog, avatar-description synthesis, runtime prompt generation, and validation workflows can consume PSP output without guessing.

## Non-Goals

- Do not reduce PSP to a personality summary.
- Do not force high-confidence values when evidence is weak.
- Do not hard-code private raw material into public LifeOS output.
- Do not make the system prompt the PSP source of truth. `PSP.md` remains the source artifact.

## Output Principle

Every PSP field must include:

- `value`: the current modeled claim or empty value.
- `status`: `confirmed`, `inferred`, `hypothesis`, `unassessed`, `empty`, or `not_extractable`.
- `confidence`: `high`, `medium`, `low`, or `insufficient`.
- `evidence`: source pointers or explicit `none`.
- `runtime_use`: how this field should or should not be used by an agent.
- `missing_evidence`: what would improve this field.

Fresh scaffolds therefore expose useful absence:

```text
Judgment model: unassessed, from PSP, evidence: none
Language fingerprint: unassessed, from PSP, requires language samples
Behavior boundary: unassessed, from PSP/Soul, evidence: none
```

## Required Artifact Set

Default PSP output:

```text
people/{person_id}/
├── PSP-YYYYMMDD-HHMMSS.md
├── PSP.md
├── PSP.summary.yml
├── evidence-map.yml
├── system_prompt-YYYYMMDD-HHMMSS.txt
└── validation/
```

LifeOS mode:

```text
identity/psp/{person_id}/
├── PSP-YYYYMMDD-HHMMSS.md
├── PSP.md
├── PSP.summary.yml
├── evidence-map.yml
├── current.yml
├── versions.yml
├── changelog.md
├── system_prompt-YYYYMMDD-HHMMSS.txt
└── validation/
```

`PSP.md` is the human-readable source model. `PSP.summary.yml` is the machine-readable contract consumed by LifeOS.

## Fixed Summary Schema

`PSP.summary.yml`:

```yaml
schema: psp.summary.v1
person_id: ""
generated_at: ""
model_maturity:
  value: scaffold
  confidence: insufficient
  evidence: []

kernel:
  ultimate_value_order:
    status: unassessed
    values: []
    confidence: insufficient
    evidence: []
    runtime_use: "Do not infer value ordering until evidence exists."
    missing_evidence: ["conflict stories", "high-stakes decisions"]
  boundaries:
    status: unassessed
    items: []
    confidence: insufficient
    evidence: []
  drivers:
    status: unassessed
    items: []
  identity_self_definition:
    status: unassessed
    values: []

cognition:
  world_assumptions:
    status: unassessed
    items: []
  attribution_patterns:
    status: unassessed
    matrix: []
  attention_filter:
    status: unassessed
    sequence: []
  analogy_domains:
    status: unassessed
    domains: []

decision:
  decision_style:
    status: unassessed
    dimensions: []
  information_threshold:
    status: unassessed
    value: null
  risk_policy:
    status: unassessed
    value: null
  conflict_resolution:
    status: unassessed
    patterns: []

interaction:
  communication_style:
    status: unassessed
    patterns: []
  relationship_posture:
    status: unassessed
    patterns: []
  disagreement_style:
    status: unassessed
    patterns: []

language_fingerprint:
  status: unassessed
  sample_size: 0
  measurable_features: []
  qualitative_features: []
  confidence: insufficient
  evidence: []
  missing_evidence: ["informal writing", "formal writing", "spoken transcripts"]

best_state:
  status: unassessed
  description: ""
  activation_conditions: []
  avoid_conditions: []

runtime_instructions:
  status: unassessed
  must_follow: []
  must_not_do: []
  uncertainty_policy: "When PSP evidence is insufficient, disclose uncertainty and route to source collection."

validation:
  status: not_started
  required_tests: []
  last_score: null
  failure_modes: []

evidence_summary:
  source_count: 0
  source_types: []
  weak_claims: []
  contradictions: []
  unavailable_sources: []
```

## Required Markdown Sections

`PSP.md` must contain these headings in this order:

1. `## Metadata`
2. `## Evidence Summary`
3. `## Kernel`
4. `## Cognition`
5. `## Decision`
6. `## Interaction`
7. `## Language Fingerprint`
8. `## Best State`
9. `## Runtime Instructions`
10. `## Confidence And Gaps`
11. `## Validation Plan`
12. `## Iteration Log`

The full PSP v2.1 16-subitem structure may remain inside these sections or as subheadings. The fixed headings are the stable consumer contract.

## Field-To-LifeOS Mapping

| PSP field | LifeOS consumer |
|---|---|
| `kernel.ultimate_value_order` | `SOUL.md`, runtime decision policy |
| `kernel.boundaries` | `SOUL.md`, `security/permissions.yml`, Catalog behavior-boundary row |
| `cognition.attention_filter` | avatar operating mode |
| `decision.decision_style` | runtime handbook / agent response policy |
| `interaction.communication_style` | avatar-description communication style |
| `language_fingerprint` | Catalog language-fingerprint row, validation workflows |
| `best_state` | system prompt generation |
| `runtime_instructions.must_not_do` | anti-blunting and guardrail prompts |
| `validation` | `identity/psp/{person_id}/validation/` |
| `evidence_summary` | `docs/evidence-sufficiency.md` |

## Status Rules

- Use `confirmed` only when repeated behavior across contexts supports the claim.
- Use `inferred` when multiple weak signals point in the same direction.
- Use `hypothesis` when a useful model exists but owner/reviewer alignment is pending.
- Use `unassessed` when the submodel has not been evaluated.
- Use `empty` when no content exists but the field is structurally required.
- Use `not_extractable` when available material cannot support the field.

## Runtime Safety Rules

- If `model_maturity.value` is `scaffold`, the agent must not imitate personality, language fingerprint, or value ordering.
- If `language_fingerprint.status` is not `confirmed` or `inferred`, the agent must not claim style fidelity.
- If `kernel.ultimate_value_order.confidence` is `insufficient`, the agent must not make high-stakes decisions as the person.
- If contradictions exist, runtime output must disclose the uncertainty instead of choosing the more convenient story.

## Acceptance Criteria

A PSP run is schema-complete when:

- `PSP.md` has every required fixed heading.
- `PSP.summary.yml` validates against `psp.summary.v1`.
- Every non-empty model claim has evidence pointers.
- Every unassessed or not-extractable field has `missing_evidence`.
- Language fingerprint includes sample size and confidence.
- Runtime instructions explicitly separate `must_follow` from `must_not_do`.
- Validation plan exists before any system prompt is treated as production-ready.
