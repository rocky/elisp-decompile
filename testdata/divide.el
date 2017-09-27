(defun divide-boom(a b c)
  "A canonical example where decompilation is desireable.
Is it the first divide or second that causes an error?"
  (/ a (/ b c)))
