[![Downloads](https://pepy.tech/badge/lapdecompile)](https://pepy.tech/project/lapdecompile)

A [decompiler](https://en.wikipedia.org/wiki/Decompiler) for Emacs Lisp bytecode... or at least a proof of concept.

This code uses the [Python
spark-parser](https://pypi.python.org/pypi/spark_parser/) for its Earley algorithm parser and the code organization.  I have a project that implements the [Earley algorithm in Emacs
Lisp](https://github.com/rocky/elisp-earley). It needs _a lot_ more work though to replace the Python code.

This is in a very early stage, but with some hand-waving, the code seems like it could cover everything.

A list of the kinds of things we can decompiler are in the [test/lap](https://github.com/rocky/elisp-decompile/tree/master/test/lap) directory. Two of the longer examples are:

* [test-nested-when.el](https://github.com/rocky/elisp-decompile/blob/master/test/lap/test-when-nested.el) which demonstrates detecting forms like `defvar`, and `defconst`, as well as inverting macros like `when` and
* [my-gcd.el](https://github.com/rocky/elisp-decompile/blob/master/test/lap/fib.el) which is a recursive fib program that really works.

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

# Bugs

You should think of this like you would, say, google translate to convert between two human languages: sometimes what you get back is perfect, sometimes what you get back is a little stilted but you still get the idea. And sometimes what you get back is just wrong.

Here, the wrong cases generally involve getting control flow correct. We have the underlying high-powered control-flow code to get control-flow graphs and compute dominators and reverse dominators. However we are not making use of this information right now. And doing so requires a lot of serious thought, engineering, and experimentation.

# Using this code

Perhaps (with help, possibly yours) this will all get converted to Emacs Lisp. But for now it's Python since the decompiler code I have is currently in that language.

The simplest way to install if via Python's `pip` command:

```
pip install lapdecompile
```

This installs the last stable release, but right now what is in github is generally more complete.


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

So inside Emacs find a function you want to disassemble and run `M-x disassemble-full`. Or find a bytecode file you want and run or `M-x disassembe-file`

The first is like `disassemble`, but we don't truncate the output of docstrings or other things that `disassemble` generally does. The second is like `disassemble-full` but we start out with a bytecode file instead of a lisp function.

## Disassemble LAP file

After you have written the results of the last section to LAP file, the file should end in `.lap`, and have set up the Python code, you can try to disassemble:

```
$ lapdecompile <name-of-lap-file> [options]
```

There is perhaps a *lot* of debug output. There is even some flow control that isn't really used at the moment. You can probably go into the Python and comment this stuff out.

Also, what we can decompile right now is a bit limited. I see no technical difficulties other than lots of work. So please help out.

# But is it worth it?

A number of people have opined that you really don't need a decompiler.

__Aside:__

_Whenever something new or novel comes along, in addition to the group that says "Why not?!" there is the "Why bother?"" group.  In my lifetime, I have experienced this attitude when undo and regular expressions were added to GNU Emacs, adding a debugger to languages where debugging support didn't exist or was weak, using decomplation to give more precise error location information, and here. Convincing the crowd that is happy with the status quo is hard, and quite frankly this project isn't mature. The next section is more for those who have an open mind and want to see a better world._

Below are the arguments offered and why I think they are inadequate.


### It's GNU Emacs, so of course I have the source code!

There is a difference between being able to find the source code and having it accessible when you need it, such as at runtime in a stack trace.

When many people hear the word "decompile" they think reverse engineering or hacking code where source has deliberately been withheld. But are other situations where a decompiler is useful.

A common case is where you wrote the code, but have accidentally deleted the source code and just have the bytecode file.

But, I know, you always use version control and GNU Emacs provides it's tilde backup file.

So that leads us to the situation where there are _several_ possible source-code versions around, e.g. a development version and a stable version, or one of the various versions that in your version-control system, and you'd like to know which one of those corresponds to the bytecode that is stored in a bytecode file, or that you have loaded.


And then we come to situation where there _is_ no source-code file. One can create functions on the fly and change them on the fly.  Lisp is known for its culture in having programs create programs; it is possible such a program doesn't have a ``debug'' switch (that you know
about) to either save or show the result before it was byte-compiled.  Perhaps you'd like to reconstruct the source code for a function that you worked on interactively.

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
have been filled in. This decompiler has the ability to show both reconstructed show both before compressing into macros, should you want to see in high-level terms what is going on, and after.

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

#### Pedagogy

Another aspect about a decompiler, especially this one, is that it can help you learn LAP and Emacs bytecode, and how the existing compiler and optimizer work.

The program creates a parse tree from (abstracted) LAP instructions, where the the higher levels of the tree consist of grammar nodes that should be familiar in higher-level Emacs Lisp terms.

With this it is possible to see how the individual instructions combine to form the higher-level constructs.

Here is a decompilation using of the LAP instructions listed earlier

```
$ lap-decompile --tree=after tmp/foo.lap
fn_body (3)
  0. body
    exprs
      expr_stmt (2)
        0. expr
          call_exprn (3)
            0. expr
              name_expr
                    0 CONSTANT   fn
            1. expr
              binary_expr (3)
                0. expr
                  call_exprn (3)
                    0. expr
                          1 DUP
                    1. expr
                      unary_expr (2)
                        0. expr
                              2 VARREF     n
                        1. unary_op
                              3 SUB1
                    2.    4 CALL_1     1
                1. expr
                  call_exprn (3)
                    0. expr
                      name_expr
                            5 CONSTANT   fn
                    1. expr
                      binary_expr (3)
                        0. expr
                              6 VARREF     n
                        1. expr
                          name_expr
                                7 CONSTANT   2
                        2. binary_op
                              8 DIFF
                    2.    9 CALL_1     1
                2. binary_op
                     10 PLUS
            2.   11 CALL_1     1
        1. opt_discard
  1. opt_label
  2. opt_return
(defun foo(n)
  (fn (+ (fn (1- n)) (fn (- n 2)))))
```

Looking at the above we see that:

```
1 DUP
2 VARREF     n
3 SUB1
4 CALL_1     1
```

contains a function call and its parameters; One of the parameters is the unary expression:

```
2 VARREF     n
3 SUB1
```

And if you want to know which operation the stack value of first instruction `CONSTANT fn`
is used in, the nesting makes it easy to see it is the very last instruction `CALL_1`.

As I mentioned before, personally, I find matching this stuff up a bit tedious.
