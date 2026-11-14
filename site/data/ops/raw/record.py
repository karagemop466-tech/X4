#!/usr/bin/env python3
"""Record a retrieval: verbatim body + parsed cache body + UTC stamp."""
import sys, os, json, datetime
RAW = "/home/user/X4/data/ops/raw"
def main(src, name):
    payload = open(src, encoding='utf-8').read()
    os.makedirs(RAW, exist_ok=True)
    t = payload.strip()
    if t.startswith('```'):
        nl = t.find('\n'); t = t[nl+1:] if nl >= 0 else t
        if t.rstrip().endswith('```'): t = t.rstrip()[:-3]
    t = t.strip()
    body = t
    try:
        json.loads(t)
    except json.JSONDecodeError:
        body = payload
    open(os.path.join(RAW, name), 'w', encoding='utf-8').write(body)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    open(os.path.join(RAW, name + '.stamp'), 'w', encoding='utf-8').write(stamp + '\n')
    print(name, len(body), 'bytes', stamp)
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
