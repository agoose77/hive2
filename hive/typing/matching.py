from enum import auto, Flag

from .ast import AnyType, CompositeType, MappingType, SequenceType, TypeName
from .parser import parse_type_string
from ..exception import MatchFailedError, MatchCaseUnhandled, InvalidMatchCase


class MatchFlags(Flag):
    none = 0
    permit_any_source = auto()
    permit_any_target = auto()
    full_match = auto()
    permit_any = permit_any_source | permit_any_target


def find_common_sequence(source, target):
    matches = []
    for a, b in zip(source, target):
        if a != b:
            break
        matches.append(a)
    return tuple(matches)


def find_type_name_type_name_match(source, target, flags):
    common_type_name = find_common_sequence(source.type_name, target.type_name)
    if common_type_name:
        if (flags & MatchFlags.full_match) and len(common_type_name) != min(len(source.type_name),
                                                                            len(target.type_name)):
            raise ValueError

        return TypeName(common_type_name)
    raise ValueError


def find_sequence_sequence_match(source, target, flags):
    element_ast = find_matching_ast(source.etype, target.etype, flags)
    return SequenceType(source.type, element_ast)


def find_composite_composite_match(source, target, flags):
    """Compare two composites"""
    if source.type != target.type:
        raise ValueError

    # Compare set/list/tuple
    if isinstance(source, SequenceType):
        return find_sequence_sequence_match(source, target, flags)

    # Compare mappings
    return find_mapping_mapping_match(source, target, flags)


def find_mapping_mapping_match(source, target, flags):
    key_ast = find_matching_ast(source.ktype, target.ktype, flags)
    value_ast = find_matching_ast(source.vtype, target.vtype, flags)

    return MappingType(source.type, key_ast, value_ast)


def find_type_name_composite_match(type_name, composite, flags):
    if len(type_name.type_name) > 1:  # TODO allow 0 (== no typing)
        raise ValueError

    source_type = type_name.type_name[0]
    if source_type != composite.type:
        raise MatchFailedError

    return type_name


def if_either_are(cls, other_cls, then):
    def matcher(source, target, flags):
        if isinstance(source, cls) and isinstance(target, other_cls):
            return then(source, target, flags)
        elif isinstance(target, cls) and isinstance(source, other_cls):
            return then(target, source, flags)
        raise MatchCaseUnhandled

    return matcher


def if_source_is(cls, then):
    def matcher(source, target, flags):
        if isinstance(source, cls):
            return then(source, target, flags)
        raise MatchCaseUnhandled

    return matcher


def if_target_is(cls, then):
    def matcher(source, target, flags):
        if isinstance(target, cls):
            return then(source, target, flags)
        raise MatchCaseUnhandled

    return matcher


def if_order_is(left_cls, right_cls, then):
    def matcher(source, target, flags):
        if isinstance(source, left_cls) and isinstance(target, right_cls):
            return then(source, target, flags)
        raise MatchCaseUnhandled

    return matcher


def source_is_any(source, target, flags):
    if flags & MatchFlags.permit_any_source:
        return source
    raise MatchFailedError


def target_is_any(source, target, flags):
    if flags & MatchFlags.permit_any_target:
        return target
    raise MatchFailedError


_dispatch_table = [
    if_source_is(AnyType, then=source_is_any),
    if_target_is(AnyType, then=target_is_any),
    if_order_is(SequenceType, SequenceType, then=find_sequence_sequence_match),
    if_order_is(MappingType, MappingType, then=find_mapping_mapping_match),
    if_order_is(TypeName, TypeName, find_type_name_type_name_match),
    if_either_are(TypeName, CompositeType, find_type_name_composite_match),
]


def is_valid_data_type(string):
    try:
        parse_type_string(string)
    except ValueError:
        return False
    return True


def find_matching_ast(source, target, flags=MatchFlags.none):
    for matcher in _dispatch_table:
        try:
            return matcher(source, target, flags)

        except MatchCaseUnhandled:
            continue

    raise InvalidMatchCase


def type_asts_match(source, target, flags=MatchFlags.none):
    try:
        find_matching_ast(source, target, flags)

    except MatchFailedError:
        return False

    return True


def data_type_is_untyped(type_string):
    return isinstance(parse_type_string(type_string), AnyType)


def data_types_match(source_string, target_string, flags=MatchFlags.none):
    source_ast = parse_type_string(source_string)
    target_ast = parse_type_string(target_string)
    return type_asts_match(source_ast, target_ast, flags)
