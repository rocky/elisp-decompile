A [decompiler](https://en.wikipedia.org/wiki/Decompiler) for Emacs Lisp bytecode... or at least a proof of concept.

This code uses the [Python
spark-parser](https://pypi.python.org/pypi/spark_parser/) for its Earley algorithm parser and the code organization.  I have a project that implements the [Earley algorithm in Emacs
Lisp](https://github.com/rocky/elisp-earley). It needs _a lot_ more work though to replace the Python code.

This is in a very early stage, but amazingly the code seems sound so far.
A list of the kinds of things we can decompiler are in the [test/lap](https://github.com/rocky/elisp-decompile/tree/master/test/lap) directory. Two of the longer examples are:

* [test-nested-when.el](https://github.com/rocky/elisp-decompile/blob/master/test/lap/test-when-nested.el) which demonstrates detecting forms like `defvar`, and `defconst`, as well as inverting macros like `when` and
* [my-gcd.el](https://github.com/rocky/elisp-decompile/blob/master/test/lap/gcd.el) which is a recursive gcd program that really works.

Until docs are better organized, see
[Writing Semantic-action Rules](https://github.com/rocky/python-spark/wiki/Writing-Semantic-action-rules)
and the
https://github.com/rocky/python-uncompyle6/wiki/Deparsing-Paper for a
more general overview.

I gave a
[talk on Emacs bytecode showing this code](http://rocky.github.io/NYC-Emacs-April-2018). Type
"s" on a slide to see the text associated with the slide.

We are currently working on documenting Elisp bytecode. See https://github.com/rocky/elisp-bytecode .

You may find yourself consulting the source code: [`emacs/lisp/emacs-lisp/bytecomp.el`](http://git.savannah.gnu.org/cgit/emacs.git/tree/lisp/emacs-lisp/bytecomp.el),
[`emacs/src/data.c`](http://git.savannah.gnu.org/cgit/emacs.git/tree/src/data.c) and [`emacs/src/bytecode.c`](http://git.savannah.gnu.org/cgit/emacs.git/tree/src/bytecode.c).

# Using this code

Perhaps (with help, possibly yours) this will all get converted to Emacs Lisp. But for now it's Python since the decompiler code I have is currently in that language.

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

The specific functions in `dedis.el` are `disassemble-file` and `disassemble-full`.

So inside Emacs find a function you want to disassemble and run `M-x disassemble-full`.
Or find a bytecode file you want and run or `M-x disassembe-file`

The first is like `disassemble`, but we don't truncate the
output of docstrings or other things that `disassemble` generally does. The second is
like `disassemble-full` but we start out with a bytecode file instead of a lisp function.

## Disassemble LAP file

After you have written the results of the last section to LAP file,
the file should end in `.lap`, and have set up the Python code, you
can try to disassemble:

```
$ lapdecompile <name-of-lap-file> [options]
```

There is perhaps a *lot* of debug output. There is even some flow
control that isn't really used at the moment. You can probably go into
the Python and comment this stuff out.

Also, what we can decompile right now is a bit limited. I see no
technical difficulties other than lots of work. So please help out.

# But is it worth it?

### It's GNU Emacs, so of course I have the source code!

There is a difference between being able to find the source code and having it accessible when you need it, such as at runtime in a stack trace.

When many people hear the word "decompile" they think reverse engineering or hacking code where source has deliberately been withheld. But are other situations where a decompiler is useful.

A common case is where you wrote the code, but have accidentally deleted the source code and just have the bytecode file.

But, I know, you always use version control and emacs provides it's tilde backup file.

So that leads us to the situation where there are _several_ possible source-code versions around, e.g. a development version and a stable version, or one of the various versions that correspond to version in your version-control system, and you'd like to know which one of those corresponds to the bytecode that is stored in a bytecode file, or that you have loaded.


And then we come to situation where there _is_ no source-code file. One can create functions on the fly and change them on the fly. Similarly, functions can create functions when run
interactively. Perhaps you'd like to reconstruct the source code for a function that you worked on interactively.

### Isn't it simpler to just disassemble?

Interestingly, a number of people have proffered the suggestion that it might just be easier to understand LAP and disassemble than write this code.

Most people don't know LAP. In fact, before I started writing the [Elisp bytecode reference](https://github.com/rocky/elisp-bytecode), there really _wasn't_ any good documentation on LAP, short of reading source code.

From writing this decompiler and noting all of the subtleties and intricacies, I am pretty convinced that those who say they understand LAP have to do *a lot* of time-consuming tedious work to decipher things.

This is what computers were invented for. They do this stuff very fast compared to humans.

Here are some simple examples:

#### Macros are expanded

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

And then you have things like `dolist` which are just long and boring template kinds of things. Because it's long it is very easy to lose sight of what it is.

#### Stacked values

Keeping track of values pushed on a stack is also tedious. Again, there can be some non-locality in when a value is pushed with when it is used and popped. As an example, consider this LAP code which is similar to a well-known mathematical function:

```
        constant  fn
        dup
        varref    n
        sub1
        call      1
        constant  fn
        varref    n
        constant  2
        diff
        call      1
        plus
        call      1
```


At what point is that duplicated function the second instruction used? And what are the arguments to this function?

How long did it take you to figure this out? It takes a computer hundredths of a second to reconstruct the Lisp code.

#### Keyboard bindings

Yet another piece of tedium for the few that know how to do.

See how fast you can come up with the key names for:

```
[134217761]
[134217854]
[134217820]
```

Again this is done in hundredths of a second by a computer.
