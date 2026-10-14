import json
from pathlib import Path
import pytest

FIXTURE=json.loads(Path('tests/fixtures/ka_oct11_declarations.json').read_text(encoding='utf-8'))


def test_named_immediately_registered_descriptor_inherits_explicit_zero_domains():
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    client='var Description=xd.extend({ctor:function(a){"undefined"===typeof a?(this._super(null),A.Bb().Gg("Synthetic",this)):this._super(a)},Ya:function(){return ce.create(this.Cc(),this.la)}});new Description;'
    result=client_declarations(FIXTURE['common'],client,'Synthetic',{})
    assert result['domains']['purchase']['complete']
    assert result['domains']['purchase']['options']==[]
    assert result['domains']['ante']['complete']
    for bad in [client.replace('new Description;', 'new Other;'),
                client.replace(');new Description;',');Description=Other;new Description;'),
                'function build(){'+client+'}',
                'if(false){'+client+'}',
                client.replace('ctor:function(a){"undefined"===typeof a?(this._super(null),A.Bb().Gg("Synthetic",this)):this._super(a)}',
                    'ctor:function(){if(false){A.Bb().Gg("Synthetic",this)}}'),
                client.replace('Gg("Synthetic"','Gg("Other"')]:
        assert not client_declarations(FIXTURE['common'],bad,'Synthetic',{})['domains']['purchase']['complete']

@pytest.mark.parametrize('row', FIXTURE['games'], ids=lambda r:r['symbol'])
def test_options_come_from_game_descriptor_not_observed_requests(row):
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    declaration=client_declarations(FIXTURE['common'],row['client'],row['symbol'],row['initial'])
    expected=[] if row['symbol']=='BonusVending' else ['pos:1']
    assert declaration['domains']['purchase']['options']==expected
    assert declaration['domains']['purchase']['complete']
    assert declaration['domains']['ante']['options']==[]
    assert len(declaration['modes'])==len(expected)


def test_other_game_and_unknown_flags_do_not_prove_absence():
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    row=FIXTURE['games'][0]
    for name,initial in [('OtherGame',row['initial']),(row['symbol'],{})]:
        assert client_declarations(FIXTURE['common'],row['client'],name,initial)['domains']['purchase']['complete'] is False


def test_server_disable_is_respected():
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    row=FIXTURE['games'][0]
    assert client_declarations(FIXTURE['common'],row['client'],row['symbol'],{'dbf':True})['domains']['purchase']['options']==[]


def test_unknown_cost_is_pending_instead_of_guessed():
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    row=FIXTURE['games'][0]
    declaration=client_declarations(FIXTURE['common'],row['client'].replace('80*this.Tc','dynamic*this.Tc'),row['symbol'],row['initial'])
    assert declaration['domains']['purchase']['complete'] is False


@pytest.mark.parametrize('row', FIXTURE['games'], ids=lambda r:r['symbol'])
def test_declared_purchase_replays_complete_capture_without_rebuying(tmp_path,row):
    import threading
    from unittest.mock import MagicMock
    from tester_spin.models import Game
    from tester_spin.providers.ka_gaming.runtime import run_rmp_game
    from tester_spin.providers.path_coverage import enforce_complete_path_coverage
    states=iter(row['responses']);calls=[];active=[False]
    initial=row['initial_state']
    rest=next((s for s in reversed(row['responses']) if not s.get('fs') and s.get('acb')==0),initial)
    def post(url,**kwargs):
        context=json.loads(kwargs['headers']['ctx'])
        assert context['do']=='Windows'
        assert context['dt']=='Chrome'
        assert 'Windows NT' in kwargs['headers'].get('User-Agent','')
        assert 'Chrome/'+context['dv'] in kwargs['headers']['User-Agent']
        body=json.loads(kwargs['data']);calls.append(body)
        if url.endswith('startGame'):value={'e':False,'ec':0,'gn':row['symbol'],'un':'local-user','si':'local-session','dbf':False,'sgr':{'lsd':initial}}
        elif url.endswith('endSession'):value={'e':False,'ec':0}
        elif 'pos' in body or active[0]:
            md=next(states);active[0]=bool(md.get('fs') or md.get('acb'))
            value={'e':False,'ec':0,'md':md}
        else:value={'e':False,'ec':0,'md':rest}
        response=MagicMock(status_code=200,text=json.dumps(value));response.json.return_value=value;return response
    # Kick Cash Monkey capture starts with two ordinary rounds before its buy.
    if row['symbol']=='KickCashMonkey2':states=iter(row['responses'][2:])
    http=MagicMock();http.post.side_effect=post
    game=Game('ka_gaming',row['symbol'].lower(),row['symbol'],'https://gamesdemo.kaga88.com/?p=demo&g='+row['symbol'],symbol=row['symbol'])
    result=run_rmp_game(game,http=http,root=tmp_path,profile=('2071','version','local-literal'),modes=[{'id':'SPIN'}],spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None,capabilities={'common':FIXTURE['common'],'client':row['client']})
    assert enforce_complete_path_coverage(result).status=='OK',result.error
    expected=0 if row['symbol']=='BonusVending' else 1
    assert sum('pos' in c for c in calls)==expected
    assert len(result.feature_domains['purchase']['options'])==expected
    for attempt in result.attempts:
        proof=json.loads((Path(attempt.artifact_dir)/'return-to-base.json').read_text())
        assert proof['status']=='CONFIRMED' and proof['consecutive_base']==2


