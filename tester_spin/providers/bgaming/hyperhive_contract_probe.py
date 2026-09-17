from __future__ import annotations

import re
import threading
from typing import Any


_install_lock = threading.Lock()
_installed = False


def _wire_contract_evidence(text: str) -> dict[str, Any]:
    """Return source-free syntax evidence for HyperHive request discovery.

    The report intentionally contains only booleans/counts and symbolic pattern
    names. It never returns client source, string literal contents, URLs, tokens,
    or session material, so it can be embedded in sanitized Actions diagnostics.
    """
    compact = re.sub(r"\s+", "", text or "")
    patterns = {
        "method_play": r'(?:\bmethod|["\']method["\'])\s*:\s*["\']play["\']',
        "params_req_object": r'\bparams\s*:\s*\{[^{}]{0,2000}\breq\s*:',
        "params_req_property": r'\.params\.req\b',
        "req_bet_object_value": r'\breq\s*:\s*\{[^{}]{0,2000}\bbet\s*:',
        "req_bet_dot_assignment": r'\.req\.bet\s*=',
        "req_bet_bracket_assignment": r'\.req\[["\']bet["\']\]\s*=',
        # Minified ES2015 clients often serialize `{req:{bet,bet_type:"bet"}}`.
        # Object shorthand is semantically the same field presence as `bet:x`.
        "req_bet_shorthand": (
            r'\breq\s*:\s*\{(?:bet(?=[,}])|[^{}]{0,2000},bet(?=[,}]))'
        ),
        "req_bet_type_object": r'\breq\s*:\s*\{[^{}]{0,2000}\bbet_type\s*:',
        "req_bet_type_dot_assignment": r'\.req\.bet_type\s*=',
        "req_bet_type_bracket_assignment": r'\.req\[["\']bet_type["\']\]\s*=',
        "custom_req": r'\bcustom_req\b',
        "jsonrpc": r'\bjsonrpc\b',
    }
    evidence: dict[str, Any] = {
        name: bool(re.search(pattern, compact))
        for name, pattern in patterns.items()
    }
    evidence["bet_token_count"] = min(9999, len(re.findall(r"\bbet\b", compact)))
    evidence["req_token_count"] = min(9999, len(re.findall(r"\breq\b", compact)))
    evidence["bet_type_token_count"] = min(9999, len(re.findall(r"\bbet_type\b", compact)))
    evidence["syntax_signatures"] = sorted(
        name for name, matched in evidence.items()
        if isinstance(matched, bool) and matched
    )
    return evidence


def install_contract_probe() -> None:
    """Attach safe structural evidence to modes without changing execution."""
    global _installed
    with _install_lock:
        if _installed:
            return

        from tester_spin.providers.bgaming import hyperhive

        original_discover_modes = hyperhive.discover_modes_from_bundle

        def probed_discover_modes(
            runtime,
            *,
            timeout_s: float,
            bundle_text: str | None = None,
            engine_contract: str = "",
        ):
            modes = original_discover_modes(
                runtime,
                timeout_s=timeout_s,
                bundle_text=bundle_text,
                engine_contract=engine_contract,
            )
            resolved_bundle = bundle_text or ""
            try:
                refreshed = hyperhive._download_bundle(runtime, timeout_s)
                if refreshed:
                    resolved_bundle = refreshed
            except Exception:
                pass
            evidence = _wire_contract_evidence(
                resolved_bundle + "\n" + (engine_contract or "")
            )
            base = next(
                (
                    mode for mode in modes
                    if isinstance(mode, dict) and str(mode.get("id") or "") == "SPIN"
                ),
                None,
            )
            if isinstance(base, dict):
                base["contract_evidence"] = evidence
            return modes

        hyperhive.discover_modes_from_bundle = probed_discover_modes
        _installed = True


__all__ = ["_wire_contract_evidence", "install_contract_probe"]
