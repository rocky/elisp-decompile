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

# Using this code

Perhaps (with help, possibly yours) this will all get converted to
Emacs Lisp. But for now it's Python since the decompiler code I have
is currently in that language.

## Set up Python project

The below is GNU/Linux centric. Adjust to your OS.

This is a pretty standard Python project so install however you'd do that from source.


```
$ pip install -e .
```

## Get a LAP file

You need to run code in the `elisp/dedis.el` to produce disassembly
that you'd write to a file that ends in `.lap`.  We have a number of
sample LAP files in `testdata` in case you want to try a canned example.

The specfic functions in `dedis.el` are `disassemble-file` and `disassemble-full`.

So inside Emacs find a function you want to disassemble and run `M-x disassemble-full`

This is pretty much like `disassemble`, but we don't truncate the
output of docstrings or other things that `disassemble` generally does.

## Disassemble LAP file

After you have a LAP file and have set up the Python code, you can try to disassemble:

```
$ python eldecompile/main.py <name-of-lap-file>
```

There is perhaps a *lot* of debug output. There is even some flow
control that isn't really used at the moment. You can probably go into
the Python and comment this stuff out.

Also, what we can decompile right now is a bit limited. I see no
technical difficulties other than lots of work. So please help out.

# Is it worth it?

Interestingly, a number of people have proffered the suggestion that
it might just be easier to understand LAP and disassemble than write this code.

Most people don't know LAP. From working with it so far and from
seeing what the decompiler has to do, I am pretty convinced that those
who say they understand it still would have to do a lot of tedious
work to decipher things.

And all of this takes a lot of time and is tedious. This is what
computers were invented for. They do this stuff very fast compared to a human.

Here are some simple examples:

## Macros are expanded

I would find it tedious enough just to descramble something that has
been macro expanded. And I am sure people may find that unsatisfying
right now with our results. Now imagine how you'd feel to add another
layer on that in going from LAP to Elisp for the expanded macros.

The LAP instructions for:

```
(define-minor-mode testing-minor-mode "Testing")
```

expand to 60 or so LAP instructions; a lot more when various parameters
have been filled in.

Or consider `with-temp-buffer`:

```
(macroexpand '(with-temp-buffer 5))
```

This expands to:

```
(let ((temp-buffer (generate-new-buffer " *temp*")))
   (with-current-buffer temp-buffer (unwind-protect (progn 5)
   (and ... ...))))
```

The elision is not mine, but what you get back from macroexpand.

It is non-trivial to reconstruct this. And then you have things like
`dolist` which are just long and boring template kinds of
things. Because it's long it is very easy to loose site of what it is.

## Stacked values

Keeping track of values pushed on a stack is also tedious. Again there
can be some non-locality in when a value is pushed with when it is used and popped.

## Keyboard bindings

Yet another piece of tedium for the few that know how to do.
