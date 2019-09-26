(defun test-substring(string s)
  "Test string= and substring. We should transform to two-arg substring when possible"
  (if (string= "\n" (substring s -1))
      (substring s 0 -1)
      s))
