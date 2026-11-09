# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
import os
from unittest.mock import patch
_config = patch.dict(os.environ, {"TV_ADB_SERIAL": "fixture-only", "TV_EXPECTED_DEVICE": "G10"})
def setUpModule(): _config.start()
def tearDownModule(): _config.stop()
import subprocess, unittest
from unittest.mock import Mock
from launch_app import launch
class Tests(unittest.TestCase):
 def setUp(self):self.stop=Mock();self.stop.exists.return_value=False
 def run_with(self,outs):
  run=Mock(side_effect=[subprocess.CompletedProcess([],0,stdout=x.encode()) for x in outs])
  result=launch('max',stop_file=self.stop,run=run)
  return result,run
 def test_success_no_input(self):
  result,run=self.run_with(['G10','Packages:\n  Package [com.wbd.stream] (a):\n    versionName=22.0.0.36\n','Status: ok','mCurrentFocus=Window{a u0 com.wbd.stream/com.wbd.beam.BeamActivity}'])
  self.assertTrue(result['verified_foreground']);self.assertFalse(result['playback_verified'])
  for call in run.call_args_list:self.assertNotIn('input',call.args[0]);self.assertIn('timeout',call.kwargs)
 def test_wrong_device(self):
  r,run=self.run_with(['other']);self.assertFalse(r['verified_foreground']);self.assertEqual(run.call_count,1)
 def test_wrong_version(self):
  r,run=self.run_with(['G10','Packages:\n  Package [com.wbd.stream] (a):\n    versionName=99\n']);self.assertFalse(r['verified_foreground']);self.assertEqual(run.call_count,2)
 def test_stop_no_calls(self):
  self.stop.exists.return_value=True;run=Mock();r=launch('max',stop_file=self.stop,run=run);run.assert_not_called();self.assertFalse(r['verified_foreground'])
 def test_unknown(self):
  with self.assertRaises(ValueError):launch('com.android.settings',stop_file=self.stop)
 def test_command_error(self):
  r=launch('max',stop_file=self.stop,run=Mock(side_effect=subprocess.TimeoutExpired('adb',5)));self.assertFalse(r['verified_foreground'])
 def test_am_error(self):
  r,run=self.run_with(['G10','Packages:\n  Package [com.wbd.stream] (a):\n    versionName=22.0.0.36\n','Error type 3']);self.assertFalse(r['verified_foreground']);self.assertTrue(r['launch_may_have_taken_effect'])
 def test_foreground_timeout(self):
  t=[0.0]
  def clock():return t[0]
  def run(args,**kw):
   t[0]+=1
   out='G10' if 'getprop' in args else 'Packages:\n  Package [com.wbd.stream] (a):\n    versionName=22.0.0.36\n' if 'package' in args else 'wrong foreground'
   return subprocess.CompletedProcess(args,0,stdout=out.encode())
  r=launch('max',stop_file=self.stop,run=run,clock=clock,sleep=lambda s:None)
  self.assertFalse(r['verified_foreground']);self.assertLessEqual(t[0],20)
if __name__=='__main__':unittest.main()

class ActiveVersionTests(unittest.TestCase):
 def dump(self,active='current'):
  return 'Packages:\n  Package [p.app] (aa):\n    versionName='+active+'\n\nHidden system packages:\n  Package [p.app] (bb):\n    versionName=factory\n'
 def test_hidden_ignored(self):
  from launch_app import active_version
  self.assertEqual(active_version(self.dump(),'p.app'),'current')
 def test_active_change_not_hidden(self):
  from launch_app import active_version
  self.assertEqual(active_version(self.dump('new'),'p.app'),'new')
 def test_no_active_fails(self):
  from launch_app import active_version,Halt
  with self.assertRaises(Halt):active_version(self.dump().replace('Packages:','Other:'),'p.app')
 def test_other_package_not_selected(self):
  from launch_app import active_version,Halt
  with self.assertRaises(Halt):active_version(self.dump(),'other.app')
 def test_duplicate_target_fails(self):
  from launch_app import active_version,Halt
  with self.assertRaises(Halt):active_version(self.dump().replace('Hidden system packages:', '  Package [p.app] (cc):\n    versionName=current\nHidden system packages:'),'p.app')
 def test_hidden_only_matching_version_blocks_launch(self):
  from unittest.mock import Mock
  run=Mock(side_effect=[subprocess.CompletedProcess([],0,stdout=b'G10'),subprocess.CompletedProcess([],0,stdout=self.dump('new').replace('p.app','com.wbd.stream').replace('factory','22.0.0.36').encode())])
  stop=Mock();stop.exists.return_value=False
  r=launch('max',stop_file=stop,run=run)
  self.assertFalse(r['verified_foreground']);self.assertEqual(run.call_count,2)
