(defun control(&optional e)

  (if (<= e 4)
      (+ e 10))
  (if (> e 5)
      (+ e 3))
  (if (e)
      (progn
	(setq x 1)
	(setq y 2)
	(setq z 3)))
  (unless c
    (setq x 1)
    (setq y 2)))

(defun test-let-cond(c)
  (let ((a))
    (setq x 1))
  (let ((b 1))
    (setq x 1))
  (cond
   ((c (setq d 1))
    ('t 6))))
