(defun test-or1 (object buffer)
  "Print disassembled code for OBJECT in (optional) BUFFER.
BLAH BLAH BLAH"
  (if (or interactive-p (null buffer))
      (insert "foo")))
