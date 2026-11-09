# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
import copy, json, pathlib, unittest
from screen_cache import lookup

class CacheTests(unittest.TestCase):
    def setUp(self):
        self.c = json.loads(pathlib.Path(__file__).with_name('screen_catalog.json').read_text())
        self.c['apps'][0]['screens'][0]['status']='live_verified'  # synthetic test fixture
        self.o = dict(package='com.crunchyroll.crunchyroid', activity='com.crunchyroll.crunchyroid.player.ui.PlayerActivity', version='3.80.0', success=True, started=10, completed=12, xml=self.xml('btnPlayPause','btnSettings'))
    def xml(self,*ids):
        return '<hierarchy>'+''.join(f'<node package="com.crunchyroll.crunchyroid" enabled="true" resource-id="{i}"/>' for i in ids)+'</hierarchy>'
    def result(self): return lookup(self.c,self.o,now=12.2)
    def test_match(self): self.assertEqual(self.result()['action'],'guarded_mapping_available')
    def test_no_mapping_drawer(self):
        self.o['xml']=self.xml('playerSettingsAudioDrawerItem','playerSettingsSubtitlesDrawerItem')
        self.assertEqual(self.result()['action'],'observe_only')
    def test_stale(self): self.assertEqual(lookup(self.c,self.o,now=14)['action'],'refresh_observation')
    def test_failed(self): self.o['success']=False;self.assertEqual(self.result()['reason'],'failed_observation')
    def test_version(self): self.o['version']='4';self.assertEqual(self.result()['reason'],'unverified_app_version')
    def test_unknown_app(self): self.o['package']='unknown';self.assertEqual(self.result()['reason'],'unknown_or_ambiguous_app')
    def test_activity(self): self.o['activity']='other';self.assertEqual(self.result()['reason'],'unknown_or_ambiguous_screen')
    def test_foreign(self): self.o['xml']=self.o['xml'].replace('com.crunchyroll.crunchyroid','other');self.assertEqual(self.result()['reason'],'foreign_or_missing_nodes')
    def test_ambiguous(self): self.c['apps'][0]['screens'].append(copy.deepcopy(self.c['apps'][0]['screens'][0]));self.assertEqual(self.result()['reason'],'unknown_or_ambiguous_screen')
    def test_malformed(self): self.o['xml']='bad';self.assertEqual(self.result()['reason'],'invalid_observation')
    def test_slow(self): self.o['started']=1;self.assertEqual(self.result()['reason'],'stale_or_slow_observation')
    def test_nan(self): self.o['completed']=float('nan');self.assertEqual(self.result()['reason'],'invalid_clock')
    def test_future(self): self.o['completed']=13;self.assertEqual(self.result()['reason'],'stale_or_slow_observation')
    def test_disabled(self): self.o['xml']=self.o['xml'].replace('enabled="true"','enabled="false"');self.assertEqual(self.result()['reason'],'unknown_or_ambiguous_screen')

if __name__=='__main__': unittest.main()

class RecognitionTests(unittest.TestCase):
    def test_changes_fail_closed(self):
        from screen_cache import recognize
        class Device:
            i=0
            def cancelled(self):return False
            def identity(self):self.i+=1;return ('p','a',str(self.i))
            def observe(self):return '<hierarchy/>'
        self.assertEqual(recognize(Device(),{},clock=lambda:1)['reason'],'identity_changed_or_cancelled')
    def test_cancellation_no_reads(self):
        from screen_cache import recognize
        class Device:
            def cancelled(self):return True
        self.assertEqual(recognize(Device(),{})['reason'],'cancelled')
