import json
from pathlib import Path
from tester_spin.models import GameTestResult, SpinAttempt
from tester_spin.providers.path_coverage import build_path_coverage_report


def run(root):
    result=GameTestResult(provider='pragmatic',slug='synthetic',game_name='Synthetic',game_url='https://example.invalid',
        requested_spins=2,successful_spins=2,failed_spins=0,status='OK',symbol='synthetic',run_dir=str(root),
        feature_domains={'purchase':{'complete':True,'source':'doInit.purInit/purInit_e','options':['PURCHASE_1']},
                         'ante':{'complete':True,'source':'doInit.bls','options':['ANTE_BET_1']}})
    for mode,kind,bl,pur in [('PURCHASE_1','PURCHASE',0,0),('ANTE_BET_1','ANTE_BET',1,None)]:
        result.discovered_modes.append({'id':mode,'kind':kind,'provider_bl':bl,'provider_pur':pur,
            'enabled':True,'price_known':True,'paid_cost':10})
        d=root/mode/'attempt-1';d.mkdir(parents=True)
        (d/'step-000-entry.request.txt').write_text('action=doSpin&symbol=synthetic&bl='+str(bl)+('' if pur is None else '&pur='+str(pur)))
        (d/'step-000-entry.response.json').write_text(json.dumps({'na':'s','bl':str(bl),
            **({'purtr':'1','puri':str(pur)} if pur is not None else {})}))
        (d/'step-000-entry.http.json').write_text(json.dumps({'status':200}))
        (d/'return-to-base.json').write_text(json.dumps({'status':'CONFIRMED','consecutive_base':2}))
        result.attempts.append(SpinAttempt(number=len(result.attempts)+1,ok=True,terminal=True,
            mode_id=mode,mode_kind=kind,artifact_dir=str(d)))
    return result


def declared_points(result):
    report=build_path_coverage_report(result)
    return [p for p in report['branch_points'] if p['mode_id'].endswith('_DECLARATION')]


def test_current_validated_mode_wire_proves_declared_purchase_and_ante(tmp_path):
    points=declared_points(run(tmp_path))
    assert all(not p['missing'] for p in points)


def test_wrong_selector_missing_base_or_sample_deficit_remain_pending(tmp_path):
    for i,change in enumerate(['selector','base','warning','samples','duplicate','ignored','symbol','metadata']):
        result=run(tmp_path/str(i));d=Path(result.attempts[0].artifact_dir)
        if change=='selector':(d/'step-000-entry.request.txt').write_text('action=doSpin&symbol=synthetic&bl=0&pur=1')
        if change=='base':(d/'return-to-base.json').write_text('{}')
        if change=='warning':result.attempts[0].warning='price mismatch'
        if change in {'samples','duplicate'}:result.samples_per_path=2
        if change=='duplicate':result.attempts.append(result.attempts[0])
        if change in {'ignored','metadata'}:(d/'step-000-entry.response.json').write_text(json.dumps({'na':'s','bl':'0'}))
        if change=='symbol':result.symbol=''
        if change=='metadata':result.discovered_modes[0].update(validated=True,covered_options=['PURCHASE_1'])
        assert next(p for p in declared_points(result) if p['mode_id']=='PURCHASE_DECLARATION')['missing']
