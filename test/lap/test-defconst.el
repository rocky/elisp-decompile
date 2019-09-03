(defun test-defconst(font-info)
  (when (font-info "DejaVu Sans Mono-10")
    (set-frame-font "DejaVu Sans Mono-10")
    (defconst fixed-font "DejaVu Sans Mono-11"
      "Font to use as the fixed font")
    (defconst variable-font "DejaVu Sans 10"
      "Font to use as the proportional-space font")))
