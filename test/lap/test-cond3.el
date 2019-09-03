(defun test-cond3(a b c)
  (cond
        (a 2)
        (b 4)
        (t (and (not c) a))))
