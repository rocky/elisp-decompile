(defun test-with-current-buffer(srcbuf)
  "Test with-current-buffer and with-current-buffer-safe-macros"
  (with-current-buffer srcbuf
    (realgud-cmdbuf-info-in-debugger?= nil)
    (realgud-cmdbuf-info-bp-list= '())
    )
  (with-current-buffer-safe srcbuf
    (setq x 1)
  ))
