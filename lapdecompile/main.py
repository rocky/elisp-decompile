#!/usr/bin/env python
from spark_parser.ast import AST

from lapdecompile.scanner import LapScanner
from lapdecompile.parser import ElispParser, ParserError
from lapdecompile.semantics import SourceWalker
from lapdecompile.transform import TransformTree
from lapdecompile.bb import basic_blocks, ingest
from lapdecompile.cfg import ControlFlowGraph
from lapdecompile.dominators import DominatorTree, build_df


import os, sys
import click


def control_flow(name, instructions, show_assembly, write_cfg):
    #  Flow control analysis of instruction
    bblocks, instructions = basic_blocks(instructions, show_assembly)

    for bb in bblocks.bb_list:
        if write_cfg:
            # FIXME: Perhaps the below debug output should not be tied to writing
            # the control-flow graph?
            print("\t", bb)
        cfg = ControlFlowGraph(bblocks.bb_list)
    try:
        dom_tree = DominatorTree(cfg).tree()
        dom_tree = build_df(dom_tree)
        if write_cfg:
            dot_path = "/tmp/flow-dom-%s.dot" % name
            png_path = "/tmp/flow-dom-%s.png" % name
            open(dot_path, "w").write(dom_tree.to_dot())
            print("%s written" % dot_path)
            os.system("dot -Tpng %s > %s" % (dot_path, png_path))
            dot_path = "/tmp/flow-%s.dot" % name
            png_path = "/tmp/flow-%s.png" % name
            open(dot_path, "w").write(cfg.graph.to_dot())
            print("%s written" % dot_path)
            os.system("dot -Tpng %s > %s" % (dot_path, png_path))
            print("=" * 30)
        instructions = ingest(bblocks, instructions, show_assembly)
        return instructions
    except:
        import traceback

        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print("%s had an error" % name)
        return instructions


def deparse(path, outstream, show_assembly, write_cfg, show_grammar, show_tree):
    # Scan...
    with open(path, "r") as fp:
        scanner = LapScanner(fp, show_assembly=show_assembly)
        pass

    import os.path as osp

    rc = 0
    for fn_name, fn in scanner.fns.items():

        tokens, customize = fn.tokens, fn.customize
        name = f"{osp.basename(path)}:{fn_name}"
        tokens = control_flow(name, tokens, show_assembly, write_cfg)

        # Parse...
        p = ElispParser(AST, tokens)
        p.add_custom_rules(tokens, customize)

        parser_debug = {
            "rules": False,
            "transition": False,
            "reduce": show_grammar,
            "errorstack": "full",
            "dups": False,
        }

        try:
            ast = p.parse(tokens, debug=parser_debug)
        except ParserError as e:
            print("file: %s\n\t %s\n" % (path, e))
            rc = 1
            continue

        # Before transformation
        if show_tree in ("full", "before"):
            print(ast)

        # .. and Generate Elisp
        transformed_ast = TransformTree(ast, debug=False).traverse(ast)

        if show_tree == "full":
            print("=" * 30)

        # After transformation
        if show_tree in ("full", "after"):
            print(ast)

        formatter = SourceWalker(transformed_ast)
        is_file = fn.fn_type == "file"
        if is_file:
            indent = header = ""
        else:
            indent = "  "
            header = "(%s %s%s%s" % (
                fn.fn_type,
                fn.name,
                fn.args,
                fn.docstring,
            )

        # from trepan.api import debug; debug()
        result = formatter.traverse(ast, indent)
        result = result.rstrip()

        if not header.endswith("\n") and not result.startswith("\n") or fn.interactive:
            header += "\n"

        if fn.interactive is not None:
            outstream.write(
                "%s%s(interactive %s)\n%s%s)"
                % (header, indent, fn.interactive, indent, result)
            )
        elif is_file:
            outstream.write("%s%s\n" % (header, result))
        else:
            outstream.write("%s%s%s)\n" % (header, indent, result))
            pass
        pass
    return rc


@click.command()
@click.option("-a", "--assembly/--no-assembly", default=False, help="Show LAP assembly")
@click.option("-G", "--graphs/--no-graphs", default=False, help="Produce dot/png control-flow graphs")
@click.option(
    "-g", "--grammar/--no-grammar", default=False, help="Show grammar reductions"
)
@click.option(
    "--tree",
    default="none",
    type=click.Choice(["after", "before", "full", "none"]),
    help="Show parse tree",
)
@click.option("-t", "tree_alias", flag_value="after", help="alias for --tree=after")
@click.option("-T", "tree_alias", flag_value="full", help="alias for --tree=full")
@click.argument("lap-filename", type=click.Path(exists=True))
def main(assembly, graphs, grammar, tree, tree_alias, lap_filename):
    """Lisp Assembler Program (LAP) decompiler"""
    if tree_alias:
        tree = tree_alias
    sys.exit(deparse(lap_filename, sys.stdout, show_assembly=assembly,
                     write_cfg=graphs,
                     show_grammar=grammar, show_tree=tree))

if __name__ == "__main__":
    main()
