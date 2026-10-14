import json
from pathlib import Path
import pytest
from decimal import Decimal
from tester_spin.providers.nolimit_city.protocol import rc4_hex,lzw_decode,decode_capture,analyze_messages

def test_rc4_matches_independent_known_vector():
    assert rc4_hex('Key','bbf316e8d940af0ad3')=='Plaintext'

def test_lzw_uses_client_utf16_dictionary_codes():
    codes=[84,79,66,69,79,82,78,79,84,256,258,260,265,259,261,263]
    assert lzw_decode('lzw:'+''.join(chr(c) for c in codes))=='TOBEORNOTTOBEORTOBEORNOT'
    assert lzw_decode('{"plain":true}')=='{"plain":true}'

@pytest.mark.parametrize('value',['lzw:','lzw:A'+chr(9999)])
def test_invalid_lzw_never_invents_output(value):
    with pytest.raises(ValueError):lzw_decode(value)

def test_expansion_is_bounded():
    with pytest.raises(ValueError):lzw_decode('lzw:ABC',max_output=2)

def test_real_capture_quotes_roots_and_continuations_agree():
    messages=json.loads(Path('tests/fixtures/nolimit_airport_protocol.json').read_text())
    report=analyze_messages(messages)
    assert report['request_count']==51 and report['paid_rounds']==14 and report['zero_bet_continuations']==36
    assert len(report['domains']['purchase']['options'])==4
    assert len(report['domains']['boosted_bet']['options'])==3
    assert Decimal(report['total_paid'])==Decimal('10273.80') and Decimal(report['total_win'])==Decimal('2756.05')
    assert report['final_balance']=='2482.25' and report['closed_rounds']==14
    assert report['consecutive_normal_at_end']==1
    assert not report['ok_certified']

def test_wrong_price_or_response_id_is_rejected():
    messages=json.loads(Path('tests/fixtures/nolimit_airport_protocol.json').read_text())
    messages[1]['message']['game']['featureBuyTimesBetValue'][0]['price']=79
    with pytest.raises(ValueError):analyze_messages(messages)
    messages=json.loads(Path('tests/fixtures/nolimit_airport_protocol.json').read_text())
    messages[3]['message']['id']='wrong'
    with pytest.raises(ValueError):analyze_messages(messages)

def test_capture_without_ws_or_bootstrap_key_remains_unknown():
    for doc in [{'log':{'entries':[]}},{'log':{'entries':[],'_warpWebSockets':[{'direction':'sent','payload':'deadbeef','url':'wss://demo.nolimitcity.com/EjsGameWeb/ws/game'}]}}]:
        with pytest.raises(ValueError):decode_capture(doc)


def test_http_bootstrap_is_bound_to_derived_websocket_url():
    from tester_spin.providers.nolimit_city.protocol import websocket_url
    url=websocket_url('https://demo.nolimitcity.com/EjsGameWeb/gs','fixture-key')
    assert url=='wss://demo.nolimitcity.com/EjsGameWeb/ws/game?data=fixture-key'
    doc={'log':{'entries':[{'request':{'method':'POST','url':'https://demo.nolimitcity.com/EjsFrontWeb/fs'},
        'response':{'content':{'text':json.dumps({'key':'fixture-key','url':'https://demo.nolimitcity.com/EjsGameWeb/gs'})}}}],
        '_warpWebSockets':[{'url':url,'direction':'received','payload':'{"id":"fixture","init":"ok"}','encoding':'utf8'}]}}
    assert decode_capture(doc)[0]['message']['init']=='ok'
