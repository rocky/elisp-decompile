(defun test-add-minor-mode()
  (add-minor-mode 'foo 'nil
		  (if (boundp 'foo-map)
		      foo-map)
		  nil nil))
