# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
"""Bounded app-specific UI mappings. No shell commands in mapping data."""
import time,re
import xml.etree.ElementTree as E
class Stop(RuntimeError):pass

def validate_mapping(m):
    if set(m) != {'name','package','activity','version','steps','post_ids'}: raise ValueError('mapping fields')
    if any(not isinstance(m[k],str) or not m[k] or len(m[k])>200 for k in ('name','package','activity','version')): raise ValueError('identity')
    if not isinstance(m['steps'],list) or not 1<=len(m['steps'])<=3: raise ValueError('steps')
    if any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+',m[k]) for k in ('package','activity')):raise ValueError('unsafe identity')
    total=0
    for s in m['steps']:
        if set(s)!={'keys','spacing_ms','settle_ms','require_focus','select'}: raise ValueError('step fields')
        if not isinstance(s['keys'],list) or not 1<=len(s['keys'])<=8 or any(type(k)!=int or k not in {19,20,21,22,127} for k in s['keys']): raise ValueError('keys')
        total+=len(s['keys'])
        if total>12: raise ValueError('too many keys')
        if type(s['spacing_ms'])!=int or not 100<=s['spacing_ms']<=500: raise ValueError('spacing')
        if type(s['settle_ms'])!=int or not 100<=s['settle_ms']<=500: raise ValueError('settle')
        if type(s['select'])!=bool or not isinstance(s['require_focus'],str) or not s['require_focus']: raise ValueError('focus guard')
    if not isinstance(m['post_ids'],list) or not 1<=len(m['post_ids'])<=8 or any(not isinstance(v,str) or not v for v in m['post_ids']):raise ValueError('postconditions')

def parse(xml):
    try: return list(E.fromstring(xml).iter('node'))
    except E.ParseError: raise Stop('Malformed hierarchy; return to operator observation')

def execute(m,d):
    validate_mapping(m);started=time.monotonic();deadline=started+30;timeline=[]
    def check():
        if d.cancelled():raise Stop('Cancelled')
        if time.monotonic()-started>30:raise Stop('Deadline')
        if d.state()!=(m['package'],m['activity'],m['version']):raise Stop('App/activity/version mismatch; return to operator observation')
        if time.monotonic()>=deadline or d.cancelled():raise Stop('Deadline or cancelled after state check')
    for s in m['steps']:
        check(); d.keys(s['keys'],s['spacing_ms'],s['settle_ms'],valid_until=deadline)
        before=time.monotonic(); nodes=parse(d.observe()); observed=time.monotonic()
        if observed-before>4:raise Stop('Observation too slow for transient menu')
        focused=[n for n in nodes if n.get('focused')=='true']
        if len(focused)!=1 or any(focused[0].get(k)!=v for k,v in {'package':m['package'],'resource-id':s['require_focus'],'enabled':'true'}.items()):raise Stop('Target focus mismatch; return to operator observation')
        check()
        if time.monotonic()-observed>1:raise Stop('Stale focus')
        if s['select']:d.keys([23],0,200,valid_until=min(deadline,observed+1))
        timeline.append(round((time.monotonic()-started)*1000,1))
    check();nodes=parse(d.observe());check()
    if not all(any(n.get('package')==m['package'] and n.get('resource-id')==rid for n in nodes) for rid in m['post_ids']):raise Stop('Postcondition missing; no blind retry')
    return {'verified':True,'mapping':m['name'],'step_ms':timeline,'total_ms':round((time.monotonic()-started)*1000,1)}
