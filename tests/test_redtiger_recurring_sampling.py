import json
from tester_spin.models import GameTestResult, SpinAttempt
from tester_spin.sample_catalog import build_sample_catalog


def make_run(root):
    result=GameTestResult(provider='redtiger',slug='synthetic',game_name='Synthetic',game_url='https://example.invalid',
        requested_spins=3,successful_spins=3,failed_spins=0,status='OK',run_dir=str(root))
    result.discovered_modes=[{'id':'SPIN','kind':'SPIN'},
        {'id':'RECURRING','kind':'DIAGNOSTIC','parent':'SPIN','observed':True,'coverage_required':False,
         'source':'choice_transition.gameData.progress.level','entry_prefix':[],
         'coverage_scope':'available_actions_not_all_repeat_counts','options':['continue','collect'],'repeat_actions':['continue']}]
    for i,actions in enumerate([['continue'],['collect'],['continue','continue','collect']],1):
        d=root/'SPIN'/f'attempt-{i}';d.mkdir(parents=True)
        records=[{'selected':a,'available':['continue','collect']} for a in actions]
        (d/'summary.json').write_text(json.dumps({'choice_continuations':records,'branch_prefix':actions[:1]}))
        (d/'response.json').write_text(json.dumps({'success':True,'result':{'game':{'spinMode':'Normal'}}}))
        (d/'return-to-base.json').write_text(json.dumps({'status':'CONFIRMED','consecutive_base':2}))
        result.attempts.append(SpinAttempt(number=i,ok=True,terminal=True,
            mode_id='SPIN' if i==1 else 'SPIN__CHOICE_'+actions[0].upper(),
            mode_kind='SPIN' if i==1 else 'CHOICE_PATH',artifact_dir=str(d)))
    return result


def test_recurring_controls_sample_across_entry_paths_once_per_independent_round(tmp_path):
    result=make_run(tmp_path)
    report=build_sample_catalog(result,samples_per_path=2)
    groups={tuple(c['value'] for c in g['choices']):g for g in report['groups']}
    assert groups[()]['validated_samples']==3
    assert groups[('continue',)]['validated_samples']==2
    assert groups[('collect',)]['validated_samples']==2
    assert report['observed_paths_sampled']


def test_unknown_scope_or_missing_base_proof_never_combines_routes(tmp_path):
    result=make_run(tmp_path)
    result.discovered_modes[-1]['source']='unknown'
    assert not build_sample_catalog(result,samples_per_path=2)['observed_paths_sampled']
    result.discovered_modes[-1]['source']='choice_transition.gameData.progress.level'
    (tmp_path/'SPIN/attempt-3/return-to-base.json').write_text('{}')
    assert not build_sample_catalog(result,samples_per_path=2)['observed_paths_sampled']
