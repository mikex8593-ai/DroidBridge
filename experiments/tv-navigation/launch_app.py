# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
from device_config import adb_serial, expected_device
"""One-shot supervised app launch, not playback/title/profile selection.
No inputs, shell interpolation, unknown components, permissions or services.
"""
import argparse, fcntl, json, pathlib, re, subprocess, time
BASE=pathlib.Path(__file__).resolve().parent
# Entries are inventory observations, not proof of successful title navigation.
APPS={
 'hulu':('com.hulu.livingroomplus','com.hulu.livingroomplus.WKFactivity','C59F39CFP3.10.33'),
 'prime':('com.amazon.amazonvideo.livingroom','com.amazon.ignition.IgnitionActivity','6.24.13+v16.0.1.93-allAbis'),
 'paramount':('com.cbs.ott','com.paramount.android.pplus.features.splash.tv.SplashMediatorActivity','17.3.0'),
 'roku':('com.roku.web.trc','com.roku.web.trc.MainActivity','2.0.83'),
 'crunchyroll':('com.crunchyroll.crunchyroid','com.crunchyroll.crunchyroid.splash.ui.SplashActivity','3.80.0'),
 'max':('com.wbd.stream','com.wbd.beam.BeamActivity','22.0.0.36'),
 'peacock':('com.peacocktv.peacockandroid','com.peacock.peacocktv.GoogleMainActivity','7.10.200'),
 'tubi':('com.tubitv','com.tubitv.activities.MainActivity','10.44.5000'),
 'netflix':('com.netflix.ninja','com.netflix.ninja.MainActivity','13.2.2 build 27249'),
 'disney':('com.disney.disneyplus','com.bamtechmedia.dominguez.main.MainActivity','26.20.0+rc3-2026.11.02'),
}
class Halt(RuntimeError):pass

def active_version(info, package):
 """Read exact target in active Packages section; never hidden factory versions."""
 sections=list(re.finditer(r'^Packages:[ \t]*\r?$',info,re.M))
 if len(sections)!=1:raise Halt('Missing or ambiguous active Packages section')
 body=info[sections[0].end():]
 boundary=re.search(r'^\S',body,re.M)
 if boundary:body=body[:boundary.start()]
 blocks=list(re.finditer(r'^  Package \[([^\]]+)\][^\n]*$',body,re.M))
 selected=[]
 for i,block in enumerate(blocks):
  if block.group(1)==package:
   selected.append(body[block.end():blocks[i+1].start() if i+1<len(blocks) else len(body)])
 if len(selected)!=1:raise Halt('Missing or ambiguous active package block')
 versions=re.findall(r'^[ \t]+versionName=([^\r\n]+)',selected[0],re.M)
 if len(versions)!=1:raise Halt('Missing or ambiguous active version')
 return versions[0].strip()

def launch(name, *, stop_file=BASE/'STOP', run=None, clock=None, sleep=None):
 run=run or subprocess.run; clock=clock or time.monotonic; sleep=sleep or time.sleep
 if name not in APPS:raise ValueError('Unknown allowlisted app')
 package,activity,expected_version=APPS[name]
 begin=clock(); deadline=begin+30;launch_sent=False
 def check():
  if stop_file.exists():raise Halt('STOP requested')
  if clock()>=deadline:raise Halt('Deadline expired')
 def call(*args):
  check()
  out=run(['adb','-s',adb_serial(),*args],capture_output=True,check=True,timeout=min(5,deadline-clock())).stdout.decode()
  check();return out
 try:
  if call('shell','getprop','ro.product.device').strip()!=expected_device():raise Halt('Wrong TV device')
  info=call('shell','dumpsys','package',package)
  version=active_version(info,package)
  if version!=expected_version:raise Halt('Installed version differs from verified inventory; refresh inventory')
  check();launch_sent=True
  output=call('shell','am','start','-W','-n',package+'/'+activity)
  if re.search(r'(?im)^\s*(error|exception)',output):raise Halt('Activity launch reported error')
  # Package foreground is the postcondition, not an assumed landing activity.
  # Splash may legitimately transition; no attempt to select or navigate.
  deadline=min(deadline,clock()+15)
  while True:
   state=call('shell','dumpsys','window')
   focus=next((l for l in state.splitlines() if 'mCurrentFocus=' in l),'')
   match=re.search(r'\bu\d+ ([\w.]+)/([\w.$]+)',focus)
   if match and match.group(1)==package:
    return {'verified_foreground':True,'app':name,'foreground_activity':match.group(2),'elapsed_ms':round((clock()-begin)*1000,1),'playback_verified':False,'next':'Observe actual screen; do not assume profile/title/playback.'}
   check();sleep(min(.25,max(0,deadline-clock())))
 except (Halt,subprocess.SubprocessError,OSError) as exc:
  return {'verified_foreground':False,'app':name,'reason':str(exc),'launch_may_have_taken_effect':launch_sent,'playback_verified':False,'next':'Refresh actual state. No blind retry.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('app',choices=sorted(APPS));p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:
  print(json.dumps({'preview':dict(zip(('package','activity','version'),APPS[a.app])),'note':'Available TV required. Launch can resume prior playback; no profile/title selection.'}));return
 try:
  with (BASE/'runner.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   result=launch(a.app)
 except BlockingIOError:
  result={'verified_foreground':False,'reason':'Another prototype holds input lock'}
 print(json.dumps(result));raise SystemExit(0 if result['verified_foreground'] else 1)
if __name__=='__main__':main()
