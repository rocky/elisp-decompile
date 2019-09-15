(defun test-with-temp-buffer()
  (with-temp-buffer
    (insert-file-contents file)
    (intern (file-name-base file)) sub-pkgs))
