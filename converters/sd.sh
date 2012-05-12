#!/bin/zsh
$(dirname $0)/collapse.py |
java -cp ~/sw/stanfordnlp/stanford-parser-2008-10-26 -ea Depper /dev/stdin
