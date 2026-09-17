# BGaming Complete Demo Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe full-catalog BGaming sweep and make BGaming farm readiness capability-driven so games are not blocked by optional capabilities they do not expose.

**Architecture:** Keep Spin-Wire deterministic. BGaming discovery/execution continues to own protocol knowledge; the new sweep only crawls once, executes many games with bounded concurrency under one Proton tunnel, and exports sanitized evidence. Optional modes explicitly marked `coverage_required=false` remain diagnostic and do not block a ready farm contract; strong/unmarked existing BGaming modes keep the current fail-closed behavior until their producer explicitly says otherwise.

**Tech Stack:** Python 3.12, requests, Playwright/Chromium, pytest/unittest, GitHub Actions Ubuntu 24.04, WireGuard/Proton.

**Spec:** `docs/superpowers/specs/2026-09-17-bgaming-complete-demo-coverage-design.md`

## Global Constraints

- Scope is BGaming only.
- Coverage is capability-driven; purchase/ante/chance/gamble are not universal requirements.
- Base `SPIN` remains mandatory for a playable demo.
- `coverage_required=false` is authoritative diagnostic-only evidence and must never block `OK`/farm readiness.
- Strong BGaming modes without an explicit override preserve current fail-closed semantics.
- No title/slug hardcoding for normal protocol families.
- Game-specific exceptions are allowed only when demonstrated, isolated, documented, and regression-tested.
- Full sweep uses one GitHub-hosted runner and one Proton WireGuard tunnel.
- Diagnostic sweep concurrency is bounded to 1-4 and starts at 3; normal BGaming GUI/provider behavior remains capped at 1.
- Raw HAR, cookies, tokens, session URLs, authorization, CSRF, and WireGuard material are never uploaded as public artifacts.
- A game-level `PARCIAL`/`ERROR` is data for diagnosis and must not crash or abort the catalog sweep.
- Protocol corrections follow TDD and are validated against existing API-v2, HyperHive, and legacy-lines controls.

---

### Task 1: Make BGaming farm readiness respect optional capabilities

**Files:**
- Modify: `tests/test_bgaming_farm_contract.py`
- Modify: `tester_spin/providers/bgaming/farm_contract.py`

**Interfaces:**
- Consumes: `GameTestResult.discovered_modes[*].coverage_required: bool | missing`
- Produces: BGaming farm-contract mode field `required: bool`; only required non-demonstrated modes contribute `MODE_NOT_DEMONSTRATED:*` unresolved reasons.

- [ ] **Step 1: Write the failing regression test for a diagnostic-only purchase**

Add to `tests/test_bgaming_farm_contract.py`:

```python
    def test_optional_literal_only_purchase_does_not_block_ready_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _write_game_json(root, profile=_profile())
            result = _result()
            result.discovered_modes.append(
                {
                    "id": "PURCHASE_LITERAL_ONLY",
                    "kind": "PURCHASE",
                    "wire_command": "spin",
                    "purchased_feature": "buy_bonus",
                    "observed": False,
                    "validated": False,
                    "executable": False,
                    "coverage_required": False,
                    "discovery_state": "DISCOVERED_LITERAL_ONLY",
                }
            )

            contract = build_bgaming_farm_contract(_game(), result, root)

            self.assertTrue(contract["ready"], contract["unresolved"])
            by_id = {mode["id"]: mode for mode in contract["modes"]}
            self.assertFalse(by_id["PURCHASE_LITERAL_ONLY"]["required"])
            self.assertEqual(by_id["PURCHASE_LITERAL_ONLY"]["evidence"], "SOLO_ANUNCIADO")
            self.assertFalse(
                any("PURCHASE_LITERAL_ONLY" in reason for reason in contract["unresolved"]),
                contract["unresolved"],
            )
```

Keep `test_unknown_feature_discovered_in_ok_run_blocks_farm_readiness` unchanged: an unmarked actionable mode still fails closed.

- [ ] **Step 2: Run the regression test and verify the current contract fails**

