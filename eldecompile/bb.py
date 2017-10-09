#!/usr/bin/env python
from graph import (BB_ENTRY, BB_JUMP_UNCONDITIONAL, BB_NOFOLLOW)
from eldecompile.tok import Token

class BasicBlock(object):
  """Represents a basic block (or rather extended basic block) from the
    bytecode. It's a bit more than just the a continuous range of the
    bytecode offsets. It also contains * jump-targets offsets, * flags
    that classify flow information in the block * graph node
    predecessor and successor sets, filled in a later phase * some
    layout information for dot graphing

  """

  def __init__(self, start_offset, end_offset, follow_offset,
               flags = set(),
               jump_offsets=set([])):

    # The offset of the first and last instructions of the basic block.
    self.start_offset = start_offset
    self.end_offset = end_offset

    # The follow offset is just the offset that follows the last
    # offset of this basic block. It is None in the very last
    # basic block. Note that the the block that follows isn't
    # and "edge" from this basic block if the last instruction was
    # an unconditional jump or a return.
    # It is however useful to record this so that when we print
    # the flow-control graph, we place the following basic block
    # immediately below.
    self.follow_offset = follow_offset

    # Jump offsets is the targets of all of the jump instructions
    # inside the basic block. Note that jump offsets can come from
    # things SETUP_.. operations as well as JUMP instructions
    self.jump_offsets = jump_offsets

    # flags is a set of interesting bits about the basic block.
    # Elements of the bits are BB_... constants
    self.flags = flags
    self.index = (start_offset, end_offset)

    # Lists of predecessor and successor bacic blocks
    # This is computed in cfg.
    self.predecessors = set([])
    self.successors = set([])

    # Set true if this is dead code, or unureachable
    self.unreachable = False
    self.number = None


  # A nice print routine for a Basic block
  def __repr__(self):
      if len(self.jump_offsets) > 0:
        jump_text = ", jumps=%s" % sorted(self.jump_offsets)
      else:
        jump_text = ""
      if len(self.flags) > 0:
        flag_text = ", flags=%s" % sorted(self.flags)
      else:
        flag_text = ""
      return ('BasicBlock(range: %s%s, follow_offset=%s%s)'
              % (self.index, flag_text, self.follow_offset, jump_text))


JUMP_UNCONDITONAL = frozenset(['GOTO'])
JUMP_CONDITIONAL = frozenset("""
GOTO-IF-NIL GOTO-IF-NIL-ELSE-POP GOTO-IF-NOT-NIL GOTO-IF-NOT-NIL-POP
""".split())
JUMP_INSTRUCTIONS = JUMP_CONDITIONAL | JUMP_UNCONDITONAL
NOFOLLOW_INSTRUCTIONS = frozenset("""
GOTO RETURN
""".split())
class BBMgr(object):

  def __init__(self):
    self.bb_list = []
    self.offset2label = {}
    self.jumps2offset = {}
    self.jump_targets = {}
    # Pick up appropriate version

  def add_bb(self, start_offset, end_offset, follow_offset, flags,
             jump_offsets):
      self.bb_list.append(BasicBlock(start_offset, end_offset,
                                     follow_offset,
                                     flags = flags,
                                     jump_offsets = jump_offsets))
      start_offset = end_offset
      flags = set([])
      jump_offsets = set([])
      return flags, jump_offsets


def get_offset(inst):
    offset = inst.offset
    if isinstance(offset, int):
        return offset
    if offset.find(':') > -1:
        offset = offset[:offset.find(':')]
    return int(offset)

def basic_blocks(instructions):
    """Create a list of basic blocks found in a code object
    """

    bblocks = BBMgr()
    bblocks.label2offset = {}
    bblocks.jumps2offset = {}


    # Populate label2offset map
    for i, inst in enumerate(instructions):
        op = inst.kind
        offset = get_offset(inst)
        if op == 'LABEL':
            bblocks.label2offset[inst.attr[1:]] = offset
            pass
        pass

    # Get jump targets
    jump_targets = set()
    bblocks.jumps2offset = {}
    for inst in instructions:
        op = inst.kind
        offset = get_offset(inst)

        if op in JUMP_INSTRUCTIONS:
            jump_offset = bblocks.label2offset[inst.attr]
            jump_targets.add(jump_offset)
            if jump_offset not in bblocks.jumps2offset:
                bblocks.jumps2offset[jump_offset] = [offset]
            else:
                bblocks.jumps2offset[jump_offset].append(offset)
            pass

    last_offset = -1
    new_instructions = []
    for inst in instructions:
        offset = get_offset(inst)
        if offset != last_offset:
            sources = bblocks.jumps2offset.get(offset, [])
            for source in sorted(sources, reverse=True):
                new_instructions.append(Token('COME_FROM', source, offset))
                pass
            last_offset = offset
        new_instructions.append(inst)

    instructions = new_instructions
    print('-' * 40)
    for i in new_instructions:
        print(i)

    start_offset = 0
    end_offset = -1
    jump_offsets = set()
    prev_offset = -1
    endloop_offsets = [-1]
    flags = set([BB_ENTRY])

    for i, inst in enumerate(instructions):
        prev_offset = end_offset
        end_offset = get_offset(inst)
        op = inst.kind
        offset = get_offset(inst)
        if i+1 < len(instructions):
            follow_offset = get_offset(instructions[i+1])
        else:
            follow_offset = get_offset(instructions[i])+1

        if offset == endloop_offsets[-1]:
          endloop_offsets.pop()
        pass

        if offset in jump_targets:
            # Fallthrough path and jump target path.
            # This instruction definitely starts a new basic block
            # Close off any prior basic block
            if start_offset < end_offset:
                flags, jump_offsets = bblocks.add_bb(start_offset,
                                                prev_offset, end_offset,
                                                flags, jump_offsets)
                start_offset = end_offset

        # Add block flags for certain classes of instructions
        if op in JUMP_INSTRUCTIONS:
            # Some sort of jump instruction.
            # While in theory an absolute jump could be part of the
            # same (extened) basic block, for our purposes we would like to
            # call them two basic blocks as that probably mirrors
            # the code more simply.

            # Figure out where we jump to amd add it to this
            # basic block's jump offsets.
            jump_offset = bblocks.label2offset[inst.attr]

            jump_offsets.add(jump_offset)
            if op in JUMP_UNCONDITONAL:
                flags.add(BB_JUMP_UNCONDITIONAL)
                pass
            flags, jump_offsets = bblocks.add_bb(start_offset,
                                                 end_offset, follow_offset,
                                                 flags, jump_offsets)
            start_offset = follow_offset
        elif op in NOFOLLOW_INSTRUCTIONS:
            flags.add(BB_NOFOLLOW)
            flags, jump_offsets = bblocks.add_bb(start_offset,
                                                 end_offset, follow_offset,
                                                 flags, jump_offsets)
            start_offset = follow_offset
            pass
        pass

    if len(bblocks.bb_list):
      bblocks.bb_list[-1].follow_offset = None
    if start_offset <= end_offset:
        bblocks.bb_list.append(BasicBlock(start_offset, end_offset, None,
                                          flags=flags, jump_offsets=jump_offsets))

    return bblocks, instructions
