#!/usr/bin/env python

"""
parseviz.py

Give this an s-expression, treebank-style parse tree on STDIN, or a CoNLL
dependency format. This script will make a graphviz graphic and open it on your
computer to look at.  Some sensible colors have been chosen for
 * PTB-style POS tags
 * PTB constituent tree non-terminals
 * LTH-style (pennconverter, penn2malt) dependencies
 * Stanford dependencies

(Though for many purposes the defaults give too many colors.)

Brendan O'Connor (anyall.org)
http://www.ark.cs.cmu.edu/parseviz

This has only been tested on linux and mac
and requires GraphViz to be installed - the 'dot' command.
"""

from __future__ import with_statement
import sys,os,time,pprint,re,json

QUIET = False

nounish = '#700070'
verbish = '#207020'
prepish = '#C35617'
modifiers = '#902010'
coordish = '#404090'
fade = '#b0b0b0'

# simpler alternatives
#nounish = '#700070'
#verbish = '#d02020'


## LTH/pennconverter and penn2malt dependency label colors

dep_colors = {
# tricky. LTH uses SUB for "subordinate clause" but penn2malt uses it for "subject".
  #'SUB': '#202090',
  'SBJ': '#202090',
  #'OBJ': '#903030',
  #'OBJ': '#CC009C',
  'OBJ': ' #9F336C',
  'PMOD': prepish,
  'COORD': coordish,
  'CONJ': coordish,
  #'SBAR': prepish,
  'NMOD': nounish,
  'VMOD': verbish,
  'VC': verbish,
  'AMOD': modifiers,
  #'ADV': modifiers,
  'P': fade,
}

## Stanford dependency label colors
# parts out of the stanford dep hierarchy
d = dep_colors
for c in 'aux auxpass cop'.split(): d[c] = verbish
for c in 'subj nsubj nsubjpass csubj'.split(): d[c] = d['SBJ']
for c in 'obj dobj iobj '.split(): d[c] = d['OBJ']
#for c in 'arg comp agent   attr ccomp xcomp compl mark rel acomp'.split(): d[c]=d['OBJ']
  #if pos.startswith('prep'): return prepish
#for c in 'mod advcl purpcl tmod rcmod amod infmod partmod num number  appos nn abbrev advmod neg poss possessive prt det prep'.split(): d[c]=d['AMOD']
d['nn'] = nounish
#d['amod'] = modifiers
del d


def pos_color(pos):
  if pos.startswith('VB') or pos=='MD': return verbish
  if pos.startswith('NN') or pos.startswith('PRP') or pos.startswith('NNP'): return nounish
  if pos in ('IN','TO'): return prepish
  #if pos.startswith('JJ') or pos.endswith('DT'): return fade
  if pos.startswith('RB') or pos.startswith('JJ'): return modifiers

  if pos.startswith('NP'): return nounish
  if pos.startswith('VP'): return verbish
  if pos.startswith('PP'): return prepish
  if pos in ('ADVP','ADJP'): return modifiers
  if pos=='CC': return coordish

  return 'black'

## some counts
#1398844 NMOD
#575426 VMOD
#422175 PMOD
#402221 P
#262052 SUB
#149750 OBJ
#138129 ROOT
#138129 
#122029 VC
#77576 SBAR
#70289 AMOD
#41906 PRD
#9181 DEP

#dep_bold = set(['SBJ','OBJ'])
dep_bold = set([])



def parse_sexpr(s):
  s = s[s.find('('):]
  tree = []
  stack = []  # top of stack (index -1) points to current node in tree
  stack.append(tree)
  curtok = ""
  depth = 0
  for c in s:
    if c=='(':
      new = []
      stack[-1].append(new)
      stack.append(new)
      curtok = ""
      depth += 1
    elif c==')':
      if curtok:
        stack[-1].append(curtok)
        curtok = ""
      stack.pop()
      curtok = ""
      depth -= 1
    elif c.isspace():
      if curtok:
        stack[-1].append(curtok)
        curtok = ""
    else:
      curtok += c
    if depth<0: raise BadSexpr("Too many closing parens")
  if depth>0: raise BadSexpr("Didn't close all parens, depth %d" % depth)
  root = tree[0]
  # weird
  if isinstance(root[0], list):
    root = ["ROOT"] + root
  return root

class BadSexpr(Exception): pass

def is_balanced(s):
  if '(' not in s: return False
  d = 0
  for c in s:
    if c=='(': d += 1
    if c==')': d -= 1
    if d<0: return False
  return d==0

def node_is_leaf(node):
  return isinstance(node, (unicode,str))