Run:

```bash
python -m pytest tests/test_bgaming_farm_contract.py::BGamingFarmContractTests::test_optional_literal_only_purchase_does_not_block_ready_contract -q
```

Expected: FAIL because `build_bgaming_farm_contract()` currently sets `required=True` for every discovered mode and appends `MODE_NOT_DEMONSTRATED:PURCHASE_LITERAL_ONLY:*`.

- [ ] **Step 3: Implement the minimal capability-driven requiredness rule**

In `build_bgaming_farm_contract()` replace the unconditional `required = True` and unconditional unresolved append with:

```python
        required = raw_mode.get("coverage_required") is not False

        item: dict[str, Any] = {
            "id": mode_id,
            "kind": kind,
            "required": required,
            "evidence": evidence,
            "executor": command or kind.lower(),
            "options": _mode_options(raw_mode, profile),
        }
        # ... keep existing item enrichment ...

        if required and evidence != "DEMOSTRADO":
            unresolved.append(f"MODE_NOT_DEMONSTRATED:{mode_id}:{evidence}")
```

Do not infer `required=False` merely from `executable=False` or `observed=False`; only the explicit provider signal disables coverage. This preserves current strong server-advertised and pending-flow behavior.

- [ ] **Step 4: Run BGaming farm-contract and shared contract tests**

Run:

```bash
python -m pytest -q \
  tests/test_bgaming_farm_contract.py \
  tests/test_all_provider_farm_contracts.py \
  tests/test_all_provider_execution_structure.py
```

Expected: PASS. The new optional literal test passes, and the existing unknown-feature/required-mode tests still block readiness.

- [ ] **Step 5: Commit**

```bash
git add tester_spin/providers/bgaming/farm_contract.py tests/test_bgaming_farm_contract.py
git commit -m "fix: make BGaming farm readiness capability-driven"
```

---

### Task 2: Allow bounded sweep-only BGaming concurrency without changing normal safety defaults

**Files:**
- Modify: `tests/test_bgaming_adapter.py`
- Modify: `tester_spin/providers/bgaming/adapter.py`

**Interfaces:**
- Consumes: `BGamingProvider(data_root, test_concurrency_cap: int | None = None)`
- Produces: instance-level `max_test_concurrency`; default stays `1`, explicit sweep override may be `1..4`.

- [ ] **Step 1: Write tests for default serial behavior and explicit sweep override**

Add to `tests/test_bgaming_adapter.py`:

```python
def test_bgaming_default_concurrency_remains_serial(tmp_path: Path) -> None:
    provider = BGamingProvider(tmp_path)
    assert provider.effective_test_concurrency(4) == 1


def test_bgaming_sweep_can_request_bounded_instance_concurrency(tmp_path: Path) -> None:
    provider = BGamingProvider(tmp_path, test_concurrency_cap=3)
    assert provider.effective_test_concurrency(4) == 3
```

- [ ] **Step 2: Run the new tests and verify constructor override is missing**

Run:

```bash
python -m pytest -q \
  tests/test_bgaming_adapter.py::test_bgaming_default_concurrency_remains_serial \
  tests/test_bgaming_adapter.py::test_bgaming_sweep_can_request_bounded_instance_concurrency
```

Expected: second test FAIL because the constructor does not accept `test_concurrency_cap`.

- [ ] **Step 3: Add an instance-only concurrency cap**

Change `BGamingProvider.__init__` in `tester_spin/providers/bgaming/adapter.py` to:

```python
    def __init__(
        self,
        data_root: Path,
        *,
        test_concurrency_cap: int | None = None,
    ) -> None:
        self.data_root = data_root
        self.provider_root = data_root / "providers" / self.key
        self.provider_root.mkdir(parents=True, exist_ok=True)
        self.http = self._new_session()
        if test_concurrency_cap is not None:
            self.max_test_concurrency = max(1, min(4, int(test_concurrency_cap)))
```

Keep the class attribute `max_test_concurrency = 1`; only the dedicated sweep opts into parallel execution.

