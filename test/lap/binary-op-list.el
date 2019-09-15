(defun test-binary-op-list(a b c d e l1 l2 l3)
  "Test that we handle and transform list-like binary ops"
  (+ (min b c d e) (max a b c) (max a b))
  (nconc l1 l2 l3))
