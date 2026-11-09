# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
import copy, unittest
from runner import execute, validate_mapping, Stop
P='com.crunchyroll.crunchyroid'
M={'name':'crunchy-settings','package':P,'activity':P+'.player.ui.PlayerActivity','version':'3.80.0','steps':[{'keys':[127,19,19,19],'spacing_ms':200,'settle_ms':300,'require_focus':'btnSettings','select':True}], 'post_ids':['playerSettingsAudioDrawerItem','playerSettingsSubtitlesDrawerItem']}
def snap(focus='btnSettings',ids=(),pkg=P):
 return '<hierarchy>'+f'<node package="{pkg}" resource-id="{focus}" focused="true" enabled="true"/>'+''.join(f'<node package="{pkg}" resource-id="{i}"/>' for i in ids)+'</hierarchy>'
class Device:
 def __init__(self):self.calls=[];self.pkg=P;self.activity=M['activity'];self.version='3.80.0';self.xmls=[snap(),snap(ids=M['post_ids'])];self.cancel=False
 def state(self):return self.pkg,self.activity,self.version
 def observe(self):return self.xmls.pop(0)
 def keys(self,keys,spacing_ms,settle_ms,*,valid_until):self.calls.append(keys)
 def cancelled(self):return self.cancel
class Tests(unittest.TestCase):
 def test_real_contract(self):
  d=Device();r=execute(M,d);self.assertTrue(r['verified']);self.assertEqual(d.calls,[[127,19,19,19],[23]])
 def test_wrong_app_no_input(self):
  d=Device();d.pkg='other';self.assertRaises(Stop,execute,M,d);self.assertEqual(d.calls,[])
 def test_wrong_version_no_input(self):
  d=Device();d.version='4.0';self.assertRaises(Stop,execute,M,d);self.assertEqual(d.calls,[])
 def test_wrong_focus_no_select(self):
  d=Device();d.xmls[0]=snap('btnPlayPause');self.assertRaises(Stop,execute,M,d);self.assertEqual(d.calls,[[127,19,19,19]])
 def test_foreign_focus_no_select(self):
  d=Device();d.xmls[0]=snap(pkg='other');self.assertRaises(Stop,execute,M,d);self.assertEqual(len(d.calls),1)
 def test_ambiguous_focus_no_select(self):
  d=Device();d.xmls[0]=snap().replace('</hierarchy>','<node package="'+P+'" resource-id="btnSettings" focused="true" enabled="true"/></hierarchy>');self.assertRaises(Stop,execute,M,d);self.assertEqual(len(d.calls),1)
 def test_missing_post_fails(self):
  d=Device();d.xmls[1]=snap();self.assertRaises(Stop,execute,M,d)
 def test_cancel_no_input(self):
  d=Device();d.cancel=True;self.assertRaises(Stop,execute,M,d);self.assertEqual(d.calls,[])
 def test_changed_app_before_select(self):
  class Changed(Device):
   def observe(self):self.pkg='other';return super().observe()
  d=Changed();self.assertRaises(Stop,execute,M,d);self.assertEqual(len(d.calls),1)
 def test_second_mapping(self):
  m=copy.deepcopy(M);m.update(name='different',package='org.example',activity='org.example.Player',version='1');m['steps'][0]['require_focus']='Options';m['post_ids']=['AudioChoice']
  d=Device();d.pkg=m['package'];d.activity=m['activity'];d.version='1';d.xmls=[snap('Options',pkg='org.example'),snap(ids=['AudioChoice'],pkg='org.example')];self.assertTrue(execute(m,d)['verified'])
 def test_bad_key(self):
  m=copy.deepcopy(M);m['steps'][0]['keys']=[999];self.assertRaises(ValueError,validate_mapping,m)
 def test_long_macro(self):
  m=copy.deepcopy(M);m['steps'][0]['keys']=[19]*9;self.assertRaises(ValueError,validate_mapping,m)
 def test_select_requires_guard(self):
  m=copy.deepcopy(M);del m['steps'][0]['require_focus'];self.assertRaises(ValueError,validate_mapping,m)
 def test_no_shell_steps(self):
  m=copy.deepcopy(M);m['steps'][0]['shell']='rm';self.assertRaises(ValueError,validate_mapping,m)
if __name__=='__main__':unittest.main()
