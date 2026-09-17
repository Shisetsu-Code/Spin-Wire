from __future__ import annotations

import requests

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


def test_contract_evidence_traces_identifier_passed_as_params_req() -> None:
    text = (
        'const r={};r.bet=stake;r.bet_type="bet";'
        'const request={method:"play",params:{token:t,req:r}};'
    )

    evidence = hyperhive_wire._wire_contract_evidence(text)

    assert evidence["params_req_identifier"] is True
    assert evidence["req_alias_bet_dot_assignment"] is True
    assert evidence["req_alias_bet_type_dot_assignment"] is True


def test_contract_evidence_traces_req_alias_object_bet_fields() -> None:
    text = (
        'const r={bet:stake,bet_type:"bet"};'
        'const request={method:"play",params:{token:t,req:r}};'
    )
    shorthand = (
        'const bet=stake;const r={bet};'
        'const request={method:"play",params:{token:t,req:r}};'
    )

    evidence = hyperhive_wire._wire_contract_evidence(text)
    shorthand_evidence = hyperhive_wire._wire_contract_evidence(shorthand)

    assert evidence["req_alias_object_bet_value"] is True
    assert shorthand_evidence["req_alias_object_bet_shorthand"] is True


def test_mode_diagnostic_metadata_preserves_source_free_contract_evidence() -> None:
    mode = {
        "id": "SPIN",
        "kind": "SPIN",
        "request": {"bet_type": "bet"},
        "source": "live-client-evidence-incomplete",
        "executable": False,
        "discovery_state": "CONTRACT_UNRESOLVED",
        "contract_evidence": {
            "method_play": True,
            "req_bet_shorthand": True,
            "bet_token_count": 4,
            "syntax_signatures": ["method_play", "req_bet_shorthand"],
        },
    }

    metadata = hyperhive._mode_diagnostic_metadata(mode)

    assert metadata["contract_evidence"]["req_bet_shorthand"] is True
    assert metadata["request_options"] == {"bet_type": "bet"}
