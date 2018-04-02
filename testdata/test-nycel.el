(defun test-nyc ()
  "Visit the source code corresponding to the `next-error' message at point."
  (setq next-error-last-buffer (current-buffer))
  ;; we know here that next-error-function is a valid symbol we can funcall
  (with-current-buffer next-error-last-buffer
    (funcall next-error-function 0 nil)
    (when next-error-recenter
      (recenter next-error-recenter))
    (run-hooks 'next-error-hook)))
