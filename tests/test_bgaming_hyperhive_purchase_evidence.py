from __future__ import annotations

import requests

# Import the active provider package so the same production HyperHive adapters
# used by the GUI and Actions runner are installed for these tests.
from tester_spin.providers.bgaming import BGamingProvider  # noqa: F401
from tester_spin.providers.bgaming import hyperhive, hyperhive_wire
from tester_spin.providers.bgaming.runtime import BGamingRuntime


def _runtime() -> BGamingRuntime:
    return BGamingRuntime(
        session=requests.Session(),
        launch_url="https://game.demo.bgaming-network.com/hyperhive?launch_token=x",
        api_url="https://game.demo.bgaming-network.com/api",
        identifier="Fixture",
        csrf_header_name="X-CSRF-Token",
        csrf_header_value="csrf",
        options={},
        round_series_id=1,
    )


def test_known_purchase_literal_without_req_scope_is_discovery_only() -> None:
    runtime = _runtime()
    try:
        # The base play serializer is proven, but buy_bonus is only a loose
        # client literal. That proves vocabulary, not that this game's live
        # request serializer/menu makes the purchase available.
        bundle = (
            'var request={req:{bet:stake,bet_type:"bet"}};'
            'function metadata(){return {purchased_feature:"buy_bonus"}};'
        )
        modes = hyperhive.discover_modes_from_bundle(
            runtime,
            timeout_s=1,
            bundle_text=bundle,
            engine_contract="",
        )
    finally:
        runtime.session.close()

    by_id = {str(mode["id"]): mode for mode in modes}
    purchase = by_id["PURCHASE_BUY_BONUS"]
    assert purchase["executable"] is False
    assert purchase["discovery_state"] == "DISCOVERED_LITERAL_ONLY"
    assert purchase["coverage_required"] is False


def test_request_scoped_purchase_literal_remains_executable() -> None:
    runtime = _runtime()
    try:
        bundle = (
            'var request={req:{bet:stake,bet_type:"bet",'
            'purchased_feature:"buy_bonus"}};'
        )
        modes = hyperhive.discover_modes_from_bundle(
            runtime,
            timeout_s=1,
            bundle_text=bundle,
            engine_contract="",
        )
    finally:
        runtime.session.close()

    by_id = {str(mode["id"]): mode for mode in modes}
    purchase = by_id["PURCHASE_BUY_BONUS"]
    assert purchase["executable"] is True
    assert purchase["discovery_state"] == "WIRE_PATTERN"
    assert purchase.get("coverage_required") is not False


def test_contract_evidence_reports_structure_without_source_literals() -> None:
    text = (
        'const secretValue="do-not-export";'
        'const request={method:"play",params:{req:{bet,bet_type:"bet"}}};'
        'payload.params.req["bet"]=stake;'
    )

    evidence = hyperhive_wire._wire_contract_evidence(text)

    assert evidence["method_play"] is True
    assert evidence["req_bet_shorthand"] is True
    assert evidence["req_bet_bracket_assignment"] is True
    assert evidence["bet_token_count"] >= 2
    assert evidence["req_token_count"] >= 2
    assert "syntax_signatures" in evidence
    serialized = repr(evidence)
    assert "do-not-export" not in serialized
    assert "secretValue" not in serialized
