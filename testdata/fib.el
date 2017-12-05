(defun fib(n)
  (cond ((< n 1) 1)
	(t (+ (fib (1- n)) (fib (- n 2))))))
