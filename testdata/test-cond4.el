(defun test-cond4(mode)
  (cond
        ((eq mode 'eshell) 1)
        (t (and (eq mode 'comint) 2))))
