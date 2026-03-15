# AI Interview Evaluation Engine Constitution

## Core Principles

### I. Backend-First Product Scope

This project is a backend system for simulating technical interviews and evaluating candidate responses with large language models. Features must directly support interview orchestration, prompt execution, response evaluation, scoring, feedback generation, or the APIs and jobs required to run them.

### II. Structured and Traceable Evaluation

All interview and evaluation flows must produce structured inputs and outputs. Prompts, model responses, scores, rationales, and final decisions must be representable as explicit schemas so runs can be replayed, inspected, and compared.

### III. Safety and Fairness by Default

Candidate evaluation must avoid hidden criteria and unsupported conclusions. Prompts and scoring logic must prefer role-relevant evidence, clear rubrics, and bounded outputs; personally sensitive or irrelevant attributes must not influence evaluation.

### IV. Testable LLM Integration

LLM-dependent logic must be isolated behind clear interfaces so core business rules can be tested without live model calls. Critical paths require deterministic tests for schema validation, scoring rules, and failure handling when model output is missing, malformed, or incomplete.

### V. Simplicity and Observability

Start with the simplest design that supports reliable interview execution and evaluation. Services must emit logs and status information sufficient to debug prompt failures, model failures, and scoring discrepancies without adding unnecessary architectural complexity.

## Technical Guardrails

- Prefer explicit service boundaries between interview orchestration, prompt construction, model access, evaluation, and persistence.
- Persist evaluation artifacts needed for auditability, including rubric version, prompt version, model identifier, and normalized result payloads.
- Use versioned schemas for any stored or externally exposed evaluation result.
- Treat external model providers as unreliable dependencies: enforce timeouts, retries only when safe, and clear fallback or failure states.
- Do not ship features that require manual interpretation of raw model text when a stable structured response format is feasible.

## Delivery Workflow

- New work should start from a written spec that states the interview scenario, evaluation objective, inputs, outputs, and failure conditions.
- Changes that affect scoring, rubrics, prompts, or result schemas must include tests and a brief note on backward-compatibility impact.
- Reviews must check three things before approval: the feature is in scope for the evaluation engine, the evaluation path is auditable, and the change remains simple enough to operate.

## Governance

This constitution governs planning, specs, tasks, and implementation guidance in this repository. When a spec or plan conflicts with these principles, this document takes precedence. Amendments must update this file directly and keep the rules minimal, explicit, and relevant to the evaluation engine.

**Version**: 1.0.0 | **Ratified**: 2026-03-14 | **Last Amended**: 2026-03-14
