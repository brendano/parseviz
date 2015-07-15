"""Some utilities for Python CGI
[brendan oconnor feb 2010, anyall.org/cgiutil.py]

OK, it's 2010 and there are now a zillion alternatives to CGI.
But every time I try one, I always come back.
It's just so much easier from a unix-based deployment perspective.
(PHP is ideal.  CGI is close though not quite as good.)

If you run this you get a skeleton cgi app with example usage.

It requires the following Apache directives.
  AddHandler cgi-script .cgi
  Options [... bla bla ...] ExecCGI
And maybe (ubuntu/debian)
  $ sudo a2enmod cgi && sudo /etc/init.d/apache2 reload
"""
from __future__ import with_statement
import sys,os,cgi
from copy import copy

def safehtml(x):
  return cgi.escape(str(x),quote=True)

def unicodify(s, encoding='utf8', *args):
  """ because {str,unicode}.{encode,decode} is anti-polymorphic, but sometimes
  you can't control which you have. """
  if isinstance(s,unicode): return s
  if isinstance(s,str): return s.decode(encoding, *args)
  return unicode(s)

class Struct(dict):
  def __getattr__(self, a):
    if a.startswith('__'):
      raise AttributeError
    return self[a]
  def __setattr__(self, a, v):
    self[a] = v

def type_clean(val,type):
  if type==bool:
    if val in (False,0,'0','f','false','False','no','n'): return False
    if val in (True,1,'1','t','true','True','yes','y'): return True
    raise Exception("bad bool value %s" % repr(val))
  if type==str or type==unicode:
    # nope no strings, you're gonna get unicode instead!
    return unicodify(val)
  return type(val)

class Opt(object): pass

type_builtin = type
def opt(name, type=None, default=None, values=None):
  o = Opt()
  o.__dict__.update(name=name,type=type,default=default,values=values)
  if type is None:
    if default is not None:
      o.type = type_builtin(default)
    else:
      o.type = str #raise Exception("need type for %s" % name)
  #if o.type==bool: o.type=int
  return o

class Opts(Struct):
  " modelled on trollop.rubyforge.org and gist.github.com/5682 "
  def __init__(self, *optlist):
    self.optspecs = {}
    environ = os.environ
    # can't use cgi.py's form processing: we want to handle POST content ourselves now
    vars = cgi.parse_qs(environ['QUERY_STRING'] or sys.stdin.read())

    for opt in optlist:
      # fix up the opt spec
      if opt.values and not opt.default:
        opt.default = opt.values[0]

      # save it for later
      self.optspecs[opt.name] = opt

      # value processing from GET/POST info
      val = vars.get(opt.name)
      val = val[0] if val else None
      if val is None and opt.default is not None:
        val = copy(opt.default)
      elif val is None:
        raise Exception("option not given: %s" % opt.name)
      val = type_clean(val, opt.type)
      self[opt.name] = val

  def input(self, name, **kwargs):
    val = self[name]
    h = '''<input id=%s name=%s value="%s"''' % (name, name, safehtml(val))
    more = {}
    if type(val)==int:
      more['size'] = 2
    elif type(val)==float:
      more['size'] = 4
    more.update(kwargs)
    for k,v in more.iteritems():
      h += ''' %s="%s"''' % (k,v)
    h += ">"
    return h

  def select(self, name):
    selected_value = self[name]
    h = '<select name="' +safehtml(name)+ '">'
    for value in self.optspecs[name].values:
      h += '<option name="%s"' % safehtml(value)
      if value==selected_value:
        h += " selected"
      h += ">" + safehtml(value) + "</option>"
    h += "</select>"
    return h


def make_skel():
  """makes options/viewer-oriented cgi skeleton app in current directory"""

  os.system("cp %s ." % os.path.join(os.path.dirname(__file__), "cgiutil.py"))
  assert not os.path.exists("index.cgi")

  with open("index.cgi",'w') as f:
    f.write(r'''#!/usr/bin/env python
import cgi,sys,os,re
import cgitb; cgitb.enable()
from cgiutil import *   # anyall.org/cgiutil.py

print "Content-Type: text/html\n"

print """<style>
body{font-family:"helvetica neue",arial,sans-serif; font-size:10pt; }
td  {font-family:"helvetica neue",arial,sans-serif; font-size:10pt; }
pre {font-family:"helvetica neue",arial,sans-serif; white-space: pre-wrap; white-space: -moz-pre-wrap; white-space: -pre-wrap; white-space: -o-pre-wrap; word-wrap: break-word; }
</style>"""

print """<script src=http://ajax.googleapis.com/ajax/libs/jquery/1.4.1/jquery.min.js></script>"""

print """<script>
$(document).ready(function() {
  $('input[name=q]').focus()
})
</script>"""


print "<a href=.><h1>this is an app</h1></a>"
print "bla <i>bla</i> bla. <br>"

opts = Opts(
    opt('q', default=""),
    opt('parser', default="SP_DepSD", values=['SP_DepSD','SP_DepLTH']),
)
print opts
print "<form method=get action=.>"
print opts.input('q', style="width:300px")
print opts.select('parser')
print "<input type=submit>"
print "</form>"

print "<table>"
for k,v in sorted(os.environ.items()):
  print "<tr><td>" + safehtml(k) + "<td>" + safehtml(v)
print "</table>"
''')
  os.system("chmod +x index.cgi")

if __name__=='__main__':
  make_skel()
