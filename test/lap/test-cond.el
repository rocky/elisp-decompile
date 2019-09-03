(defun test-cond(mode)
  (setq b (cond ((eq mode 'eshell) 5)
		  ((eq mode 'comint) 6)
		  ((eq mode 'foo) 10))))
