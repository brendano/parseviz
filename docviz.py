# visualize CoreNLP xml files

from xml.etree import ElementTree as ET
from pprint import pprint
import json

def css():

  h = """
  .tok_block { text-align: center; display:inline-block }
  .word { display:inline; }
  .pos { color:gray; display:block; font-size:9pt; }
  .ner { color: gray; display:block; font-size:9pt; }
  .ner.emph { color: #222 }
  .token_id { color:gray; display:block; font-size:9pt}
  .nice_ent_sub { font-size: 8pt; }
  .ment_bracket { padding-left: 3pt; padding-right: 3pt }
  """

  ent_colors = " maroon navy green orange purple magenta teal  ".split()
  for i in range(100):
    col = ent_colors[i % len(ent_colors)]
    h += ".ent_num_%d { color: %s } \n" % (i, col)
  return h

def token_html(tok, left='', right=''):
  h = """
  <span class=word>{left}{word}{right}</span>
  <span class=token_id>{token_id}</span>
  <span class=pos>{pos}</span>
  <span class="ner {nerclass}">{ner}</span>
  """.format(
      token_id = tok['id'], left=left, right=right,
      word=tok['word'], pos=tok['POS'],
      ner=tok['NER'],
      nerclass= 'emph' if tok['NER']!='O' else '',
  )
  return h

def sent_html(sent_id, sent, tok_ents):
  h = ""
  h += "<div class=sent>"
  h += "<div style='vertical-align:top; display:inline-block; padding-right:10pt'>(S %s)</div>" % sent_id
  N = len(sent['tokens'])
  cur_ents = set()
  for i,tok in enumerate(sent['tokens']):
    if tok_ents[i]:
      moreclass = [ "ent_num_%d" % e['num'] for e in tok_ents[i]]
      moreclass = ' '.join(moreclass)
    else:
      moreclass = ''

    left,right = "", ""
    for ent in tok_ents[i]:
      if ent not in cur_ents:
        left += "<span class=ment_bracket>[</span>"
        cur_ents.add(ent)
    for cur_ent in set(cur_ents):
      if i == N-1 or all(e != cur_ent for e in tok_ents[i+1]):
        right += "<span class=ment_bracket>]<span class=nice_ent_sub>%s</span></span>" % (cur_ent['nice_id'])
        cur_ents.remove(cur_ent)

    th = token_html(tok, left=left, right=right)

    h += """
    <div class="tok_block {moreclass}">{token_html}</div>
    """.format(token_html= th, moreclass=moreclass)
  h += "</div>"
  return h

# Convert to a JSON-able representation
# The XML is 1-indexed for both sentences and tokens
# Convert to 0-indexed for indexing convenience

def convert_sentences(xm):
  sents = []
  for sent_x in xm.find('document').find('sentences').findall('sentence'):
    #ET.dump(sent_x)
    sent = {
        'id': int(sent_x.get('id')) - 1,
        'tokens': convert_tokens(sent_x.find('tokens').findall('token')),
        }
    sents.append(sent)
  return sents

def convert_tokens(tokens_x):
  toks = []
  for token_x in tokens_x:
    tok = {
        'id': int(token_x.get('id')) - 1,
        'word': token_x.find('word').text,
        'lemma': token_x.find('lemma').text,
        'POS': token_x.find('POS').text,
        'NER': token_x.find('NER').text,
        }
    toks.append(tok)
  return toks

class Entity(dict):
  def __hash__(self):
    return hash('entity::' + self['id'])

def convert_coref(xm, sentences):
  entities = []
  for entity_x in xm.find('document').find('coreference').findall('coreference'):
    mentions = []
    for mention_x in entity_x.findall('mention'):
      m = {}
      m['sentence'] = int(mention_x.find('sentence').text) - 1
      m['start'] = int(mention_x.find('start').text) - 1
      m['end'] = int(mention_x.find('end').text) - 1
      m['head'] = int(mention_x.find('head').text) - 1
      mentions.append(m)
    ent = Entity()
    ent['mentions'] = mentions
    first_mention = min((m['sentence'],m['head']) for m in mentions)
    ent['first_mention'] = first_mention
    ent['id'] = '%s:%s' % first_mention
    entities.append(ent)
  entities.sort()
  for i in range(len(entities)):
    ent = entities[i]
    ent['num'] = i
    s,pos = ent['first_mention']
    ent['nice_id'] = '%s:%s' % (s,pos)
    ent['nice_name'] = sentences[s]['tokens'][pos]['word']

  return entities

def convert_document(xm):
  sentences = convert_sentences(xm)
  entities = convert_coref(xm, sentences)

  # for each sentence, entity ID per token. different than lapata/barzilay "grid"
  tok_ents = [ 
      [ []  for i in range(len(sent['tokens']))]
    for sent in sentences ]
  for ent in entities:
    for ment in ent['mentions']:
      for i in range(ment['start'], ment['end']):
        tok_ents[ment['sentence']][i].append(ent)
        ## very wasteful if JSON-d

  return {'sentences':sentences, 'entities':entities, 'tok_ents': tok_ents}


if __name__=='__main__':
  import sys
  xm = ET.fromstring(open(sys.argv[1]).read())
  doc = convert_document(xm)

  print "<head><style>"
  print css()
  print "</style></head> <body>"
  for s,sent in enumerate(doc['sentences']):
    print sent_html(s, sent, doc['tok_ents'][s])

  print "<hr>"

  for ent in doc['entities']:
    print """<div class="ent_num_%d">""" % ent['num']
    hs = []
    for ment in ent['mentions']:
      text = [doc['sentences'][ment['sentence']]['tokens'][i]['word'] for i in range(ment['start'], ment['end']) ]
      #print ment
      #print text
      hs.append( "%s <small>(%s:%s,%s-%s)</small>" % (' '.join(text),
        ment['sentence'], ment['head'], ment['start'], ment['end'],
        ))
    print ' | '.join(hs)
    print """</div>"""
  #print "<pre>"
  #print json.dumps(doc, indent=4)
  #print "</pre>"
