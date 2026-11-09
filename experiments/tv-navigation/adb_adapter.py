# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
from device_config import adb_serial, expected_device
"""Supervised one-shot prototype adapter; no daemon, no new access grant."""
import argparse,contextlib,fcntl,json,pathlib,re,subprocess,time,uuid
from runner import execute,Stop
BASE=pathlib.Path(__file__).resolve().parent
class Adb:
 def __init__(self,mapping,cancel_file):
  self.mapping=mapping;self.cancel_file=cancel_file;self.path='/sdcard/tv-macro-'+uuid.uuid4().hex+'.xml';self.version=None
 def call(self,*args,timeout=5):
  return subprocess.run(['adb','-s',adb_serial(),*args],capture_output=True,check=True,timeout=timeout).stdout
 def cancelled(self):return self.cancel_file.exists()
 def state(self):
  s=self.call('shell','dumpsys','window').decode()
  line=next((l for l in s.splitlines() if 'mCurrentFocus=' in l),'')
  match=re.search(r'\bu\d+ ([\w.]+)/([\w.$]+)',line)
  if not match:return None,None,None
  package,activity=match.groups()
  if activity.startswith('.'):activity=package+activity
  if self.version is None:
   text=self.call('shell','dumpsys','package',self.mapping['package']).decode()
   v=re.search(r'^\s*versionName=(\S+)',text,re.M);self.version=v.group(1) if v else None
  return package,activity,self.version
 def identity(self):
  # Fresh actual foreground version, separate from mapping-bound execution cache.
  text=self.call('shell','dumpsys','window').decode()
  line=next((l for l in text.splitlines() if 'mCurrentFocus=' in l),'')
  match=re.search(r'\bu\d+ ([\w.]+)/([\w.$]+)',line)
  if not match:return None,None,None
  package,activity=match.groups()
  if activity.startswith('.'):activity=package+activity
  text=self.call('shell','dumpsys','package',package).decode()
  v=re.search(r'^\s*versionName=(\S+)',text,re.M)
  return package,activity,v.group(1) if v else None
 def observe(self):
  path='/sdcard/tv-macro-'+uuid.uuid4().hex+'.xml'
  try:
   result=self.call('shell','uiautomator','dump',path,timeout=8)
   if ('UI hierchary dumped to: '+path).encode() not in result:raise Stop('Fresh hierarchy dump not confirmed')
   return self.call('shell','cat',path)
  finally:
   self.call('shell','rm','-f',path)
 def keys(self,keys,spacing_ms,settle_ms,*,valid_until):
  expected=(self.mapping['package'],self.mapping['activity'],self.mapping['version'])
  for k in keys:
   if self.cancelled() or time.monotonic()>=valid_until:raise Stop('Cancelled or expired before input check')
   if self.state()!=expected:raise Stop('Foreground changed during sequence')
   if self.cancelled() or time.monotonic()>=valid_until:raise Stop('Cancelled or expired after input check')
   self.call('shell','input','keyevent',str(k),timeout=min(5,valid_until-time.monotonic()))
   time.sleep(spacing_ms/1000)
  time.sleep(settle_ms/1000)
 def close(self):
  pass

def main():
 p=argparse.ArgumentParser();p.add_argument('mapping',nargs='?',default='crunchyroll-settings',choices=['crunchyroll-settings']);g=p.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--recognize',action='store_true');a=p.parse_args()
 m=json.loads((BASE/'mappings'/f'{a.mapping}.json').read_text())
 if a.recognize:
  from screen_cache import recognize
  with (BASE/'runner.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   d=Adb(m,BASE/'STOP')
   try:
    if d.call('shell','getprop','ro.product.device').strip()!=expected_device().encode():raise Stop('Wrong device')
    result=recognize(d,json.loads((BASE/'screen_catalog.json').read_text()))
   except (Stop,subprocess.SubprocessError) as exc:
    result={'action':'refresh_observation','reason':str(exc),'mapping':None}
   print(json.dumps(result));return
 if not a.execute:print(json.dumps({'preview':m,'note':'Requires available TV, no other operator, Crunchyroll player open. Pauses playback.'}));return
 with (BASE/'runner.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  d=Adb(m,BASE/'STOP');start=time.monotonic()
  try:
   if d.call('shell','getprop','ro.product.device').strip()!=expected_device().encode():raise Stop('Wrong device')
   result=execute(m,d)
  except (Stop,subprocess.SubprocessError) as exc:result={'verified':False,'reason':str(exc),'fallback':'Return fresh observation to operator. No blind retries.'}
  finally:
   try:d.close()
   except subprocess.SubprocessError:pass
  result['wall_ms']=round((time.monotonic()-start)*1000,1)
  (BASE/'last-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));raise SystemExit(0 if result['verified'] else 1)
if __name__=='__main__':main()
