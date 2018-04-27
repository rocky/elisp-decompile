(defun test-or3 (object buffer)
  "Print disassembled code for OBJECT in (optional) BUFFER.
BLAH BLAH BLAH"
  (save-excursion
    (if (or interactive-p (null buffer))
	(save-current-buffer
	  (set-buffer "*Disassemble*")
	  (insert "foo")))))
