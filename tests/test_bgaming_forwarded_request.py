from tester_spin.providers.bgaming.hyperhive_wire import _has_req_bet_evidence, _req_literal_values
from tester_spin.providers.bgaming.hyperhive_contract_probe import _has_req_bet_type_evidence


CLIENT = '''const rpc=async(method,params)=>{return await http.post("/api",{id:crypto.randomUUID(),jsonrpc:"2.0",method:method,params:params})};
send=async arg=>{const result=await(async arg=>{const token=currentToken();return await rpc("play",{token:token,req:{...arg}})})(arg);return result};
send({bet:state.bet,bet_type:freebet?"freebet":"bet"});
send({bet:state.bet,purchased_feature:"buy_bonus",bonus_multiplier_type:"freeSpin"});
const unrelated={purchased_feature:"high_freespin_buy"};'''


def test_exact_forwarding_proves_only_called_request_fields():
    assert _has_req_bet_evidence(CLIENT)
    assert _has_req_bet_type_evidence(CLIENT)
    assert _req_literal_values(CLIENT, "purchased_feature") == {"buy_bonus"}
    assert _req_literal_values(CLIENT, "bonus_multiplier_type") == {"freespin"}


def test_optional_feature_is_proven_only_through_forwarded_call():
    source = CLIENT + 'send({bet:state.bet,purchased_feature:!free&&state.boost?"buy_chance":void 0});'
    assert _req_literal_values(source, "purchased_feature") == {"buy_bonus", "buy_chance"}
    assert _req_literal_values(source.replace('req:{...arg}', 'req:{...other}'), "purchased_feature") == set()


def test_discovery_uses_forwarded_purchase_variants_not_generic_init_vocabulary():
    import requests
    from unittest.mock import patch
    from tester_spin.providers.bgaming import hyperhive
    from tester_spin.providers.bgaming.runtime import BGamingRuntime
    source = CLIENT + 'send({bet:state.bet,purchased_feature:!free&&state.boost?"buy_chance":void 0});'
    source += 'send({bet:state.bet,purchased_feature:"buy_bonus",bonus_multiplier_type:"freeSpinRandom"});'
    runtime = BGamingRuntime(session=requests.Session(),launch_url='https://fixture.demo.bgaming-network.com/hyperhive',
        api_url='https://fixture.demo.bgaming-network.com/api', identifier='fixture',
        csrf_header_name='',csrf_header_value='',options={},round_series_id=1)
    try:
        with patch.object(hyperhive, '_download_bundle', return_value=source):
            modes=hyperhive.discover_modes_from_bundle(runtime,timeout_s=1,bundle_text=source,engine_contract=source)
    finally:
        runtime.session.close()
    executable={m['id'] for m in modes if m.get('executable')}
    assert executable=={'SPIN','PURCHASE_BUY_CHANCE','PURCHASE_BUY_BONUS_FREESPIN','PURCHASE_BUY_BONUS_RANDOM'}


def test_broken_transport_or_changed_spread_does_not_prove_request():
    for source in (CLIENT.replace('jsonrpc:"2.0"', 'protocol:"other"'),
                   CLIENT.replace('req:{...arg}', 'req:{...other}'),
                   CLIENT.replace('req:{...arg}', 'req:{...arg,bet:0}'),
                   CLIENT.replace('rpc("play"', 'rpc("info"')):
        if 'req:{...arg,bet:0}' not in source:
            assert not _has_req_bet_evidence(source)
        assert not _req_literal_values(source, "purchased_feature")


def test_comments_strings_rebinding_and_unreachable_transport_do_not_prove_calls():
    call='send({bet:state.bet,purchased_feature:"buy_bonus",bonus_multiplier_type:"freeSpin"});'
    for source in (CLIENT.replace(call, '/*'+call+'*/'),
                   CLIENT.replace(call, json_string(call)),
                   CLIENT.replace(call, 'send=async arg=>rpc("info",arg);'+call),
                   CLIENT.replace('return await http.post', 'if(false)return await http.post')):
        assert not _req_literal_values(source, 'purchased_feature')
    assert _req_literal_values('const pattern=/["\']/;'+CLIENT,'purchased_feature')=={'buy_bonus'}
    assert _req_literal_values(CLIENT+'unrelated.send({purchased_feature:"invented"});','purchased_feature')=={'buy_bonus'}
    assert not _req_literal_values(CLIENT+'function other(send){send({purchased_feature:"invented"});}','purchased_feature')


def json_string(value):
    import json
    return 'const documentation='+json.dumps(value)+';'
