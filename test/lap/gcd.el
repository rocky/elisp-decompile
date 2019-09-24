(defun my-gcd(a b)
  "Greatest Common Divisor of A and B"
  ;; Make a <= b
  (if (> a b)
      (let ((c a))
	(setq a b)
	(setq b c)))
  (cond
   ((< a 0) nil)
   ((or (= 0 (- b a)) (= a 1)) a)
   (t (my-gcd (- b a) a))
   )
)
