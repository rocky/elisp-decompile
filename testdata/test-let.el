(defun test-let1()
  (let ((a 2))
    (setq b (1+ a))))

(defun test-let()
  (let ((a 2)
	(b 3))
    (setq b (+ a b))))

(defun test-let1()
  (let ((a 2))
    (setq b (+1 a))))

(defun test-let-mixed()
  (let ((a)
	(b 3)
	(c))
    (setq c (+ a b))))
