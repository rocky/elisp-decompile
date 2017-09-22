(defun test-cond(mode)
  (progn
    (setq b (cond ((eq mode 'eshell) (not mode) 5)
		  ((eq mode 'comint) 5)
		  (t 10)))))

(defun test-cond2(mode)
  (cond ((eq mode 'eshell) 1)
	((eq mode 'comint) 2)
	(t 13)))
