#!/usr/bin/env python
from spark_parser.ast import AST

from eldecompile.scanner import fn_scanner
from eldecompile.parser import ElispParser, ParserError
from eldecompile.semantics import SourceWalker
from eldecompile.transform import TransformTree
from eldecompile.bb import basic_blocks
from eldecompile.cfg import ControlFlowGraph
from eldecompile.dominators import DominatorTree, build_df


import os, sys
import click

def flow_control(name, tokens, show_assembly):
#  Flow control analysis of instruction
    bblocks, tokens = basic_blocks(tokens, show_assembly)
    for bb in bblocks.bb_list:
        print("\t", bb)
    cfg = ControlFlowGraph(bblocks.bb_list)
    dot_path = '/tmp/flow-%s.dot' % name
    png_path = '/tmp/flow-%s.png' % name
    open(dot_path, 'w').write(cfg.graph.to_dot())
    print("%s written" % dot_path)
    os.system("dot -Tpng %s > %s" % (dot_path, png_path))
    try:
        dom_tree = DominatorTree(cfg).tree()
        dom_tree = build_df(dom_tree)
        dot_path = '/tmp/flow-dom-%s.dot' % name
        png_path = '/tmp/flow-dom-%s.png' % name
        open(dot_path, 'w').write(dom_tree.to_dot())
        print("%s written" % dot_path)
        os.system("dot -Tpng %s > %s" % (dot_path, png_path))
        print('=' * 30)
        return tokens
    except:
        import traceback
        traceback.print_exc()
        print("Unexpected error:", sys.exc_info()[0])
        print("%s had an error" % name)
        return tokens

def deparse(path, show_assembly, show_grammar, show_tree):
    # Scan...
    with open(path, 'r') as fp:
        fn_def, tokens, customize = fn_scanner(fp, show_assembly=show_assembly)
        pass

    import os.path as osp
    name = osp.basename(path)
    tokens = flow_control(name, tokens, show_assembly)

    # Parse...
    p = ElispParser(AST, tokens)
    p.add_custom_rules(tokens, customize)

    parser_debug = {'rules': False, 'transition': False, 'reduce' : show_grammar,
                   'errorstack': 'full', 'dups': False }

    try:
        ast = p.parse(tokens, debug=parser_debug)
    except ParserError as e:
        print("file: %s\n\t %s\n" % (path, e))
        sys.exit(1)

    # Before transformation
    # if show_tree:
    #    print(ast)

    # .. and Generate Elisp
    transformed_ast = TransformTree(ast, debug=False).traverse(ast)

    # After transformation
    if show_tree:
        print(ast)
    formatter = SourceWalker(transformed_ast)
    is_file = fn_def.fn_type == 'file'
    if is_file:
        indent = header = ''
    else:
        indent = '  '
        header = "(%s %s%s%s" % (fn_def.fn_type, fn_def.name, fn_def.args,
                                 fn_def.docstring)

    result = formatter.traverse(ast, indent)
    result = result.rstrip()

    if (not header.endswith("\n")
            and not result.startswith("\n") or fn_def.interactive):
        header += "\n"

    if fn_def.interactive is not None:
        print("%s%s(interactive %s)\n%s%s)" %
              (header, indent, fn_def.interactive, indent, result))
    elif is_file:
        print("%s%s" % (header, result))
    else:
        print("%s%s%s)" % (header, indent, result))


@click.command()
@click.option('-a', '--assembly/--no-assembly', default=False,
              help='Show LAP assembly')
@click.option('-g', '--grammar/--no-grammar', default=False,
              help='Show grammar reductions')
@click.option('-t', '--tree/--no-tree', default=False,
              help='Show parse tree')
@click.argument('lap-filename', type=click.Path(exists=True))
def main(assembly, grammar, tree, lap_filename):
    """Lisp Assembler Program (LAP) deparser"""
    deparse(lap_filename,
            show_assembly=assembly, show_grammar=grammar, show_tree=tree)

if __name__ == '__main__':
    main()