- [ ] **Step 4: Run adapter and scheduler regressions**

Run:

```bash
python -m pytest -q tests/test_bgaming_adapter.py tests/test_scheduler.py
```

If `tests/test_scheduler.py` is not present, run:

```bash
python -m pytest -q tests/test_bgaming_adapter.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tester_spin/providers/bgaming/adapter.py tests/test_bgaming_adapter.py
git commit -m "feat: allow bounded BGaming sweep concurrency"
```

---

### Task 3: Add a deterministic full/cohort BGaming sweep runner

**Files:**
- Create: `tester_spin/action_sanitize.py`
- Modify: `tester_spin/action_bgaming_diagnostic.py`
- Create: `tester_spin/action_bgaming_sweep.py`
- Create: `tests/test_action_bgaming_sweep.py`
- Modify: `tests/test_action_bgaming_diagnostic.py`

**Interfaces:**
- Produces: `sanitize_action_value(value: Any) -> Any`
- Produces: `copy_safe_diagnostics(run_dir: Path, output_dir: Path) -> list[str]`
- Produces: `load_sweep_config(path: Path) -> SweepConfig`
- Produces: `resolve_sweep_games(games: Iterable[Game], targets: list[str]) -> list[Game]`
- Produces: `build_sweep_record(provider: BGamingProvider, game: Game, result: GameTestResult) -> dict[str, Any]`
- CLI: `python -m tester_spin.action_bgaming_sweep --config <json> --data-root <dir> --output-dir <dir>`

- [ ] **Step 1: Extract the existing action sanitizer without changing behavior**

Create `tester_spin/action_sanitize.py` with the existing sanitizer/copy behavior from `action_bgaming_diagnostic.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tester_spin.providers.bgaming.runtime import sanitize_error_text, sanitize_session_url
from tester_spin.run_diagnostics import sanitize


def sanitize_action_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize_action_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_action_value(item) for item in value]
    if isinstance(value, str):
        cleaned = sanitize_error_text(value)
        if cleaned.startswith(("http://", "https://")):
            cleaned = sanitize_session_url(cleaned)
        return sanitize(cleaned)
    return value


def copy_safe_diagnostics(run_dir: Path, output_dir: Path) -> list[str]:
    copied: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("diagnostic.json", "diagnostic.md"):
        source = run_dir / name
        if not source.is_file():
            continue
        target = output_dir / name
        if source.suffix == ".json":
            try:
                value = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            target.write_text(
                json.dumps(sanitize_action_value(value), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            target.write_text(
                str(sanitize_action_value(source.read_text(encoding="utf-8", errors="replace"))),
                encoding="utf-8",
            )
        copied.append(name)
    return copied
```

Modify `action_bgaming_diagnostic.py` to import both functions and replace `_sanitize_value(...)` calls with `sanitize_action_value(...)`. Keep `copy_safe_diagnostics` imported into the module namespace so the existing tests remain valid.

- [ ] **Step 2: Run diagnostic sanitizer regressions**

Run:

```bash
python -m pytest -q tests/test_action_bgaming_diagnostic.py
```

Expected: PASS with the same redaction and safe-copy behavior as before.

- [ ] **Step 3: Write sweep config/selection/result tests before the runner**

Create `tests/test_action_bgaming_sweep.py` with these cases:

