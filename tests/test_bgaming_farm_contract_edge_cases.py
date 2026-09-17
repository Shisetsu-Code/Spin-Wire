from __future__ import annotations

import json
from pathlib import Path

from tester_spin.models import Game, GameTestResult
from tester_spin.providers import BGamingProvider
from tester_spin.providers.bgaming.farm_contract import build_bgaming_farm_contract
from tester_spin.providers.bgaming.profile import API_V2, PROFILE_SCHEMA, SWITCHABLE


def _game(*, slug: str = "fixture", name: str = "Fixture", symbol: str = "Fixture") -> Game:
    return Game(
        provider="bgaming",
        slug=slug,
        name=name,
        url=f"https://bgaming.com/games/{slug}/",
        symbol=symbol,
    )


def _profile(family: str) -> dict:
    return {
        "schema": PROFILE_SCHEMA,
        "capability_version": 2,
        "family": family,
        "confidence": 1.0,
        "evidence": ["fixture"],
        "spin_options": {},
        "command_options": {},
        "request_extra_data": {},
        "spin_option_choices": {},
        "effective_bet_selector": "",
        "effective_bet_multipliers": {},
        "dynamic_purchased_feature": False,
        "purchase_feature_level_supported": False,
        "purchase_features": [],
        "rows_required": False,
        "line_count": 0,
        "variable_layout": False,
        "allowed_continuations": [],
        "source": "fixture",
        "bundle_sha256": "a" * 64,
        "discovery_diagnostics": [],
        "validated": True,
    }


def _write_metadata(root: Path, game: Game, family: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "game.json").write_text(
        json.dumps(
            {
                "provider": "bgaming",
                "slug": game.slug,
                "name": game.name,
                "public_url": game.url,
                "identifier": game.symbol,
                "provider_protocol": _profile(family),
            }
        ),
        encoding="utf-8",
    )


def test_completed_choice_coverage_is_demonstrated_farm_evidence(tmp_path: Path) -> None:
    game = _game()
    _write_metadata(tmp_path, game, API_V2)
    result = GameTestResult(
        provider="bgaming",
        slug=game.slug,
        game_name=game.name,
        game_url=game.url,
        requested_spins=3,
        successful_spins=3,
        failed_spins=0,
        status="OK",
        symbol=game.symbol,
        discovered_modes=[
            {
                "id": "SPIN",
                "kind": "SPIN",
                "wire_command": "spin",
                "observed": True,
                "validated": True,
                "evidence_level": "REMOTE_EXECUTION",
                "execution_state": "PROVEN_TERMINAL",
            },
            {
                "id": "BGAMING_FLOW_CHOICE_FIXTURE",
                "kind": "CHOICE_CONTINUATION",
                "wire_command": "pick_cards",
                "observed": True,
                "executable": True,
                "coverage_required": True,
                "required_options": ["left", "right"],
                "covered_options": ["left", "right"],
                "required_samples": 1,
                "sample_counts": {"left": 1, "right": 1},
            },
        ],
    )

    contract = build_bgaming_farm_contract(game, result, tmp_path)

    by_id = {mode["id"]: mode for mode in contract["modes"]}
    assert by_id["BGAMING_FLOW_CHOICE_FIXTURE"]["evidence"] == "DEMOSTRADO"
    assert contract["ready"] is True, contract["unresolved"]


def test_switchable_variants_satisfy_base_wager_contract_and_export(tmp_path: Path) -> None:
    game = _game(
        slug="all-lucky-clover",
        name="All Lucky Clovers",
        symbol="AllLuckyClover",
    )
    provider = BGamingProvider(tmp_path)
    _write_metadata(provider.game_dir(game), game, SWITCHABLE)
    variants = ["AllLuckyClover5", "AllLuckyClover20", "AllLuckyClover40"]
    result = GameTestResult(
        provider="bgaming",
        slug=game.slug,
        game_name=game.name,
        game_url=game.url,
        requested_spins=len(variants),
        successful_spins=len(variants),
        failed_spins=0,
        status="OK",
        symbol=game.symbol,
        discovered_modes=[
            {
                "id": f"VARIANT_{identifier.upper()}",
                "kind": "VARIANT",
                "wire_command": "lobby_switch+init+spin",
                "identifier": identifier,
                "observed": True,
                "validated": True,
                "evidence_level": "REMOTE_EXECUTION",
                "execution_state": "PROVEN_TERMINAL",
            }
            for identifier in variants
        ],
    )

    contract = provider.build_farm_contract(game, result)

    assert contract["ready"] is True, contract["unresolved"]
    wager_ids = {item["mode_id"] for item in contract["execution_structure"]["wagers"]}
    assert wager_ids == {f"VARIANT_{identifier.upper()}" for identifier in variants}
    for wager in contract["execution_structure"]["wagers"]:
        assert wager["kind"] == "VARIANT"
        assert wager["parameters"]["identifier"] in variants
