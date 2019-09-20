(defun test-dotemacs2()
  (dolist
      (dir
       (list (expand-file-name "~/elisp")
	     (expand-file-name "~/.emacs.d/lisp")
	     "/usr/local/share/emacs/site-lisp"
	     "/usr/share/emacs/site-lisp/git"
	     ))
    (if (file-directory-p (expand-file-name dir))
	(add-to-list 'load-path (expand-file-name dir))
      )
    )
  (put 'set-goal-column 'disabled nil))