```python
from __future__ import annotations

import json
from pathlib import Path

from tester_spin.action_bgaming_sweep import (
    SweepConfig,
    build_sweep_summary,
    load_sweep_config,
    resolve_sweep_games,
)
from tester_spin.models import Game, GameTestResult


def _game(name: str, slug: str, symbol: str = "") -> Game:
    return Game(
        provider="bgaming",
        slug=slug,
        name=name,
        url=f"https://bgaming.com/games/{slug}/",
        symbol=symbol,
    )


def test_load_sweep_config_bounds_concurrency(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "concurrency": 3,
        "spins": 1,
        "timeout_seconds": 60,
        "max_catalog_pages": 100,
        "targets": ["*"],
        "run_nonce": "baseline",
    }), encoding="utf-8")
    config = load_sweep_config(path)
    assert config == SweepConfig(3, 1, 60.0, 100, ("*",), "baseline")


def test_resolve_sweep_games_supports_all_and_exact_cohorts() -> None:
    games = [
        _game("Alien Fruits 3", "alien-fruits-3", "alienfruits3"),
        _game("Multi Rush", "multi-rush", "multirush"),
    ]
    assert resolve_sweep_games(games, ["*"]) == games
    assert [g.slug for g in resolve_sweep_games(games, ["Multi Rush"])] == ["multi-rush"]
    assert [g.slug for g in resolve_sweep_games(games, ["alienfruits3"])] == ["alien-fruits-3"]


def test_sweep_summary_preserves_ok_but_not_ready_signal() -> None:
    result = GameTestResult(
        provider="bgaming",
        slug="fixture",
        game_name="Fixture",
        game_url="https://bgaming.com/games/fixture/",
        requested_spins=1,
        successful_spins=1,
        failed_spins=0,
        status="OK",
    )
    records = [{
        "slug": "fixture",
        "game_name": "Fixture",
        "status": "OK",
        "farm_ready": False,
        "farm_unresolved": ["MODE_NOT_DEMONSTRATED:PURCHASE_X:SOLO_ANUNCIADO"],
    }]
    summary = build_sweep_summary(catalog_size=1, selected_size=1, records=records)
    assert summary["status_counts"] == {"OK": 1}
    assert summary["ok_not_ready_count"] == 1
    assert summary["ok_not_ready"] == ["fixture"]
```

Also add a config validation test asserting concurrency `0` or `5` raises `ValueError` rather than silently creating uncontrolled parallelism.

- [ ] **Step 4: Run the sweep tests and verify the module does not exist**

Run:

```bash
python -m pytest -q tests/test_action_bgaming_sweep.py
```

Expected: collection/import FAIL because `tester_spin.action_bgaming_sweep` has not been created.

- [ ] **Step 5: Implement the sweep runner**

Create `tester_spin/action_bgaming_sweep.py` with a frozen config dataclass and strict config parser:

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SweepConfig:
    concurrency: int
    spins: int
    timeout_seconds: float
    max_catalog_pages: int
    targets: tuple[str, ...]
    run_nonce: str = ""
