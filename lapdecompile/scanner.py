"""Scanner for ELISP decompiler

We take input from ELISP disassembly
"""
import re
from lapdecompile.tok import Token
from collections import namedtuple

Func = namedtuple(
    "Func", ["name", "args", "opt_args", "docstring", "interactive", "fn_type",
             "tokens", "customize"]
)


class LapScanner:
    def __init__(self, fp, show_assembly=False):
        self.last_compiled_function = 0
        self.lines = fp.readlines()
        self.line_count = len(self.lines)
        self.cur_index = 0
        self.show_assembly = show_assembly
        self.fp = fp
        self.fns = {}

        self.fn_scanner()

    def fn_scanner(self):
        anonymous_count = 0
        while self.cur_index < self.line_count:
            line = self.lines[self.cur_index]
            self.cur_index += 1
            fn_type = "defun"
            m = re.match("^byte code for macro (\S+):$", line)
            if m:
                fn_type = "defmacro"
                name = m.group(1)
            else:
                m = re.match("^byte code for (\S+):$", line)
                if m:
                    name = m.group(1)
                elif re.match("^byte code:$", line):
                    fn_type = "file"
                    name = f"anonymous{anonymous_count}"
                    anonymous_count += 1
                else:
                    name = "unknown"
                    pass
                pass

            self.name = name
            self.fn_scanner_internal(name, fn_type)
            pass
        return

    def fn_scanner_internal(self, name, fn_type):

        tokens = []
        customize = {}

        line = self.lines[self.cur_index]
        m = re.match("\s+doc:(.*)", line)
        if m:
            docstring = '\n"%s"\n' % m.group(1).rstrip("\n")
        elif re.match("\s+doc-start ", line):
            m = re.match("^\s+doc-start (\d+):  (.*)$", line)
            if m:
                tot_len = int(m.group(1))
                docstring = '\n  "' + m.group(2) + "\n"
                l = len(m.group(2))
                while l < tot_len - 1:
                    self.cur_index += 1
                    line = self.lines[self.cur_index]
                    l += len(line)
                    docstring += line
                    pass
                docstring = docstring.rstrip("\n")
                docstring += '"'
                pass
        else:
            docstring = ""
            self.cur_index -= 1

        self.cur_index += 1
        line = self.lines[self.cur_index]
        m = re.match("^\s+args: (\([^)]*\))", line)
        if m:
            args = m.group(1)
            self.cur_index += 1
        elif re.match("^\s+args: nil", line):
            args = "()"
            self.cur_index += 1
        else:
            args = "(?)"

        line = self.lines[self.cur_index]
        interactive = None
        m = re.match("^\s+interactive:\s+(.*)$", line)
        if m:
            interactive = m.group(1).rstrip("\n")
            self.cur_index += 1

        label = None
        while self.cur_index < self.line_count:
            line = self.lines[self.cur_index]
            if re.match("^byte code:", line):
                break
            elif line.startswith("#"):
                self.cur_index += 1
                continue
            fields = line.split()
            if len(fields) == 0:
                break
            joined_field = re.match(r"(\d+:\d+)(\D.+)", fields[0])
            if joined_field:
                fields[0] = joined_field.group(1)
                fields.insert(1, joined_field.group(2))
            offset = fields[0]
            colon_point = offset.find(":")
            if colon_point >= 0:
                label = offset[colon_point:]
                offset = offset[:colon_point]
                tokens.append(Token("LABEL", label, offset))
            offset, opname = fields[:2]
            if opname == "constant":
                attr = line[line.index("constant") + len("constant"):].strip()
                attr = attr.replace("\?", "?")
                if attr == "<compiled-function>":
                    fn_name = "compiled-function-%d" % self.last_compiled_function
                    self.last_compiled_function += 1
                    self.cur_index += 1
                    self.fn_scanner_internal(fn_name, fn_type="defun")
                    attr = self.fns[fn_name]
                tokens.append(Token("CONSTANT", attr, offset.strip(), label=label))
            elif opname[:-1] in ("list", "concat", "cal"):
                if opname.startswith("call"):
                    count = int(fields[2])
                    opname = "%s_%d" % (opname, count)
                elif opname[-1] == "N":
                    count = int(fields[2])
                    opname = "%s_%d" % (opname, count)
                else:
                    count = int(opname[-1])
                    opname = "%s_%d" % (opname[:-1], count)
                opname = opname.upper().strip()
                tokens.append(Token(opname, count, offset.strip(), label=label))
                customize[opname] = int(count)
            elif len(fields) == 3:
                offset, opname, attr = fields
                tokens.append(
                    Token(
                        opname.upper().strip(),
                        attr.strip(),
                        offset.strip(),
                        label=label,
                    )
                )
            elif len(fields) == 2:
                offset, opname = fields
                tokens.append(Token(opname.upper().strip(), None, offset.strip()))
                pass
            else:
                print("Can't handle line %d:\n\t%s" % (self.cur_index, line))
            label = None
            self.cur_index += 1
            pass

        if self.show_assembly:
            print(f"\n{name}{args}")
            print("\n".join([str(t) for t in tokens]))

        self.fns[name] = Func(name, args, None, docstring, interactive,
                              fn_type, tokens, customize)


if __name__ == "__main__":
    import sys

    lap_file = sys.argv[1]
    with open(lap_file, "r") as fp:
        scanner = LapScanner(fp, show_assembly=True)
    pass
