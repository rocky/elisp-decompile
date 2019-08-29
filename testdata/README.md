Here we have various LAP test cases.

Things that need to be worked on are in todo.

testit.sh is a simple shell script to run everything.

In a buffer, create a test case function, e.g. `test-foo()`. Name the file associated with the buffer to be a file in this directory ending in `.el`, e.g. `foo.el`.

Evaluate the function and run `M-x disassemble` on that function. Copy the disassembled results to a `.lap`, e.g. `foo.lap`.