```

`load_sweep_config()` must reject concurrency outside `1..4`, spins/max pages below `1`, timeout below `1`, non-list targets, and an empty target list.

`resolve_sweep_games()` must return all games for exactly `targets == ["*"]`; otherwise resolve every target through the existing `select_game()` helper, de-duplicate by `(provider, slug)`, and never use substring ambiguity silently.

`build_sweep_record()` must export only sanitized diagnostic data. Read `analysis/farm-contract-candidate.json` from `provider.game_dir(game)` when present and include:

```python
{
    "slug": result.slug,
    "game_name": result.game_name,
    "symbol": result.symbol,
    "status": result.status,
    "successful_spins": result.successful_spins,
    "failed_spins": result.failed_spins,
    "error": sanitize_action_value(result.error),
    "farm_ready": bool(candidate.get("ready")),
    "farm_unresolved": sanitize_action_value(candidate.get("unresolved") or []),
    "protocol_family": str((candidate.get("source") or {}).get("protocol_family") or ""),
    "modes": [
        {
            key: sanitize_action_value(mode.get(key))
            for key in (
                "id", "kind", "observed", "validated", "executable",
                "coverage_required", "discovery_state", "evidence_level",
                "execution_state", "source",
            )
            if key in mode
        }
        for mode in result.discovered_modes
        if isinstance(mode, dict)
    ],
}
```

`build_sweep_summary()` must sort records by `(status, game_name.casefold(), slug)` and return:

```python
{
    "schema": "spin-wire/action-bgaming-sweep/v1",
    "catalog_size": catalog_size,
    "selected_size": selected_size,
    "completed_size": len(records),
    "status_counts": status_counts,
    "ok_not_ready_count": len(ok_not_ready),
    "ok_not_ready": sorted(ok_not_ready),
    "results": sorted_records,
}
```

The CLI must:

```python
provider = BGamingProvider(data_root, test_concurrency_cap=config.concurrency)
games = provider.crawl_catalog(...)
selected = resolve_sweep_games(games, list(config.targets))
run_game_tests(
    provider,
    selected,
    concurrency=config.concurrency,
    spins_per_game=config.spins,
    delay_between_starts_s=0.25,
    timeout_s=config.timeout_seconds,
    stop_event=stop_event,
    progress=progress,
    on_result=on_result,
)
```

`on_result` must append a record and immediately checkpoint it as `output_dir/results/<slug>.json`, so one failing game or later runner interruption does not erase already-finished evidence. For every result whose `status != "OK"` **or** whose `farm_ready` is false, copy only `diagnostic.json` and `diagnostic.md` into `output_dir/games/<slug>/` via `copy_safe_diagnostics()`.

Write/update `summary.json` after every completed game and once at the end. Return exit code `0` when the catalog/scheduler infrastructure ran even if individual games are `PARCIAL`, `ERROR`, or `SIN_DEMO`; return `2` only for sweep-level infrastructure failure.

Do not copy `browser.har`, request/response raw files, `game.json`, profile files, cookies, or launch URLs into the output artifact.

- [ ] **Step 6: Run sweep unit tests plus existing diagnostic tests**

Run:

```bash
python -m pytest -q \
  tests/test_action_bgaming_sweep.py \
  tests/test_action_bgaming_diagnostic.py \
  tests/test_bgaming_farm_contract.py \
  tests/test_path_coverage.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add \
  tester_spin/action_sanitize.py \
  tester_spin/action_bgaming_diagnostic.py \
  tester_spin/action_bgaming_sweep.py \
  tests/test_action_bgaming_sweep.py \
  tests/test_action_bgaming_diagnostic.py
git commit -m "feat: add BGaming catalog sweep runner"
```

---

### Task 4: Add a one-tunnel Proton Actions workflow controlled by a declarative sweep config

**Files:**
- Create: `.github/workflows/bgaming-proton-sweep.yml`
- Create: `.github/bgaming-sweep-config.json`

**Interfaces:**
- Consumes repo secret: `PROTON_WG_CONF_B64`
- Consumes config: `.github/bgaming-sweep-config.json`
- Produces artifact: `bgaming-proton-sweep-${{ github.run_id }}` containing only `action-sweep/` sanitized output.

- [ ] **Step 1: Add the declarative initial sweep config**

Create `.github/bgaming-sweep-config.json`:

```json
{
  "concurrency": 3,
  "spins": 1,
  "timeout_seconds": 60,
  "max_catalog_pages": 100,
  "targets": ["*"],
  "run_nonce": "baseline-1"
}
```

Changing `targets`, `concurrency`, or `run_nonce` is the only control needed for later cohort/full reruns. No game rule lives in this file.

- [ ] **Step 2: Create the Proton sweep workflow**

Create `.github/workflows/bgaming-proton-sweep.yml` with:

```yaml
name: BGaming Proton sweep

on:
  workflow_dispatch:
  push:
    branches:
      - feat/farm-contract-export-v1
    paths:
      - ".github/workflows/bgaming-proton-sweep.yml"
      - ".github/bgaming-sweep-config.json"

permissions:
  contents: read

concurrency:
  group: bgaming-proton-sweep
  cancel-in-progress: false

