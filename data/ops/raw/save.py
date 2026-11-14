#!/usr/bin/env python3
"""Turn a fetch_page payload into a cache body + verbatim copy + stamp."""
import sys, os, json, datetime
RAW = "/home/user/X4/data/ops/raw"
VERBATIM = "/home/user/X4/data/ops/raw/verbatim"
def main(src, name):
    payload = open(src, encoding='utf-8').read()
    os.makedirs(RAW, exist_ok=True); os.makedirs(VERBATIM, exist_ok=True)
    # verbatim, exactly as retrieved (may include the ```json fence)
    open(os.path.join(VERBATIM, name + '.retrieved.txt'), 'w', encoding='utf-8').write(payload)
    t = payload.strip()
    if t.startswith('```'):
        nl = t.find('\n'); t = t[nl+1:] if nl>=0 else t
        if t.rstrip().endswith('```'): t = t.rstrip()[:-3]
    t = t.strip()
    try:
        json.loads(t); body = t
    except json.JSONDecodeError:
        body = payload          # not JSON (an HTML page): keep verbatim
    open(os.path.join(RAW, name), 'w', encoding='utf-8').write(body)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    open(os.path.join(RAW, name + '.stamp'), 'w', encoding='utf-8').write(stamp + '\n')
    print(name, len(body), stamp, 'json' if body is t else 'text')
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
