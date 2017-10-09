(defun test-dolist()
  (dolist
      (i '(1 2 3))
    (princ i)))

(defun test-dolist-result(a)
  (dolist
      (i '(1 2 3) (+ a 10))
    (princ i)))
