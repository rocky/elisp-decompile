A decompiler for Emacs Lisp bytecode... or at least a proof of concept.

This code uses the [Python spark-parser](https://pypi.python.org/pypi/spark_parser/) for its Earley algorithm parser and the code.

This is in a very early stage. Until docs are better organized, see
[Writing Semantic-action
Rules](https://github.com/rocky/python-spark/wiki/Writing-Semantic-action-rules)
and the
https://github.com/rocky/python-uncompyle6/wiki/Deparsing-Paper for a
more general overview.

Also see [the section on Elisp
Disassembly](https://www.gnu.org/software/emacs/manual/html_node/elisp/Disassembly.html)
has some info on Emacs lisp disassembly. Until this is rewritten into
Emacs Lisp, this project uses that output as its starting point.
