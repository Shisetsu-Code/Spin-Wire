import json
from types import SimpleNamespace

def test_har_preserves_unknown_response_fields_and_form_request(tmp_path):
    from tester_spin.http_har import HTTPHar
    path=tmp_path/'analysis'/'http.har';capture=HTTPHar(path)
    response=SimpleNamespace(status_code=200,text='{"code":0,"data":{"actions":[{"newAction":{"choice":3}}]}}',headers={'Content-Type':'application/json'})
    capture.append('https://demo.example/service',{'fn':'play'}, {'cmd':'BASE_SPIN','amount':'0.1'}, {},response,0.2)
    entry=json.loads(path.read_text())['log']['entries'][0]
    assert entry['request']['url']=='https://demo.example/service?fn=play'
    assert entry['request']['postData']['text']=='cmd=BASE_SPIN&amount=0.1'
    assert json.loads(entry['response']['content']['text'])['data']['actions'][0]['newAction']['choice']==3
    assert entry['response']['status']==200

def test_har_records_rejections_before_protocol_validation(tmp_path):
    from tester_spin.http_har import HTTPHar
    path=tmp_path/'http.har';capture=HTTPHar(path)
    response=SimpleNamespace(status_code=429,text='slow down',headers={'Retry-After':'60'})
    capture.append('https://demo.example/service',{'fn':'authenticate'}, {},{},response,0.1)
    entry=json.loads(path.read_text())['log']['entries'][0]
    assert entry['response']['status']==429
    assert entry['response']['content']['text']=='slow down'


def test_json_request_is_recorded_without_changing_signed_bytes(tmp_path):
    from tester_spin.http_har import HTTPHar
    raw='{"amount":0.1,"cmd":"SPIN"}'
    path=tmp_path/'http.har'
    HTTPHar(path).append('https://demo.example/service',{},raw,{'Content-Type':'application/json'},SimpleNamespace(status_code=200,text='{}',headers={}),.1)
    post=json.loads(path.read_text())['log']['entries'][0]['request']['postData']
    assert post['text']==raw and post['mimeType']=='application/json'
    assert 'params' not in post
