#!/usr/bin/env python3
"""Capture demo game HTTP requests from a real Chromium session, never infer a HAR from API emulation.
Only sanitized evidence is published. This diagnostic does not make purchases automatically.
"""
import json
import os
import re
import sys
import traceback
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from playwright.sync_api import sync_playwright

GAMES = ["777_fruity_coins", "lady_fortune"]
OUT = Path("action-3oaks-browser-har")
TEMP = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "three-oaks-browser-raw"
OUT.mkdir(exist_ok=True, parents=True)
TEMP.mkdir(exist_ok=True, parents=True)
SENSITIVE = ("token","secret","session","cookie","auth","password","huid","userid","playerid","user_id","request_id","requestid","sid","gamekey","credentials","signature")

def redact(value, key=""):
    lower=re.sub(r"[^a-z0-9]", "", str(key).lower())
    if any(t in lower for t in SENSITIVE):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k):redact(v,str(k)) for k,v in value.items()}
    if isinstance(value,list):
        return [redact(v,key) for v in value[:250]]
    if isinstance(value,str):
        value=re.sub(r"(?i)((?:token|session(?:_id)?|huid|sid|auth|signature)=)[^\s&]+",r"\1[REDACTED]",value)
        return value[:10000]
    return value

def safe_url(url):
    u=urlsplit(url)
    path=re.sub(r"/(?:[a-f0-9]{24,}|[A-Za-z0-9_-]{70,})(?=/|$)","/[opaque]",u.path)
    # Exclude all query fields; demo launchers can embed credentials in URL query.
    return urlunsplit((u.scheme,u.netloc,path,"",""))

def maybe_json(data):
    if not data: return None
    try:return redact(json.loads(data))
    except (ValueError, TypeError):return "[NON_JSON_BODY_OMITTED]"

def redact_har(source,dest):
    if not source.exists():
        dest.write_text(json.dumps({"log":{"version":"1.2","entries":[]}},indent=2))
        return {"entries":0,"play_requests":0,"post_requests":0}
    har=json.loads(source.read_text(encoding="utf-8"))
    entries=[]
    action_requests=[]
    for e in har.get("log",{}).get("entries",[]):
        req=e.get("request",{})
        resp=e.get("response",{})
        method=req.get("method","")
        url=safe_url(req.get("url",""))
        post=req.get("postData",{})
        payload=maybe_json(post.get("text"))
        safe_req={"method":method,"url":url,"httpVersion":req.get("httpVersion"),
                  "headers":[{"name":"Content-Type","value":str(x.get("value",""))} for x in req.get("headers",[]) if str(x.get("name","")).lower()=="content-type"],
                  "queryString":[],"cookies":[],"headersSize":-1,"bodySize":-1}
        if method in ("POST","PUT","PATCH") and post:
            safe_req["postData"]={"mimeType":post.get("mimeType",""),"text":json.dumps(payload,ensure_ascii=False)}
        safe_resp={"status":resp.get("status"),"statusText":resp.get("statusText",""),"httpVersion":resp.get("httpVersion",""),
                   "headers":[],"cookies":[],"content":{"size":resp.get("content",{}).get("size",0),"mimeType":resp.get("content",{}).get("mimeType","")},
                   "redirectURL":"","headersSize":-1,"bodySize":-1}
        if method=="POST":
            action=payload.get("action",{}) if isinstance(payload,dict) else {}
            action_requests.append({"url":url,"http_status":safe_resp["status"],"command":payload.get("command") if isinstance(payload,dict) else None,
                                    "action":action,"payload":payload})
        entries.append({"startedDateTime":e.get("startedDateTime"),"time":e.get("time",0),
                        "request":safe_req,"response":safe_resp,"cache":{},"timings":e.get("timings",{})})
    dest.write_text(json.dumps({"log":{"version":"1.2","creator":{"name":"Spin-Wire 3 Oaks sanitized browser diagnostic","version":"1"},"entries":entries}},ensure_ascii=False,indent=2),encoding="utf-8")
    return {"entries":len(entries),"post_requests":len(action_requests),
            "play_requests":sum(x.get("command")=="play" or (x.get("action") or {}).get("name") in ("spin","buy_spin") for x in action_requests),
            "actions":action_requests[:100]}

