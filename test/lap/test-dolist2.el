(defun test-dolist2 (a b)
  (let ((a (or (pop args) 0)))
    (dolist (b args)
      (setq b (% a (setq a b))))))
