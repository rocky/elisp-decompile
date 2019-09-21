(defun test-string-fns(s)
  (elt '(1560 1561 1562) (length s))
  (string= s "one two three")
  (substring s 0 2))
