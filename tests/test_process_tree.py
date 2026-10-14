import os,subprocess,sys,time
from pathlib import Path
import pytest

@pytest.mark.skipif(sys.platform not in {'win32','linux'},reason='supported process boundary')
def test_process_boundary_owns_and_closes_detached_descendants(tmp_path):
 from tester_spin.independent.processes import ProcessTree
 gate=tmp_path/'gate';spawned=tmp_path/'spawned'
 script=tmp_path/'spawn.py'
 script.write_text("import subprocess,sys,time\nfrom pathlib import Path\nwhile not Path(sys.argv[1]).exists():time.sleep(.02)\np=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)\nPath(sys.argv[2]).write_text(str(p.pid))\ntime.sleep(60)\n")
 tree=ProcessTree()
 process=subprocess.Popen([sys.executable,str(script),str(gate),str(spawned)])
 try:
  tree.bind(process.pid);gate.touch()
  deadline=time.monotonic()+10
  while not spawned.exists() and time.monotonic()<deadline:time.sleep(.02)
  assert spawned.exists() and tree.active_count()>=2
  tree.stop_and_wait()
  assert tree.active_count()==0
  assert process.wait(timeout=5)!=0
 finally:
  tree.close()
  if process.poll() is None:process.kill();process.wait(timeout=5)