jobs:
  sweep:
    runs-on: ubuntu-latest
    timeout-minutes: 300
    env:
      PYTHONUNBUFFERED: "1"
      TESTER_SPIN_PUBLISH_RESULTS: "0"

    steps:
      - name: Checkout Spin-Wire
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        shell: bash
        run: |
          set -euo pipefail
          python -m pip install --disable-pip-version-check -r requirements.txt pytest
          python -m playwright install --with-deps chromium

      - name: Verify sweep and BGaming gates
        shell: bash
        run: |
          set -euo pipefail
          python -m compileall -q tester_spin/action_bgaming_sweep.py
          python -m pytest -q \
            tests/test_action_bgaming_sweep.py \
            tests/test_action_bgaming_diagnostic.py \
            tests/test_bgaming_farm_contract.py \
            tests/test_bgaming_hyperhive_purchase_evidence.py \
            tests/test_path_coverage.py

      - name: Install WireGuard tools
        shell: bash
        run: |
          set -euo pipefail
          sudo apt-get update -y
          sudo DEBIAN_FRONTEND=noninteractive apt-get install -y wireguard-tools resolvconf

      - name: Record direct runner egress
        shell: bash
        run: |
          set -euo pipefail
          mkdir -p action-sweep
          curl --fail --silent --show-error --max-time 20 -4 https://api.ipify.org > action-sweep/egress-before.txt

      - name: Configure Proton WireGuard
        shell: bash
        env:
          PROTON_WG_CONF_B64: ${{ secrets.PROTON_WG_CONF_B64 }}
        run: |
          set -euo pipefail
          test -n "${PROTON_WG_CONF_B64:-}"
          umask 077
          printf '%s' "$PROTON_WG_CONF_B64" | base64 --decode > proton.conf
          sudo install -m 600 proton.conf /etc/wireguard/proton.conf
          rm -f proton.conf

      - name: Connect Proton and verify tunnel
        shell: bash
        run: |
          set -euo pipefail
          sudo wg-quick up proton
          sleep 3
          before_ip="$(cat action-sweep/egress-before.txt)"
          after_ip="$(curl --fail --silent --show-error --max-time 20 -4 https://api.ipify.org)"
          handshake="$(sudo wg show proton latest-handshakes | awk '{print $2}' | sort -nr | head -1)"
          test "${handshake:-0}" -gt 0
          test "$after_ip" != "$before_ip"
          printf '%s\n' "$after_ip" > action-sweep/egress-proton.txt

      - name: Run BGaming sweep
        shell: bash
        env:
          RUNNER_TEMP_DIR: ${{ runner.temp }}
        run: |
          set -euo pipefail
          python -m tester_spin.action_bgaming_sweep \
            --config .github/bgaming-sweep-config.json \
            --data-root "$RUNNER_TEMP_DIR/spin-wire-bgaming-data" \
            --output-dir action-sweep

      - name: Disconnect Proton and remove config
        if: always()
        shell: bash
        run: |
          sudo wg-quick down proton >/dev/null 2>&1 || true
          sudo rm -f /etc/wireguard/proton.conf
          rm -f proton.conf

      - name: Publish sweep summary
        if: always()
        shell: bash
        run: |
          if [ -f action-sweep/summary.json ]; then
            echo '### BGaming sweep' >> "$GITHUB_STEP_SUMMARY"
            echo '```json' >> "$GITHUB_STEP_SUMMARY"
            python - <<'PY' >> "$GITHUB_STEP_SUMMARY"
          import json
          from pathlib import Path
          data = json.loads(Path('action-sweep/summary.json').read_text())
          print(json.dumps({
              'catalog_size': data.get('catalog_size'),
              'selected_size': data.get('selected_size'),
              'completed_size': data.get('completed_size'),
              'status_counts': data.get('status_counts'),
              'ok_not_ready_count': data.get('ok_not_ready_count'),
          }, indent=2))
          PY
            echo '```' >> "$GITHUB_STEP_SUMMARY"
          fi

      - name: Upload sanitized sweep evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: bgaming-proton-sweep-${{ github.run_id }}
          path: action-sweep/
          if-no-files-found: warn
          retention-days: 7
