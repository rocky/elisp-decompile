(defun test-dotemacs5()
  (dolist
      (pair '(
	      (calendar-latitude +40.7)
	      ))
    (set (car pair) (cadr pair))))
