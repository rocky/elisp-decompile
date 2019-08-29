;; setq uses DUP leaving an extra stack entry after the SETQ
;; Also we test stacking-while which reuses the top stack entry.
(defun setq-stacking2 (a b)
  (setq b (% a (setq a b))))
