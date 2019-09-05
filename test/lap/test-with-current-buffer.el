(defun test-with-current-buffer(srcbuf)
  (with-current-buffer srcbuf
    (realgud-cmdbuf-info-in-debugger?= nil)
    (realgud-cmdbuf-info-bp-list= '())
  ))
