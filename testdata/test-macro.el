(defmacro test-macro-list3 (x)
  (list 'setq 'a x))

(defmacro test-macro-list2 (x)
  (list '1+ x))
