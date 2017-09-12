(defun foo(e)

  (require 'ert) ; temporary hack

  ;; A protection against trojan horses
  (setq inhibit-local-variables t)

  ;; Find about errors in this file. debug-on-error is to set this to nil
  ;; at the end of this file so that only error in this file are caught.
  (setq debug-on-error 't)

  ;; (defvar font-loaded nil)
  (setq a 1)
  (setq b 'foo)
  (setq c "bar")
  (setq d (+ e 2)))