counter = 0
def graph_tuples(node, parent_pos=None):
  # makes both NODE and EDGE tuples from the tree
  global counter
  my_id = counter
  if node_is_leaf(node):
    col = pos_color(parent_pos)
    return [("NODE", my_id, node, {'shape':'box','fontcolor':col, 'color':col})]
  tuples = []
  name = node[0]
  name = name.replace("=H","")
  #color = 'blue' if name=="NP" else 'black'
  color = pos_color(name)
  tuples.append(("NODE", my_id, name, {'shape':'none','fontcolor':color}))
  
  for child in node[1:]:
    counter += 1
    child_id = counter
    opts = {}
    if len(node)>2 and isinstance(child,list) and child[0].endswith("=H"):
      opts['arrowhead']='none'
      opts['style']='bold'
    else:
      opts['arrowhead']='none'
    opts['color'] = pos_color(name) if node_is_leaf(child) else \
        pos_color(name) if pos_color(child[0]) == pos_color(name) else \
        'black'
    tuples.append(("EDGE", my_id, child_id, opts))
    tuples += graph_tuples(child, name)
  return tuples

def dot_from_tuples(tuples):
  # takes graph_tuples and makes them into graphviz 'dot' format
  dot = "digraph { "
  for t in tuples:
    if t[0]=="NODE":
      more = " ".join(['%s="%s"' % (k,v) for (k,v) in t[3].items()]) 
      dot += """%s [label="%s" %s]; """ % (t[1], t[2], more)
    elif t[0]=="EDGE":
      more = " ".join(['%s="%s"' % (k,v) for (k,v) in t[3].items()]) 
      dot += """ %s -> %s [%s]; """ % (t[1],t[2], more)
  dot += "}"
  return dot

def make_svg(tuples):
  assert False, "not done yet"
  print tuples
  words = [row for row in tuples if row[0]=='NODE']

def make_html(filename, svg):
  assert False, "not done yet"
  with open(filename,'w') as f:
    print>>f, svg

def call_dot(dotstr, filename="/tmp/parseviz.png", format='png'):
  dot = "/tmp/parseviz.%s.dot" % stamp()
  with open(dot, 'w') as f:
    print>>f, dotstr.encode('utf8')

  if False and format=='pdf':
    cmd = "dot -Teps < " +dot+ " | ps2pdf -dEPSCrop -dEPSFitPage - > " + filename
  else:
    cmd = "dot -T" +format+ " < " +dot+ " > " + filename
  if not QUIET:
    print cmd
  os.system(cmd)

counter = 0
def stamp():
  global counter
  counter += 1
  return "%s.%s" % (os.getpid(), counter)

def open_file(filename):
  import webbrowser
  f = "file://" + os.path.abspath(filename)
  webbrowser.open(f)
  # os.system(opener + " " + filename)

def show_tree(sexpr, format):
  tree = parse_sexpr(sexpr)
  tuples = graph_tuples(tree)
  dotstr = dot_from_tuples(tuples)
  filename = "/tmp/parseviz.%s.%s.%s" % (os.getid(), time.time(),format)
  call_dot(dotstr, filename, format=format)
  return filename

# We seem to be using 1-indexing, so 0 is root

def tokrecords_to_tuples(tokrecords):
  """returns tuples to turn into GraphViz directives"""
  ret = []
  for tokid, word_surface, pos, parent, deprel in tokrecords:
    if tokid != 0:
      col = pos_color(pos)
      ret.append(("NODE", tokid, "%s /%s" % (word_surface,pos), {'shape':'none', 'fontcolor':col}))
    opts = {'label':deprel.lower(),'dir':'forward'}  #forward back both none
    if deprel in dep_colors:
      opts.update({'fontcolor':dep_colors[deprel], 'color':dep_colors[deprel]})
    if deprel in dep_bold: opts['fontname'] = 'Times-Bold'
    if parent!=-1 and word_surface != 0:
      ret.append(("EDGE", parent,tokid, opts))
  return ret

def conll_to_tuples(conll):
  tokrecords = []
  rows = [line.split() for line in conll.split("\n") if line.strip()]
  for row in rows:
    tokid = int(row[0])
    word=row[1]
    pos=row[3]         ## Usual POS, I think
    #pos=row[4]         ## Google Web Treebank fine-grained POS
    target = int(row[6])
    deprel = row[7]
    tokrecords.append((tokid,word,pos,target,deprel))
  return tokrecords_to_tuples(tokrecords)

