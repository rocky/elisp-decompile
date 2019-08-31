(defun test-dotemacs6()

  (when (fboundp 'global-font-lock-mode)
    (global-font-lock-mode t))


  ;; (when window-system
  ;;   (setq visible-bell 't)
  ;;   (if (eq window-system 'x)
  ;; 	(progn
  ;; 	  (setq x-select-enable-clipboard t)
  ;; 	  (setq interprogram-paste-function
  ;; 		'x-cut-buffer-or-selection-value)
  ;; 	  )
  ;;     ;; else Windows N/T windows
  ;;     (add-to-list 'load-path "e:/cygwin/usr/share/emacs/site-lisp")
  ;;     ))

  ;; now that Ctrl h is no longer help, redefine help.
  (define-key esc-map "h" 'help-for-help)
  (define-key esc-map "g" 'goto-line)

  (setq Info-directory-list
	(list "/usr/local/lib/info/" "/usr/local/info/" "/usr/share/info/"
	      (expand-file-name "~/info")))
  )
