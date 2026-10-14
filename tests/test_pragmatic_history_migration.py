import copy
import json
from pathlib import Path

from tester_spin.models import GameTestResult, SpinAttempt
from tester_spin.coverage_history import retain_pending_branches
from tester_spin.providers.pragmatic_bonus_coverage import annotate_bonus_coverage
from tester_spin.providers.pragmatic_observed_transitions import bonus_transition, bonus_choice


def make_result(root):
    return GameTestResult(provider='pragmatic',slug='test',game_name='Test',game_url='https://example.invalid',
        requested_spins=1,successful_spins=1,failed_spins=0,status='OK',run_dir=str(root))


def setup_history(root, family):
    fixtures=Path(__file__).parent/'fixtures'
    if family=='gamble':
        rows=json.loads((fixtures/'pragmatic_parameterized_gamble.json').read_text())
        chosen=[next(r for r in rows if r['selected']==v) for v in ['0','1','2']]
        old_signature='PRAGMATIC:bonus-choice:bgt=69:choices=0,1,2:family=gambling:labels=play,sm5s7-6,sp7s5-6'
        required=['0','1','2']
    elif family=='repeatable':
        games=json.loads((fixtures/'pragmatic_oct09_seven.json').read_text())
        rows=next(g for g in games if g['symbol']=='vswayswildb')['choices']
        chosen=[{**next(r for r in rows if r['ind']==v),'selected':v} for v in ['0','1']]
        old_signature='PRAGMATIC:bonus-choice:bgt=69:family=bg:ask=10:labels=y,n'
        required=['0','1']
    else:
        games=json.loads((fixtures/'pragmatic_oct09_seven.json').read_text())
        rows=next(g for g in games if g['symbol']=='vs20bblup')['choices']
        chosen=[{**rows[0],'selected':rows[0]['ind']}]
        required=bonus_transition(chosen[0]['before'])['domain']
    legacy_selection=(bonus_transition(chosen[0]['before'],override=chosen[0]['selected']) if family=='range'
                      else bonus_choice(chosen[0]['before'],override=chosen[0]['selected']))
    old_signature=legacy_selection['branch_signature']
    old_root=root/'tests'/'old';old_root.mkdir(parents=True)
    artifact=old_root/'PURCHASE_1'/'attempt-1';artifact.mkdir(parents=True)
    old=make_result(old_root)
    old.attempts=[SpinAttempt(number=1,ok=True,terminal=True,mode_id='PURCHASE_1',artifact_dir=str(artifact))]
    prior={'id':'OLD','kind':'CHOICE_BRANCH','observed':True,'coverage_required':True,
        'coverage_origin':'pragmatic_bonus_selection_artifacts','origin_mode_id':'PURCHASE_1',
        'coverage_policy':'ordinal-options/v1','contract_branch_signature':old_signature,
        'contract_sha256':'a'*64,'required_options':required,'covered_options':[],'required_samples':1}
    old.discovered_modes=[prior]
    (old_root/'result.json').write_text(json.dumps(old.to_dict()))
    (artifact/'step-000-spin.response.json').write_text(json.dumps(chosen[0]['before']))
    legacy={'branch_signature':old_signature,'contract_sha256':'a'*64,'selected':chosen[0]['selected'],
            'domain':legacy_selection['domain']}
    legacy_path=artifact/'step-001-bonus.bonus-selection.json';legacy_path.write_text(json.dumps(legacy))
    retain_pending_branches(root,old)
    fresh_root=root/'tests'/'new';fresh_root.mkdir()
    fresh=make_result(fresh_root)
    for i,item in enumerate(chosen,1):
        folder=fresh_root/'PURCHASE_1'/f'attempt-{i}';folder.mkdir(parents=True)
        fresh.attempts.append(SpinAttempt(number=i,ok=True,terminal=True,mode_id='PURCHASE_1',artifact_dir=str(folder)))
        record=bonus_transition(item['before'],override=item['selected'])
        (folder/'step-001-bonus.bonus-selection.json').write_text(json.dumps(record))
        (folder/'step-001-bonus.response.json').write_text(json.dumps(item['after']))
        (folder/'return-to-base.json').write_text(json.dumps({'status':'CONFIRMED','consecutive_base':2}))
    annotate_bonus_coverage(fresh)
    return fresh,legacy_path


def test_normalized_migrations_archive_raw_evidence_and_are_idempotent(tmp_path):
    for family in ['gamble','repeatable','range']:
        root=tmp_path/family
        fresh,legacy=setup_history(root,family)
        before=legacy.read_text()
        retain_pending_branches(root,fresh)
        saved=json.loads((root/'coverage-history.json').read_text())
        assert not saved['pending']
        assert saved['policy_migrations'][0]['previous_id']=='OLD'
        assert legacy.read_text()==before
        retain_pending_branches(root,fresh)
        assert len(json.loads((root/'coverage-history.json').read_text())['policy_migrations'])==1


def test_missing_raw_origin_samples_ack_or_base_proof_keeps_history(tmp_path):
    for index,change in enumerate(['raw','origin','samples','ack','base','mismatched_raw','historical_samples']):
        root=tmp_path/str(index);fresh,legacy=setup_history(root,'gamble')
        if change=='raw':legacy.with_name('step-000-spin.response.json').unlink()
        if change=='origin':
            for a in fresh.attempts:a.mode_id='SPIN'
        if change=='samples':fresh.samples_per_path=2
        if change=='ack':
            p=Path(fresh.attempts[-1].artifact_dir)/'step-001-bonus.response.json';p.write_text('{}')
        if change=='base':
            p=Path(fresh.attempts[-1].artifact_dir)/'return-to-base.json';p.write_text('{}')
        if change=='mismatched_raw':
            p=legacy.with_name('step-000-spin.response.json')
            p.write_text(p.read_text().replace('sm5s7-6','sm5s7-2'))
        if change=='historical_samples':
            p=root/'coverage-history.json';saved=json.loads(p.read_text())
            saved['pending']['OLD']['required_samples']=2;p.write_text(json.dumps(saved))
        annotate_bonus_coverage(fresh)
        retain_pending_branches(root,fresh)
        assert 'OLD' in json.loads((root/'coverage-history.json').read_text())['pending']