def malt_to_tuples(malt_string):
  def f():
    bigtoks = malt_string.split()
    for myid,bigtok in enumerate(bigtoks):
      word,pos,parent,deprel = bigtok.split('/')
      yield myid+1, word, pos, parent, deprel
  return tokrecords_to_tuples(list(f()))

def jsent_to_dep_tuples(jsent_line):
  parts = jsent_line.split('\t')
  jsent = json.loads(parts[-1])
  def f():
    for k in ['deps','deps_cc']:
      if k in jsent:
        deprows = jsent[k]
    for deprow in deprows:
      deprel,headid,childid = deprow[:3]
      word,lemma,pos = [jsent[k][childid] for k in ['tokens','lemmas','pos']]
      yield childid+1, word, pos, headid+1, deprel
  return tokrecords_to_tuples(list(f()))


def show_conll(conll, format):
  tuples = conll_to_tuples(conll)
  filename = "/tmp/parseviz.%s.%s" % (stamp(), format)
  if format=='html':
    svg = make_svg(tuples)
    make_html(filename, svg)
  else:
    dotstr = dot_from_tuples(tuples)
    call_dot(dotstr, filename, format=format)
  return filename

def do_multi_tree(parses, to_tuples):  ##= lambda s: dot_from_tuples(graph_tuples(s))):
  base = "/tmp/parseviz.%s_NUM.pdf" % stamp()
  for i,parse in enumerate(parses):
    output = base.replace("NUM", "%.03d" % (i+1))
    call_dot(dot_from_tuples(to_tuples(parse)), filename=output, format='pdf')
  output = base.replace("NUM","merged")
  inputs = base.replace("NUM","*")
  os.system("gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=%s %s" % (output,inputs))
  return output

def is_json(s):
  try:
    json.loads(s)
    return s.strip()[0]=='{' and s.strip()[-1]=='}'
  except ValueError:
    return False
  return False

def is_conll_like(lines):
  try:
    for L in lines: int(L.split()[0])
    return True
  except ValueError:
    return False
  return False

def detect_type(input):
  """return: (format, [parses_as_strings])"""
  input = input.strip()
  lines = input.split("\n")
  lines = [l for l in lines if l.strip()]

  if is_conll_like(lines):
    format = 'conll'
    parts = re.split(r'\n[ \t\r]*\n', input)
    return format,parts

  if is_json(lines[0].split('\t')[-1]):
    d = json.loads( lines[0].split('\t')[-1] )
    if 'parse' in d or 'deps' in d or 'deps_cc' in d:
      return 'jsent', lines

  elif '\t' in lines[0]:
    if is_json(lines[0].split('\t')[-1]):
      if '-tree' in sys.argv:
        return 'sexpr', [json.loads(L.split('\t')[-1])['parse'] for L in lines]
      else:
        return 'jsent', lines
    else:
      format = 'conll'
      parts = re.split(r'\n[ \t\r]*\n', input)
      return format,parts
  if re.search(r'[\(\)]', lines[0]) and is_balanced(lines[0]):
    # one sexpr per line
    return 'sexpr', lines
  if all(('/' in L and '\t' not in L) for L in lines[:100]):
    return 'malt', lines
  # single (potentially multiline) sexpr
  return 'sexpr', [input]

def smart_process(input, output_format):
  # always do multitree these days
  assert output_format=='pdf', "non-pdf doesn't work now, needs refactoring here"

  input_format, parse_strings = detect_type(input)

  if input_format=='jsent':
    # only handle singletons for now
    dep_pdf = do_multi_tree(parse_strings, jsent_to_dep_tuples)
    c_pdf = do_multi_tree(parse_strings, lambda s: graph_tuples(parse_sexpr( json.loads(s)['parse'] )))
    finalout = "/tmp/parseviz.%s_merged.pdf" % stamp()
    os.system("gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=%s %s" % 
        (finalout, ' '.join([c_pdf,dep_pdf])))
    return finalout
  else:
    if input_format=='sexpr':
      converter = lambda s: graph_tuples(parse_sexpr(s))
    elif input_format=='conll':
      converter = conll_to_tuples
    elif input_format=='malt':
      converter = malt_to_tuples
    return do_multi_tree(parse_strings, converter)

if __name__=='__main__':
  input = sys.stdin.read().strip()
  output_format = 'png' if '-png' in sys.argv else \
            'eps' if '-eps' in sys.argv else \
            'pdf' if '-pdf' in sys.argv else \
            'html' if '-html' in sys.argv else \
            'pdf' if sys.platform=='darwin' else \
            'pdf'
  output_filename = smart_process(input, output_format)
  print "OUTPUT",output_filename
  # open_file(output_filename)

# vim: sw=2:sts=2
