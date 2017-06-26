from itertools import starmap
from operator import eq

from derp.ast import AST
from derp.grammar import Grammar
from derp.parsers import lit, parse
from derp.utilities import unpack_n


def tokenize_text(string):
    """Change collections tokens from ID tokens to distinct token types"""
    from grammars.ebnf.tokenizer import tokenize_text as _tokenize_text
    return strip_end_formatting_tokens(_tokenize_text(string))


def strip_end_formatting_tokens(tokens):
    token_list = list(tokens)
    for token in reversed(token_list.copy()):
        if token.first not in {'\n', 'ENDMARKER'}:
            break
        token_list.pop()
    yield from token_list


def compare_simple(left, right):
    if all(starmap(eq, zip(left.type_name, right.type_name))):
        return True

    return False


def compare_composite(left, right):
    """Compare two composites"""
    if left.type != right.type:
        return False

    # Compare set/list/tuple
    if isinstance(left, SequenceType):
        return compare(left.etype, right.etype)

    # Compare mappings
    return compare(left.ktype, right.ktype) and compare(left.vtype, right.vtype)


def compare(left, right):
    left_is_simple = isinstance(left, SimpleType)
    right_is_simple = isinstance(right, SimpleType)

    # Both single (simple comparison)
    if left_is_simple and right_is_simple:
        return compare_simple(left, right)

    # Both composite (composite comparison)
    elif not left_is_simple and not right_is_simple:
        return compare_composite(left, right)

    elif left_is_simple and not right_is_simple:
        return is_any(left)

    else:
        return is_any(right)


def to_ast(string):
    token_list = list(tokenize_text(string))
    for token in reversed(token_list.copy()):
        if token.first not in {'\n', 'ENDMARKER'}:
            break
        token_list.pop()

    print(token_list)
    tree = parse(t.root, token_list)
    assert len(tree) in {0, 1}
    return tree.pop()


Type = AST.subclass("Type")
CompositeType = Type.subclass("CompositeType")
SequenceType = CompositeType.subclass("SequenceType", "type etype")
MappingType = CompositeType.subclass("MappingType", "type ktype vtype")
SimpleType = Type.subclass("SimpleType", "type_name")
Union = Type.subclass("Union", "left right")


def emit_sequence(args):
    type_name, specialism = args
    return SequenceType(type_name, specialism)


def emit_mapping(args):
    type_name, _, key, _, _, value, _ = unpack_n(args, 7)
    return MappingType(type_name, key, value)


def emit_single_specialism(args):
    _, name, _ = unpack_n(args, 3)
    return name


def reduce(op, seq):
    left, *remainder = tuple(seq)
    for item in remainder:
        left = op(left, item)
    return left


def emit_simple_type_name(args):
    root, delimited = args

    type_name = root,

    if delimited != '':
        _, following = zip(*delimited)
        type_name = type_name + following

    return SimpleType(type_name)


t = Grammar('types')
t.single_specialism = (lit('[') & t.definition & lit(']')) >> emit_single_specialism
t.sequence = (lit('ID') & t.single_specialism) >> emit_sequence
t.mapping = (lit('ID') & lit('[') & t.definition & lit('-') & lit('>') & t.definition & lit(']')) >> emit_mapping
t.collections = t.sequence | t.mapping
t.simple_type_name = (lit('ID') & +(lit('.') & lit('ID'))) >> emit_simple_type_name
t.definition = t.collections | t.simple_type_name
t.ensure_parsers_defined()


def build_ast(string):
    tokens = tuple(tokenize_text(string))
    return parse(t.definition, tokens).pop()
