;;; dedis.el modified for bytecode disassembly from:
;;; disass.el --- disassembler for compiled Emacs Lisp code  -*- lexical-binding:t -*-

;; Copyright (C) 1986, 1991, 2002-2017 Free Software Foundation, Inc.

;; Author: Doug Cutting <doug@csli.stanford.edu>
;;	Jamie Zawinski <jwz@lucid.com>
;; Maintainer: emacs-devel@gnu.org
;; Keywords: internal

;; This file is not part of GNU Emacs.
;; Here we just have extensions for disass.el

;; GNU Emacs is free software: you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.

;; GNU Emacs is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with GNU Emacs.  If not, see <http://www.gnu.org/licenses/>.

;;; Commentary:

;; The single entry point, `disassemble', disassembles a code object generated
;; by the Emacs Lisp byte-compiler.  This doesn't invert the compilation
;; operation, not by a long shot, but it's useful for debugging.

;;
;; Original version by Doug Cutting (doug@csli.stanford.edu)
;; Substantially modified by Jamie Zawinski <jwz@lucid.com> for
;; the new lapcode-based byte compiler.

;;; Code:

(require 'macroexp)
(require 'disass)
(require 'files)

;;;###autoload
(defun disassemble-file (filename)
  "Disassemble an Emacs bytecode file"
  ;; Thanks to wasamasa on stackoverflow.
  (interactive
   (list (car (find-file-read-args "Find file: "
                        (confirm-nonexistent-file-or-buffer)))))

  (let ((buffer (find-file-noselect filename nil t nil)))
    (if (string-match "\\.elc$" filename)
	(progn
	  (disassemble-full (read buffer))
	  (kill-buffer buffer))
      ;; else
      (error "file name should end in .elc"))))


;;;###autoload
(defun disassemble-full (object &optional buffer indent interactive-p)
  "Print disassembled code for OBJECT in (optional) BUFFER.
OBJECT can be a symbol defined as a function, or a function itself
\(a lambda expression or a compiled-function object).
If OBJECT is not already compiled, we compile it, but do not
redefine OBJECT if it is a symbol."
  (interactive
   (let* ((fn (function-called-at-point))
          (prompt (if fn (format "Disassemble function (default %s): " fn)
                    "Disassemble function: "))
          (def (and fn (symbol-name fn))))
     (list (intern (completing-read prompt obarray 'fboundp t nil nil def))
           nil 0 t)))
  (if (and (consp object) (not (functionp object)))
      (setq object `(lambda () ,object)))
  (or indent (setq indent 0))		;Default indent to zero
  (save-excursion
    (if (or interactive-p (null buffer))
	(with-output-to-temp-buffer "*Disassemble*"
	  (set-buffer "*Disassemble*")
	  (disassemble-internal-full object indent (not interactive-p)))
      (set-buffer buffer)
      (disassemble-internal-full object indent nil)))
  nil)


(defun disassemble-internal-full (obj indent interactive-p)
  (let ((macro 'nil)
	;; (constants-vector [])
	(name (when (symbolp obj)
                (prog1 obj
                  (setq obj (indirect-function obj)))))
	args)
    (setq obj (autoload-do-load obj name))
    (if (subrp obj)
	(error "Can't disassemble #<subr %s>" name))
    (if (eq (car-safe obj) 'macro)	;Handle macros.
	(setq macro t
	      obj (cdr obj)))
    (if (eq (car-safe obj) 'byte-code)
	(setq obj `(lambda () ,obj)))
    (when (consp obj)
      (unless (functionp obj) (error "not a function"))
      (if (assq 'byte-code obj)
          nil
        (if interactive-p (message (if name
                                       "Compiling %s's definition..."
                                     "Compiling definition...")
                                   name))
        (setq obj (byte-compile obj))
        (if interactive-p (message "Done compiling.  Disassembling..."))))
    ;; (setq constants-vector (aref obj 2))
    (cond ((consp obj)
	   (setq args (help-function-arglist obj))	;save arg list
	   (setq obj (cdr obj))		;throw lambda away
	   (setq obj (cdr obj)))
	  ((byte-code-function-p obj)
	   (setq args (help-function-arglist obj)))
          (t (error "Compilation failed")))
    (if (zerop indent) ; not a nested function
	(progn
	  (indent-to indent)
	  (insert (format "byte code%s%s%s:\n"
			  (if (or macro name) " for" "")
			  (if macro " macro" "")
			  (if name (format " %s" name) "")))))
    (let ((doc (if (consp obj)
		   (and (stringp (car obj)) (car obj))
		 ;; Use documentation to get lazy-loaded doc string
		 (documentation obj t))))
      (if (and doc (stringp doc))
	  (progn (and (consp obj) (setq obj (cdr obj)))
		 (indent-to indent)
		 ;; (princ (format "  constants-vector: %s\n" constants-vector))
		 (princ (format "  doc-start %d:  " (length doc)) (current-buffer))
		 (insert doc "\n"))))
    (indent-to indent)
    (insert "  args: ")
    (prin1 args (current-buffer))
    (insert "\n")
    (let ((interactive (interactive-form obj)))
      (if interactive
	  (progn
	    (setq interactive (nth 1 interactive))
	    (if (eq (car-safe (car-safe obj)) 'interactive)
		(setq obj (cdr obj)))
	    (indent-to indent)
	    (insert "  interactive: ")
	    (if (eq (car-safe interactive) 'byte-code)
		(progn
		  (insert "\n")
		  (disassemble-1 interactive
				 (+ indent disassemble-recursive-indent)))
	      (let ((print-escape-newlines t))
		(prin1 interactive (current-buffer))))
	    (insert "\n"))))
    (cond ((and (consp obj) (assq 'byte-code obj))
	   (disassemble-1 (assq 'byte-code obj) indent))
	  ((byte-code-function-p obj)
	   (disassemble-1 obj indent))
	  (t
	   (insert "Uncompiled body:  ")
	   (let ((print-escape-newlines t))
	     (prin1 (macroexp-progn obj)
		    (current-buffer))))))
  (if interactive-p
      (message "")))


(provide 'dedis)

;;; dedis.el ends here
