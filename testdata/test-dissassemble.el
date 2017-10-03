(defun disassemble (object &optional buffer indent interactive-p)
  "Print disassembled code for OBJECT in (optional) BUFFER.
OBJECT can be a symbol defined as a function, or a function itself
\(a lambda expression or a compiled-function object).
If OBJECT is not already compiled, we compile it, but do not
redefine OBJECT if it is a symbol."
  (interactive
   (let* ((fn (function-called-at-point))
          (prompt (if fn (format "Disassemble function (default %s): " fn)
                    "Disassemble function: "))
          (def (and fn (symbol-name fn))))
     (list (intern (completing-read prompt obarray 'fboundp t nil nil def))
           nil 0 t)))
  (if (and (consp object) (not (functionp object)))
      (setq object `(lambda () ,object)))
  (or indent (setq indent 0))		;Default indent to zero
  (save-excursion
    (if (or interactive-p (null buffer))
	(with-output-to-temp-buffer "*Disassemble*"
	  (set-buffer "*Disassemble*")
	  (disassemble-internal object indent (not interactive-p)))
      (set-buffer buffer)
      (disassemble-internal object indent nil)))
  nil)
