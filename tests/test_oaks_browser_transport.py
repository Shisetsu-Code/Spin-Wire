from pathlib import Path
import json
import pytest
from tester_spin.providers.three_oaks.runtime import DemoSession

class Response:
    def __init__(self,status,text):self.status_code=status;self.text=text
    def raise_for_status(self):
        if self.status_code>=400:raise ValueError(str(self.status_code))
    def json(self):return json.loads(self.text)
class HTTP:
    def __init__(self,response):self.response=response;self.calls=0
    def post(self,*args,**kwargs):self.calls+=1;return self.response
class Browser:
    def __init__(self):self.calls=0
    def post(self,*args,**kwargs):
        self.calls+=1;return Response(200,'{"status":{"code":"OK"},"session_id":"fixture"}')

def test_browser_used_after_cloudflare_login_challenge_and_for_following_commands(tmp_path):
    http=HTTP(Response(429,'<html><title>Just a moment...</title>challenge-platform</html>'));browser=Browser()
    session=DemoSession(http,'https://betman-demo.head.3oaks.com/demo/',tmp_path,2,browser_fallback=browser)
    session.post('login',{'token':'fixture'})
    session.post('start',{'mode':'auto'})
    assert http.calls==1 and browser.calls==2
    assert session.session_id=='fixture'
    assert (tmp_path/'000-login.response.http-blocked.raw.html').exists()

def test_regular_rate_limit_is_not_treated_as_browser_challenge(tmp_path):
    http=HTTP(Response(429,'{"error":"rate limit"}'));browser=Browser()
    session=DemoSession(http,'https://betman-demo.head.3oaks.com/demo/',tmp_path,2,browser_fallback=browser)
    with pytest.raises(ValueError):session.post('login',{})
    assert browser.calls==0

def test_purchase_is_never_retried_after_a_blocked_response(tmp_path):
    http=HTTP(Response(429,'<html><title>Just a moment...</title>challenge-platform</html>'));browser=Browser()
    session=DemoSession(http,'https://betman-demo.head.3oaks.com/demo/',tmp_path,2,browser_fallback=browser)
    with pytest.raises(ValueError):session.post('play',{'action':{'name':'buy_spin'}})
    assert browser.calls==0 and http.calls==1

def test_browser_initializes_on_demo_origin_not_catalog_page(monkeypatch):
    from tester_spin.providers.three_oaks.browser_transport import BrowserDemoTransport
    calls=[]
    class Page:
        def evaluate(self,*args,**kwargs):return {'status':200,'text':'{"status":{"code":"OK"}}'}
    transport=BrowserDemoTransport('https://3oaks.com/game/unseen')
    def opened(url):calls.append(url);transport.page=Page()
    monkeypatch.setattr(transport,'_open',opened)
    transport.post('https://betman-demo.head.3oaks.com/gs/unseen/desktop/fresh/demo/',params={'gsc':'login'},data='{}',timeout=2,headers={})
    assert calls==['https://betman-demo.head.3oaks.com/gs/unseen/desktop/fresh/demo/']
