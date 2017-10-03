(defun test-save-buffer ()
  (save-current-buffer
    (insert "foo")))

(defun test-set-buffer ()
  (set-buffer "foo"))
