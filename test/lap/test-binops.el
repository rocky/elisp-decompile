(defun binops(e)

  (foo a b c)
  (bar a b)
  (require 'ert) ; temporary hack
  (package-initialize)

  ;; ;; A protection against trojan horses
  ;; (setq inhibit-local-variables t)

  ;; ;; Find about errors in this file. debug-on-error is to set this to nil
  ;; ;; at the end of this file so that only error in this file are caught.
  ;; (setq debug-on-error 't)

  ;; ;; (defvar font-loaded nil)
  (setq a 1)
  (setq b 'foo)
  (setq c "bar")
  (setq e1 (- e 2))
  (setq f (>= e 2))
  (setq g (> e 2))
  (setq h (< e 2))
  (setq i (<= e 2))
  (setq j (% e 2))
  (setq k (= e 2))
  (setq l (+ e 2))
  (setq m (/ e 2))
  (setq n (* e 2))
  )
