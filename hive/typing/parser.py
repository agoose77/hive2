from derp import Grammar, lit, parse, unpack as unpack_n
from grammars.ebnf import EBNFTokenizer

from .ast import AnyType, MappingType, SequenceType, TypeName


tokenizer = EBNFTokenizer()
_tokenize_text = tokenizer.tokenize_text


def tokenize_text(string):
    """Change collections tokens from ID tokens to distinct token types"""
    return strip_end_formatting_tokens(_tokenize_text(string))


def strip_end_formatting_tokens(tokens):
    token_list = list(tokens)
    for token in reversed(token_list.copy()):
        if token.first not in {'\n', 'ENDMARKER'}:
            break
        token_list.pop()
    yield from token_list


def parse_type_string(type_string):
    if not isinstance(type_string, str):
        if type_string is None:
            return AnyType()

        raise ValueError("Require string or None for type string, not {!r}".format(type_string))

    if not type_string:
        return AnyType()

    tokens = strip_end_formatting_tokens(tokenize_text(type_string))
    tree = parse(t.definition, tokens)

    if len(tree) != 1:
        raise ValueError("Unable to parse type string: {}".format(type_string))

    return next(iter(tree))


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

    return TypeName(type_name)


def emit_any_type(args):
    return AnyType()


t = Grammar('types')
t.single_specialism = (lit('[') & t.definition & lit(']')) >> emit_single_specialism
t.sequence = (lit('ID') & t.single_specialism) >> emit_sequence
t.mapping = (lit('ID') & lit('[') & t.definition & lit('-') & lit('>') & t.definition & lit(']')) >> emit_mapping
t.collections = t.sequence | t.mapping
t.simple_type_name = (lit('ID') & (lit('.') & lit('ID'))[...]) >> emit_simple_type_name
t.any_type = lit('?') >> emit_any_type
t.definition = t.collections | t.simple_type_name | t.any_type
t.ensure_parsers_defined()


def build_ast(string):
    tokens = tuple(tokenize_text(string))
    return next(iter(parse(t.definition, tokens)))