def snapshot_dom(page):
    code="""() => ({title:document.title, href:location.origin+location.pathname, readyState:document.readyState,
      text:(document.body?.innerText||'').slice(0,2200),
      canvases:Array.from(document.querySelectorAll('canvas')).map(x=>({width:x.width,height:x.height,rect:{w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height}})).slice(0,20),
      interactive:Array.from(document.querySelectorAll('button,a,[role=button],input')).filter(x=>{let r=x.getBoundingClientRect();return r.width&&r.height}).slice(0,45).map(x=>({tag:x.tagName,text:(x.innerText||x.value||x.title||x.getAttribute('aria-label')||'').slice(0,160),href:x.tagName==='A'?(x.href?.split('?')[0]||''):null})),
      frames:Array.from(document.querySelectorAll('iframe')).map(f=>({src:f.src?.split('?')[0],rect:{w:f.getBoundingClientRect().width,h:f.getBoundingClientRect().height}})).slice(0,12)})"""
    try:return redact(page.evaluate(code))
    except Exception as exc:return {"dom_error":type(exc).__name__+":"+str(exc)[:200]}

all_results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--use-gl=swiftshader"])
    for slug in GAMES:
        raw=TEMP/(slug+".har")
        out=OUT/slug
        out.mkdir(exist_ok=True)
        context=browser.new_context(viewport={"width":1280,"height":720}, device_scale_factor=1,
                                      record_har_path=str(raw),record_har_content="omit")
        page=context.new_page()
        browser_posts=[]
        request_failures=[]
        def observe_request(request):
            if request.method != "POST" or "betman-demo.head.3oaks.com" not in request.url:
                return
            body=maybe_json(request.post_data)
            browser_posts.append({"url":safe_url(request.url),"post":body})
        def observe_failure(request):
            if "betman-demo.head.3oaks.com" in request.url:
                request_failures.append({"url":safe_url(request.url),"method":request.method,
                                         "failure":str(request.failure or "unknown")[:200]})
        page.on("request",observe_request)
        page.on("requestfailed",observe_failure)
        # Chromium DevTools identifies CORS blocks separately from network timeouts.
        cdp_urls={}
        cdp_failures=[]
        cdp=context.new_cdp_session(page)
        cdp.send("Network.enable")
        def cdp_request(event):
            request=event.get("request",{})
            cdp_urls[event.get("requestId")]=(request.get("method"),safe_url(request.get("url","")))
        def cdp_failed(event):
            method,url=cdp_urls.get(event.get("requestId"),(None,None))
            if url and "betman-demo.head.3oaks.com" in url:
                cdp_failures.append({"method":method,"url":url,
                    "error":event.get("errorText"),
                    "blocked":event.get("blockedReason"),
                    "cors":event.get("corsErrorStatus")})
        cdp.on("Network.requestWillBeSent",cdp_request)
        cdp.on("Network.loadingFailed",cdp_failed)
        failure=None
        loaded=[]
        for target in [f"https://3oaks.com/api/v1/games/{slug}/play?lang=en",f"https://3oaks.com/game/{slug}"]:
            try:
                response=page.goto(target,wait_until="domcontentloaded",timeout=25000)
                loaded.append({"url":safe_url(page.url),"status":response.status if response else None})
                page.wait_for_timeout(9000)
                if response and response.status<400:break
            except Exception as exc:
                failure=type(exc).__name__+": "+str(exc)[:300]
                loaded.append({"url":safe_url(target),"error":failure})
        frame_details=[]
        for frame in page.frames[:8]:
            try:
                frame_details.append({"url":safe_url(frame.url),
                                      "body":redact(frame.locator("body").inner_text(timeout=500)[:200])})
            except Exception:pass
        dom=snapshot_dom(page)
        try:page.screenshot(path=str(out/"initial.jpg"),type="jpeg",quality=68,timeout=6000)
        except Exception as exc:dom["screenshot_error"]=str(exc)[:200]
        context.close()
        info=redact_har(raw,out/"capture.sanitized.har")
        if raw.exists():raw.unlink()
        summary={"slug":slug,"loaded":loaded,"failure":failure,"dom":dom,"frames":frame_details,
                 "har":{k:v for k,v in info.items() if k!="actions"},"actions":info["actions"],
                 "browser_posts":browser_posts[:100],
                 "request_failures":request_failures[:100],
                 "chromium_network_failures":cdp_failures[:100]}
        (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2))
        all_results.append({"slug":slug,"loaded":loaded,"har":summary["har"],
                            "frame_count":len(frame_details),"canvases":len(dom.get("canvases",[])),
                            "browser_posts":len(browser_posts),"network_failures":request_failures[:10],
                            "chromium_network_failures":cdp_failures[:10],"error":failure})
        print(json.dumps(all_results[-1],ensure_ascii=False),flush=True)
    browser.close()
(OUT/"summary.json").write_text(json.dumps(all_results,ensure_ascii=False,indent=2),encoding="utf-8")
