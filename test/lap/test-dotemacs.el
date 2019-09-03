(defun test-dotemacs()
  ;;
  (global-set-key "\C-h" 'backward-delete-char-untabify)
  (global-set-key "\C-u" 'advertised-undo)
  (global-set-key "\C-d" 'delete-char)
  (global-set-key "\C-xm" 'vm-mail)

  (global-set-key (kbd "C-s") 'isearch-forward-regexp)
  (global-set-key (kbd "C-r") 'isearch-backward-regexp)
  (global-set-key (kbd "C-M-s") 'isearch-forward)
  (global-set-key (kbd "C-M-r") 'isearch-backward)

  ;; The tool bar really duplicates the menu bar. And I don't even use
  ;; the menu bar all that much. However the tool/menu bar suggests new things
  ;; to try occasionally and specific to mode, I suppose one of them I should
  ;; keep around
  (tool-bar-mode 'nil)

  (auto-compression-mode)

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
    ))


(defun test-dotemacs2()
  (dolist
      (pair '(
	      (calendar-latitude +40.7)
	      ))
    (set
     (car pair)
     (cdr pair))))

(defun test-dotemacs2a()
  (dolist
      (pair '(
	      (calendar-latitude +40.7)
	      ))
    (set
     (vectorp pair)
     (cdr pair))))


(defun test-dotemacs3(foo)
  (put 'set-goal-column 'disabled nil)
  ;; Set various variables variously
  (set (car foo) (cadr pair)))
