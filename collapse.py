#!/usr/bin/env python
import sys
d = 0
for line in sys.stdin:
  for c in line:
    if c=='(': d+=1
    if c==')': d-=1
  if d>0:
    print line.strip(),
  elif d==0:
    print line.strip()
  else: assert False, "wtf"

