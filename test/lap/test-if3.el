(defun test-if-else3(string &optional multiple)
  "Another if and if/else test"
  (if (> (length string) 0)
      (if (string= "\n" string)
	    "foo"))
  (if (> (length string) 0)
      (let ((s string))
	(if (string= "\n" string)
	    "foo"
	  string))))
