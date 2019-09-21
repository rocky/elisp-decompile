(defun test-when-nested()
  "Excerpted from my .emacs file"
  (require 'ert)
  (setq inhibit-local-variables t)

  (setq debug-on-error t)

  (defvar font-loaded nil)
  (when (and window-system (not font-loaded))
    (tool-bar-mode nil)
    (when (font-info "DejaVu Sans Mono-10")
      (set-frame-font "DejaVu Sans Mono-10")
      (defconst fixed-font "DejaVu Sans Mono-11"
	"Font to use as the fixed font")
      (defconst variable-font "DejaVu Sans 10"
	"Font to use as the proportional-space font")
      )
    (set-fontset-font (frame-parameter nil 'font)
		      'han '("cwTeXHeiBold" . "unicode-bmp"))
    (setq font-loaded t)))
