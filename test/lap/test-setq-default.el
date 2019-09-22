;; At some point we may add macro detection of setq-default
(defun test-setq-default()
  (setq-default
   cygwin-root (getenv "CYGWIN_ROOT")
   exec-path (cons (concat cygwin-root "/bin") exec-path)
   process-coding-system-alist '(("bash" . undecided-unix))
   shell-file-name "bash"
   explicit-shell-file-name shell-file-name
   ))
