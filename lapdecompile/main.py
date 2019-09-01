#!/usr/bin/env python
from spark_parser.ast import AST

from lapdecompile.scanner import fn_scanner
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


def deparse(path, show_assembly, write_cfg, show_grammar, show_tree):
    # Scan...
    with open(path, "r") as fp:
        fn_def, tokens, customize = fn_scanner(fp, show_assembly=show_assembly)
        pass

    import os.path as osp

    name = osp.basename(path)
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
        sys.exit(1)

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
    is_file = fn_def.fn_type == "file"
    if is_file:
        indent = header = ""
    else:
        indent = "  "
        header = "(%s %s%s%s" % (
            fn_def.fn_type,
            fn_def.name,
            fn_def.args,
            fn_def.docstring,
        )

    result = formatter.traverse(ast, indent)
    result = result.rstrip()

    if not header.endswith("\n") and not result.startswith("\n") or fn_def.interactive:
        header += "\n"

    if fn_def.interactive is not None:
        print(
            "%s%s(interactive %s)\n%s%s)"
            % (header, indent, fn_def.interactive, indent, result)
        )
    elif is_file:
        print("%s%s" % (header, result))
    else:
        print("%s%s%s)" % (header, indent, result))


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
    """Lisp Assembler Program (LAP) deparser"""
    if tree_alias:
        tree = tree_alias
    deparse(lap_filename, show_assembly=assembly,
            write_cfg=graphs,
            show_grammar=grammar, show_tree=tree)


if __name__ == "__main__":
    main()