```

The workflow intentionally does not upload `$RUNNER_TEMP_DIR/spin-wire-bgaming-data`.

- [ ] **Step 3: Validate workflow-adjacent Python tests before relying on the live run**

Run locally/CI:

```bash
python -m pytest -q \
  tests/test_action_bgaming_sweep.py \
  tests/test_bgaming_farm_contract.py \
  tests/test_bgaming_adapter.py \
  tests/test_bgaming_hyperhive_purchase_evidence.py \
  tests/test_path_coverage.py
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/bgaming-proton-sweep.yml .github/bgaming-sweep-config.json
git commit -m "ci: add Proton BGaming catalog sweep"
```

---

### Task 5: Run the first full sweep and establish the remaining cohorts

**Files:**
- Modify only when a rerun is needed: `.github/bgaming-sweep-config.json`
- Read artifacts only; do not commit generated game data or HAR files.

**Interfaces:**
- Consumes: `action-sweep/summary.json` and per-game sanitized diagnostics from the Actions artifact.
- Produces: a concrete list of remaining BGaming non-OK/OK-not-ready cohorts for subsequent bounded debugging tasks.

- [ ] **Step 1: Trigger the baseline full sweep**

Ensure config is:

```json
{
  "concurrency": 3,
  "spins": 1,
  "timeout_seconds": 60,
  "max_catalog_pages": 100,
  "targets": ["*"],
  "run_nonce": "baseline-1"
}
```

The config/workflow creation commit triggers `BGaming Proton sweep` automatically on `feat/farm-contract-export-v1`.

- [ ] **Step 2: Verify sweep infrastructure rather than demanding every game pass**

The Actions job is a valid baseline when:

- Proton reports a handshake and changed public IPv4;
- the catalog crawl is authoritative;
- `summary.json.catalog_size == summary.json.selected_size` for `targets=["*"]`;
- `summary.json.completed_size == summary.json.selected_size`;
- every completed game has a checkpoint record;
- game-level `PARCIAL`/`ERROR` rows are present in the summary instead of aborting the job.

- [ ] **Step 3: Download and inspect only the sanitized artifact**

Group the result records externally by:

```text
status
protocol_family
farm_ready
farm_unresolved
discovered mode discovery_state/evidence_level/execution_state
error text / server error code
```

First priority is `status=OK && farm_ready=false`, because these are direct candidates for capability/readiness false positives. Next are true `PARCIAL`, then protocol `ERROR`; `SIN_DEMO` is checked separately against current public demo availability.

- [ ] **Step 4: Establish a concurrency fallback rule from evidence**

If the full sweep shows a broad cluster of transient network/HTTP 502/session failures across otherwise unrelated protocol families, rerun only those slugs with:

```json
{
  "concurrency": 1,
  "spins": 1,
  "timeout_seconds": 60,
  "max_catalog_pages": 100,
  "targets": ["slug-a", "slug-b", "slug-c"],
  "run_nonce": "serial-network-check-1"
}
```

If the serial cohort clears, keep concurrency 3 for discovery speed but classify the parallel failures as transport/concurrency noise rather than protocol bugs. If the same failures persist serially, treat them as real protocol/demo cohorts.

- [ ] **Step 5: Verify established control families after the baseline changes**

Use the existing single-game diagnostic workflow or a sweep cohort containing:

```json
{
  "targets": [
    "Alien Fruits 3",
    "Adventures",
    "Multi Rush",
    "Elvis Frog in Vegas",
    "Aztec's Claw Wild Dice"
  ]
}
```

Expected:

- API-v2 controls remain `OK`;
- HyperHive `Multi Rush` remains `OK`;
- legacy-lines `Elvis Frog in Vegas` remains `OK`;
- Aztec's literal-only purchase does not create required purchase coverage or block farm readiness.

- [ ] **Step 6: Record the baseline commit/run IDs in the debugging notes before starting cohort-specific fixes**

Use the Actions run ID and current Git commit SHA as the comparison baseline. Each subsequent protocol fix is a separate bounded TDD/debugging task: reproduce one cohort cause, fix the generic rule, rerun that cohort, then rerun the full catalog after the last cohort clears.
