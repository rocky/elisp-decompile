(defun test-while2(string)
  "Remove trailing \n if it's there"
  (while (and (> (length string) 0)
	      (eq (elt string (- (length string) 1)) ?\n))
    (setq string (substring string 0 -1))))
