import time
from pathlib import Path
from types import SimpleNamespace
import pytest

def config(tmp_path,allowed='0.0.0.0/0, ::/0'):
 path=tmp_path/'original.conf'
 path.write_text('[Interface]\nPrivateKey = private-test-key\nAddress = 10.0.0.2/32\n[Peer]\nPublicKey = public-test-key\nEndpoint = vpn.example:51820\nAllowedIPs = '+allowed+'\n',encoding='utf-8')
 return path

def test_quota_is_shared_by_actual_ip_and_counts_failed_attempts():
 from tester_spin.vpn.quota import IpQuota
 quota=IpQuota(2)
 assert quota.remaining('203.0.113.1')==2
 quota.consume('203.0.113.1');quota.consume('203.0.113.1')
 assert quota.remaining('203.0.113.1')==0
 with pytest.raises(ValueError):quota.consume('203.0.113.1')
 assert quota.remaining('203.0.113.2')==2
 assert quota.counts=={'203.0.113.1':2}

@pytest.mark.parametrize('value',[0,-1,True,1.5])
def test_quota_requires_positive_integer(value):
 from tester_spin.vpn.quota import IpQuota
 with pytest.raises(ValueError):IpQuota(value)

def test_windows_tunnel_uses_owned_copy_and_cleans_only_that_service(tmp_path):
 from tester_spin.vpn.wireguard import WireGuardTunnel
 path=config(tmp_path);original=path.read_bytes();commands=[]
 def command(args):
  commands.append(args)
  if args[-2:]==['show','interfaces']:out=tunnel.name if tunnel.installed else ''
  elif args[-1]=='latest-handshakes':out='public-key\t'+str(int(time.time()))
  elif args[-1]=='interfaces':out=tunnel.name
  else:out=''
  return SimpleNamespace(returncode=0,stdout=out)
 tunnel=WireGuardTunnel(path,platform='win32',command=command,ip_probe=lambda:'203.0.113.1',lock_factory=DummyLock)
 with tunnel as connection:
  assert connection.ip=='203.0.113.1'
  assert connection.verify()=='203.0.113.1'
 assert path.read_bytes()==original
 installs=[c for c in commands if '/installtunnelservice' in c]
 assert len(installs)==1 and Path(installs[0][-1])!=path
 assert commands[-1][-2:]==['/uninstalltunnelservice',tunnel.name]
 assert not Path(installs[0][-1]).exists()

class DummyLock:
 def __enter__(self):return self
 def __exit__(self,*args):pass

def test_existing_tunnel_is_not_modified(tmp_path):
 from tester_spin.vpn.wireguard import WireGuardTunnel,NetworkContextError
 calls=[]
 def command(args):calls.append(args);return SimpleNamespace(returncode=0,stdout='personalVPN')
 with pytest.raises(NetworkContextError,match='otro túnel'):
  with WireGuardTunnel(config(tmp_path),platform='linux',command=command,ip_probe=lambda:'203.0.113.1',lock_factory=DummyLock):pass
 assert len(calls)==1

def test_failed_activation_is_cleaned_and_never_runs_without_vpn(tmp_path):
 from tester_spin.vpn.wireguard import WireGuardTunnel,NetworkContextError
 calls=[]
 def command(args):
  calls.append(args)
  return SimpleNamespace(returncode=1 if 'up' in args else 0,stdout='' if args[-1]=='interfaces' else 'private-test-key')
 with pytest.raises(NetworkContextError) as exc:
  with WireGuardTunnel(config(tmp_path),platform='linux',command=command,ip_probe=lambda:'203.0.113.1',lock_factory=DummyLock):pytest.fail('must not execute')
 assert 'private-test-key' not in str(exc.value)
 assert any('down' in args for args in calls)

@pytest.mark.parametrize('allowed',['10.0.0.0/8','0.0.0.0/0'])
def test_partial_routes_are_not_treated_as_verified_full_tunnel(tmp_path,allowed):
 from tester_spin.vpn.wireguard import validate_config,NetworkContextError
 with pytest.raises(NetworkContextError):validate_config(config(tmp_path,allowed))

def test_custom_hooks_are_not_executed_by_runner(tmp_path):
 from tester_spin.vpn.wireguard import validate_config,NetworkContextError
 path=config(tmp_path);path.write_text(path.read_text()+'PostUp = arbitrary-command\n')
 with pytest.raises(NetworkContextError,match='hooks'):validate_config(path)

def test_ip_change_during_owned_tunnel_is_rejected(tmp_path):
 from tester_spin.vpn.wireguard import WireGuardTunnel,NetworkContextError
 ips=iter(['203.0.113.1','203.0.113.2'])
 tunnel=None
 def command(args):
  out='' if args[-1]=='interfaces' and tunnel is not None and not tunnel.installed else tunnel.name if args[-1]=='interfaces' else 'public-key\t'+str(int(time.time())) if args[-1]=='latest-handshakes' else ''
  return SimpleNamespace(returncode=0,stdout=out)
 tunnel=WireGuardTunnel(config(tmp_path),platform='win32',command=command,ip_probe=lambda:next(ips),lock_factory=DummyLock)
 with tunnel:
  with pytest.raises(NetworkContextError,match='cambió'):tunnel.verify()

def test_network_lock_rejects_overlap_and_releases():
 from tester_spin.vpn.lock import NetworkLock
 with NetworkLock():
  with pytest.raises(RuntimeError):
   with NetworkLock():pass
 with NetworkLock():pass

@pytest.mark.parametrize('table',['off','123'])
def test_route_table_override_cannot_bypass_vpn(tmp_path,table):
 from tester_spin.vpn.wireguard import validate_config,NetworkContextError
 path=config(tmp_path);path.write_text(path.read_text()+'Table = '+table+'\n')
 with pytest.raises(NetworkContextError,match='Table'):validate_config(path)

def test_fatal_live_process_tree_keeps_owned_vpn_active(tmp_path):
 from tester_spin.vpn.wireguard import WireGuardTunnel
 from tester_spin.independent.processes import UnsafeProcessTree
 commands=[]
 def command(args):
  commands.append(args)
  out=tunnel.name if args[-1]=='interfaces' and tunnel.installed else 'key\t'+str(int(time.time())) if args[-1]=='latest-handshakes' else ''
  return SimpleNamespace(returncode=0,stdout=out)
 tunnel=WireGuardTunnel(config(tmp_path),platform='win32',command=command,ip_probe=lambda:'203.0.113.1',lock_factory=DummyLock)
 with pytest.raises(UnsafeProcessTree):
  with tunnel:raise UnsafeProcessTree('live')
 assert tunnel.installed and not any('/uninstalltunnelservice' in c for c in commands)
 tunnel.close()