@pytest.mark.parametrize('field', ['oda','t$a'])
def test_unrecognized_outer_override_is_not_inherited_absence(field):
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    row=FIXTURE['games'][0]
    source=row['client'].replace('oda:function(){return!v.tS()&&!v.uoa}',field+':function(){if(!v.uoa){return true;}return false;}')
    category='purchase' if field=='oda' else 'ante'
    assert client_declarations(FIXTURE['common'],source,row['symbol'],row['initial'])['domains'][category]['complete'] is False



def test_other_descriptor_cannot_override_registered_game():
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    row=FIXTURE['games'][0]
    client='var another=xd.extend({ctor:function(){},foo:function(){return!1}});'+row['client']
    assert client_declarations(FIXTURE['common'],client,row['symbol'],row['initial'])['domains']['purchase']['options']==['pos:1']


def test_nonfunction_override_does_not_prove_inherited_absence():
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    row=FIXTURE['games'][0]
    client=row['client'].replace('oda:function(){return!v.tS()&&!v.uoa}','oda:unknownValue')
    assert client_declarations(FIXTURE['common'],client,row['symbol'],row['initial'])['domains']['purchase']['complete'] is False


@pytest.mark.parametrize('field,value',[('Oia','return new CustomMenu'),('Ya','return new CustomController')])
def test_custom_factory_does_not_inherit_standard_purchase_count(field,value):
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    row=FIXTURE['games'][0]
    client=row['client'].replace(field+':function(){'+('return new Uc' if field=='Oia' else 'return ce.create(this.Cc(),this.la)')+'}',field+':function(){'+value+'}')
    assert client_declarations(FIXTURE['common'],client,row['symbol'],row['initial'])['domains']['purchase']['complete'] is False



def test_button_subclass_with_unknown_dispatch_stays_pending():
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    row=FIXTURE['games'][0]
    common=FIXTURE['common'].replace('Uc=Eba.extend({','Uc=Eba.extend({lc:function(){Ab.kW(this.la,[2],this.Ol,this.mj,this.ko,v.cq,function(){})},')
    assert client_declarations(common,row['client'],row['symbol'],row['initial'])['domains']['purchase']['complete'] is False


def test_terminal_round_without_return_proof_cannot_be_ok(tmp_path):
    import threading
    from unittest.mock import MagicMock,patch
    from tester_spin.models import Game
    from tester_spin.providers.ka_gaming.runtime import run_rmp_game
    row=next(r for r in FIXTURE['games'] if r['symbol']=='BonusVending')
    state=next(s for s in reversed(row['responses']) if not s.get('fs') and s.get('acb')==0)
    def post(url,**kwargs):
        value={'e':False,'ec':0}
        if url.endswith('startGame'):value.update(un='new-user',si='new-session',dbf=False,sgr={'lsd':state})
        elif url.endswith('spin'):value['md']=state
        reply=MagicMock(status_code=200,text=json.dumps(value));reply.json.return_value=value;return reply
    http=MagicMock();http.post.side_effect=post
    game=Game('ka_gaming','synthetic','Synthetic','https://gamesdemo.kaga88.com/?p=demo',symbol=row['symbol'])
    with patch('tester_spin.return_to_base.verify_return_to_base',return_value={'status':'REVIEW_REQUIRED'}):
        result=run_rmp_game(game,http=http,root=tmp_path,profile=('2071','version','literal'),modes=[{'id':'SPIN'}],
            spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None,
            capabilities={'common':FIXTURE['common'],'client':row['client']})
    assert result.status=='PARCIAL' and not result.attempts[0].ok
    assert result.attempts[0].terminal


def test_registered_anonymous_descriptor_can_have_metadata_before_constructor():
    from tester_spin.providers.ka_gaming.capabilities import client_declarations
    source='new (xd.extend({Q4:88,ctor:function(a){"undefined"===typeof a?(this._super(null),A.Bb().Gg("Synthetic",this)):this._super(a)},Ya:function(){return ce.create(this.Cc(),this.la)}}));'
    result=client_declarations(FIXTURE['common'],source,'Synthetic',{})
    assert all(d['complete'] and d['options']==[] for d in result['domains'].values())
    for bad in [source.replace('Synthetic','Other'),source.replace('ctor:function(a)', 'unused:function(a)'),
                'if(false){'+source+'}', 'function unused(){'+source+'}',
                'var xd=xd.extend({oda:function(){return!0}});'+source]:
        assert not client_declarations(FIXTURE['common'],bad,'Synthetic',{})['domains']['purchase']['complete']
