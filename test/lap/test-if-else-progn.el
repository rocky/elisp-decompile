(defun test-if-else-progn(&optional e)
  (if e
      (progn
	(setq a 1)
	(setq b 2))
    (setq a 2)))
