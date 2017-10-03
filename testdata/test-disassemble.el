(defun test-disassemble (object buffer)
  "Print disassembled code for OBJECT in (optional) BUFFER.
BLAH BLAH BLAH"
  (if (and (consp object) (not (functionp object)))
      (setq object `(lambda () ,object)))
  (or indent (setq indent 0))		;Default indent to zero
  (save-excursion
    (if (or interactive-p (null buffer))
	(save-current-buffer
	  (set-buffer "*Disassemble*")
	  (insert "foo")))))
