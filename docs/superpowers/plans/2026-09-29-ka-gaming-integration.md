# KA Gaming Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add KA Gaming as a catalogued, fail-closed Tester-Spin provider.

**Architecture:** A provider-local catalogue module retrieves and validates the public KA Gaming payload using a browser-like HTTP session. The adapter maps validated records to neutral games and creates sanitized runtime-discovery evidence; no wager, purchase or continuation request is sent until it is proven by observed traffic.

**Tech Stack:** Python, curl_cffi, pytest, existing Tester-Spin provider interfaces.

**Spec:** `docs/superpowers/specs/2026-09-29-ka-gaming-design.md`

## Global Constraints

- Treat a catalog as authoritative only when status, declared count, IDs and launch URL validate.
- Never persist access/session credentials or promote unproven gameplay to `OK`.
- Keep protocol code and artifacts provider-local; do not modify existing providers.

## Review Focus

- A 403 from a generic HTTP client must not cause a partial catalogue to reconcile destructively.
- A duplicate or missing game ID must abort the catalog before emitting games.
- Invalid or non-HTTPS launch bases must be rejected.
- Runtime discovery with no demonstrated spin contract must return `PARCIAL` and preserve sanitized evidence.
- Stop requests must prevent later catalog pages or runtime work.

---

### Task 1: KA Gaming catalog contract

**Files:**
- Create: `tester_spin/providers/ka_gaming/catalog.py`
- Create: `tests/test_ka_gaming_catalog.py`

**Interfaces:**
- Produces `fetch_catalog(...)`, `validate_catalog(payload)`, `games_from_catalog(payload, language)` and `build_launch_url(...)`.

- [ ] Write fixture tests for valid records, count mismatch, duplicate/missing IDs, invalid launch URL and deterministic required launch query fields.
- [ ] Run `pytest tests/test_ka_gaming_catalog.py -v` and confirm the new imports fail.
- [ ] Implement the minimal validated catalogue parser with a provider-local curl_cffi browser fingerprint.
- [ ] Re-run `pytest tests/test_ka_gaming_catalog.py -v` and confirm it passes.
- [ ] Commit catalog parser and tests.

### Task 2: Isolated provider adapter and conservative runtime discovery

**Files:**
- Create: `tester_spin/providers/ka_gaming/adapter.py`
- Create: `tester_spin/providers/ka_gaming/__init__.py`
- Create: `tester_spin/providers/ka_gaming/farm_adapter.py`
- Modify: `tester_spin/providers/__init__.py`
- Test: `tests/test_ka_gaming_provider.py`

**Interfaces:**
- Consumes `games_from_catalog(...)`.
- Produces `KAGamingProvider` implementing `ProviderAdapter`.

- [ ] Write a failing adapter test proving only valid catalog data becomes a `Game` and an unproven runtime returns `PARCIAL`.
- [ ] Run the focused provider test and confirm it fails because KA Gaming is not registered.
- [ ] Implement provider registration, artifact location and sanitized discovery result without transmitting a guessed game action.
- [ ] Re-run focused tests and the provider registry tests.
- [ ] Commit adapter, registration and tests.

### Task 3: Documentation and verification

**Files:**
- Modify: `README.md`
- Modify: `docs/PROTOCOLS.md`
- Test: `tests/test_ka_gaming_catalog.py`, `tests/test_ka_gaming_provider.py`

- [ ] Document the catalog source, fail-closed runtime state and evidence needed to implement a spin contract.
- [ ] Run focused tests, the full pytest suite and compile check.
- [ ] Run a bounded live catalog smoke test; report the observed count without claiming runtime validation.
- [ ] Commit documentation and verification-safe changes.
