# KA Gaming integration design

## Goal

Add KA Gaming as an isolated Tester-Spin provider: import its verified public catalogue and collect runtime evidence without treating an unproven game action as successful.

## Scope

The catalogue request is `GET https://rmpdemo.kaga88.com/kaga/publicGameList?lang=<language>` and is authoritative only when its status, count, unique IDs and launch URL validate. The adapter will use a browser-like HTTP fingerprint, preserve only non-secret game metadata and generate the current demo URL from the advertised launch base and required parameters.

Each game test begins with a fresh demo session. The adapter records sanitized launch/bootstrap evidence and browser-observed network activity. It may classify a terminal spin only after a provider-local request/response contract is observed and implemented. Until then, runtime results remain `PARCIAL`; it must not guess betting, buy-feature or continuation payloads.

## Boundaries

`tester_spin/providers/ka_gaming/catalog.py` owns catalogue retrieval, validation and neutral `Game` construction. `adapter.py` owns the `ProviderAdapter` surface, persistence and the conservative runtime handoff. Runtime discovery is provider-local. Existing provider modules, scheduler semantics and storage schema remain unchanged.

## Verification

Fixture tests cover a valid payload, mismatch in `numGames`, duplicate/missing IDs, invalid launch bases and deterministic launch URL fields. Integration tests ensure a non-proven runtime result is `PARCIAL`, preserving evidence rather than reporting `OK`. A live catalogue smoke check is run only after tests pass.
