(defun ipython-eval (code)
  (let* ((current-module (get-current-python-module))
         (url (concat "http://localhost:5005/eval?in-module="
                      current-module) )
         (url-request-method "POST")
         (url-request-data
           (encode-coding-string code 'utf-8))
         (url-request-extra-headers '(("Content-Type" . "plain/text"))))
    (with-current-buffer (url-retrieve-synchronously url t t 5)
      (goto-char (point-min))
      (search-forward-regexp "^$")
      (next-line)
      (prog1
        (string-trim (buffer-substring-no-properties (point) (point-max)))
        (kill-buffer)))))


(defun ipython-switch-to (module)
  (let ((url "http://localhost:5005/switch")
        (url-request-method "POST")
        (url-request-data module)
        (url-request-extra-headers '(("Content-Type" . "plain/text"))))
    (with-current-buffer (url-retrieve-synchronously url)
      (prog1 (buffer-string)
        (kill-buffer)))))


(defun ipython-send-region (start end &optional send-main)
  "Send the region delimited by START and END to inferior Python process.
When optional argument SEND-MAIN is non-nil, allow execution of
code inside blocks delimited by \"if __name__== \\='__main__\\=':\".
When called interactively SEND-MAIN defaults to nil, unless it's
called with prefix argument.  When optional argument MSG is
non-nil, forces display of a user-friendly message if there's no
process running; defaults to t when called interactively."
  (interactive
   (list (region-beginning) (region-end) current-prefix-arg t))
  (let* ((string (python-shell-buffer-substring start end (not send-main)))
         (result (ipython-eval string)))
    (if (string= result "OK")
        (message "Success")
      (error "%s" result))))


(defun get-beginning-of-defun ()
  (end-of-line 1)
  ;; Searching beginnging of the class or function
  (while (and (or (python-nav-beginning-of-defun)
                  (beginning-of-line 1))
              (> (current-indentation) 0)))
  ;; Process decorators
  (while (and (forward-line -1)
              (looking-at "@")))
  (forward-line 1)
  (point-marker))


(defun get-end-of-defun ()
  ;; Go down from decorators
  (while (and (looking-at "@")
              (forward-line 1)))
  
  (or (python-nav-end-of-defun)
      (end-of-line 1))
  (point-marker))


(defun ipython-send-defun (&optional arg msg)
  "Send the current defun to inferior Python process.
When argument ARG is non-nil do not include decorators.  When
optional argument MSG is non-nil, forces display of a
user-friendly message if there's no process running; defaults to
t when called interactively."
  (interactive (list current-prefix-arg t))
  (save-excursion
    (ipython-send-region
     (get-beginning-of-defun)
     (get-end-of-defun)
     nil ;; noop
     )))


(define-key python-mode-map "\C-c\C-c" 'ipython-send-defun)


(defun get-current-python-module ()
  "Returns a string with the full name of the python module for the current file."
  (let* ((start-from buffer-file-name)
         ;; A filename without extension and path
         (current-component (file-name-base start-from))
         ;; A directory name where current component is
         (current-dir (file-name-directory start-from))
         ;; Here we'll collect our python modules
         (components (unless (equal current-component
                                    "__init__")
                       (list current-component))))
    (flet ((is-module (directory)
             (file-exists-p
              (concat directory
                      "__init__.py"))))
      (while (is-module current-dir)
        (let ((dir-as-file (directory-file-name current-dir)))
          (setf current-component
                (file-name-base dir-as-file))
          (setf current-dir
                (file-name-directory dir-as-file))
          (push current-component
                components)))
      (string-join
       components
       "."))))


(defun ipython-switch-to-current-module ()
  "Switches ipython to the module corresponding to the current file."
  (interactive)
  (let ((module (get-current-python-module)))
    (unless module
      (error "Seems you are not in the buffer with a python module."))
    (ipython-switch-to module)))


(define-key python-mode-map (kbd "C-c v") 'ipython-switch-to-current-module)
