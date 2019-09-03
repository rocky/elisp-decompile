#!/usr/bin/env python
import os
import os.path as osp
import tempfile
from lapdecompile.main import deparse
lapdir = osp.join(osp.dirname(os.path.realpath(__file__)), "lap")
os.chdir(lapdir)
succeeded = 0
invalid_source = 0
invalid_parse = 0
tot_files = 0
target_base = tempfile.mkdtemp(prefix='lap-dis-')
for filename in os.listdir("."):
    if filename.endswith(".lap"):
        target_file = os.path.join(target_base, f"{filename[:-4]}.el")
        with open(target_file, "w") as fp:
            rc = deparse(filename, fp, False, False, False, False)
            if rc == 0:
                fp.close()
                exit_rc = os.system(f"emacs --no-init-file --batch --load={target_file}")
                if exit_rc != 0:
                    invalid_source += 1
                else:
                    succeeded += 1
                pass
            else:
                invalid_parse += 1
            tot_files += 1
        pass
    pass
print(f"{succeeded} succeded, {invalid_parse} decompile errors; {invalid_source} produced incorrect Emacs Lisp; {tot_files} total.")
