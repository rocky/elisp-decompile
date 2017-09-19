A decompiler for Emacs Lisp bytecode... or at least a proof of concept.

This code uses the [Python spark-parser](https://pypi.python.org/pypi/spark_parser/) for its Earley algorithm parser and the code organization.

This is in a very early stage, but amazingly the code seems sound so
far.

Until docs are better organized, see
[Writing Semantic-action Rules](https://github.com/rocky/python-spark/wiki/Writing-Semantic-action-rules)
and the
https://github.com/rocky/python-uncompyle6/wiki/Deparsing-Paper for a
more general overview.

I gave a
[5-minute talk for a very general audience](http://rocky.github.io/NYC-Hackntell). Type
"s" on a slide to see the text associated with the slide. It has one
slide showing elisp bytecode and a deparse of that back to Emacs Lisp.


There isn't a lot on the details of Elisp bytecode, but see [the section on Elisp
Disassembly](https://www.gnu.org/software/emacs/manual/html_node/elisp/Disassembly.html).

You may find yourself consulting the source code: [`emacs/lisp/emacs-lisp/bytecomp.el`](http://git.savannah.gnu.org/cgit/emacs.git/tree/lisp/emacs-lisp/bytecomp.el),
[`emacs/src/data.c`](http://git.savannah.gnu.org/cgit/emacs.git/tree/src/data.c) and [`emacs/src/bytecode.c`](http://git.savannah.gnu.org/cgit/emacs.git/tree/src/bytecode.c).


Until this is rewritten into Emacs Lisp, this project uses the text
output from that as its input. (We lose the full text of docstrings in
the process).
