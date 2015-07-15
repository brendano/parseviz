#!/usr/bin/env python
import cgi,os,sys,urllib,md5
import cgitb;cgitb.enable()
from pprint import pprint
from copy import copy,deepcopy

from cgiutil import *

# os.environ['PATH'] = '/usr/local/bin:' + os.environ['PATH']

def safehtml(x):
  return cgi.escape(str(x),quote=True)

def get_md5(s):
  m = md5.new()
  m.update(s)
  return m.hexdigest()

import parseviz
parseviz.QUIET = True

print "Content-Type: text/html\n"
print """ <!-- tag soup 4ever -->
<title>ParseViz</title>
<style>
body{font-family:"Helvetica Neue",arial, sans-serif; font-size:10pt; }
td  {font-family:"helvetica neue",arial, sans-serif; font-size:10pt; }
form {padding-top:0;padding-bottom:0; margin-top:0;margin-bottom:0;}
</style>"""
print """<script src=http://ajax.googleapis.com/ajax/libs/jquery/1.4.1/jquery.min.js></script>"""
#print """<script src=autoHeight.js></script>"""
print """<script>
examples = {}

function do_example(name) {
  $('textarea').val(examples[name])
  $('form#parseform').submit()
}

function resize_viewer() {
  if ($('object').length > 0) {
    $('object').height($(window).height() - $('#topstuff').height() - $('#topstuff').offset().top - 15)
  }
}

$(document).ready(function(){

  $(window).resize(resize_viewer)

  if ($('[name=parsedata]').text().length == 0) {
    $('input[name=s]').focus()
  }
})

%s

</script>""" % (open("examples.js").read())
print "<div id=topstuff>" ## topstuff
print """<div>
<span style="font-size:130%; font-weight:bold"><a href=.>ParseViz</a> - parse visualization</span>
<small>
&nbsp; <a href=http://github.com/brendano/parseviz>code and documentation on github</a>  
by <a href=http://brenocon.com>brendan</a>
</small>
</div>
"""

# import parsezoo

opts = Opts(
    opt('s', default=""),
    # opt('parser', default="SP_DepSD_cc", values=[p['name'] for p in parsezoo.parsers]),
    opt('parsedata', default=""),
)

parsedata = opts.parsedata
# if not parsedata and opts.s:
#   parsedata = parsezoo.parse_sentence(opts.s, opts.parser)

if False:
  print "<form action=. method=get>"
  print "Parse sentence: "
  print opts.input('s', style="width:50%", width=200)
  print " with parser <small><sup><a href=parsezoo.html target=_blank>[info]</a></sup></small> "
  print opts.select('parser')
  print "<input type=submit>"
  print "</form>"

print "<form id=parseform action=. method=post>"

#print "<input name=sentence>
print """Enter parse(s). 
Examples: 
  <small>
<a href="javascript:do_example('tree1')">[tree]</a>
<a href="javascript:do_example('tree_mobydick')">[big tree: melville]</a>
<a href="javascript:do_example('dep1')">[deps]</a>
<a href="javascript:do_example('many_trees')">[many trees]</a>
<a href="javascript:do_example('many_deps')">[many deps]</a>
<a href="javascript:do_example('malt')">[malt-format deps]</a>
<a href="javascript:do_example('jsent')">[jsent-format tree/deps]</a>
</small>

  <br>"""
print """
<textarea name=parsedata rows=6 cols=100 style="font-family: helvetica,arial, sans-serif; font-size:9pt; width:90%%">%s</textarea>
<br>
<input type=submit>
</form>
""" % safehtml(str(parsedata))

if parsedata:
  hash = get_md5(parsedata)
  final = "output/%s.pdf" % hash
  if not os.path.exists(final):
    pdf_filename = parseviz.smart_process(parsedata, 'pdf')
    os.system("mv %s %s" % (pdf_filename, final))
    os.system("rm -f /tmp/parseviz.*")
  url = "http://www.ark.cs.cmu.edu/parseviz/%s" % final
  # http://docs.google.com/viewer has minimal info

  # g_url = "http://docs.google.com/viewer?url=%s" % urllib.quote(url)
  print "<a target=_blank href='%s'>[Open in new window]</a>" % final
  # print "<a target=_blank href='%s'>[Google Docs link]</a>" % g_url
  # print " and reload if below is stuck "
  print "</div>" ## topstuff
  # print "<iframe src='%s&embedded=true' style='width:100%%' width=600 height=400 style='border:none'></iframe>" % g_url

  print r"""
  <object data="{final}" type="application/pdf" width="100%" height=400>
    <p><a target=_blank href='{final}'>[Open in new window]</a>
  </object>
  """.format(**locals())


  # print "<script>resize_viewer()</script>"


