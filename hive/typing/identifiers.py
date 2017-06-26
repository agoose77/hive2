from enum import auto, Flag


class MatchFlags(Flag):
    none = 0
    source_untyped = auto()
    target_untyped = auto()
    either_untyped = source_untyped | target_untyped


def identifier_is_valid(value):
    if isinstance(value, str):
        return True

    if not isinstance(value, tuple):
        return False

    return all((isinstance(x, str) for x in value))


def identifier_to_tuple(value, allow_none=True):
    """Generate a tuple identifier from a string / tuple object.

    String identifiers are split by full-stop '.'.
    """
    if value is None:
        if not allow_none:
            raise ValueError("None is not permitted!")
        return ()

    if isinstance(value, str):
        return tuple(value.split('.'))
    
    if not identifier_is_valid(value):
        raise ValueError("'{}' is not a valid identifier".format(value))

    return value


def match_identifiers(source_identifier, target_identifier, support_flags=MatchFlags.either_untyped):
    """Checks that two identifier strings match by comparing their first N elements,
    where N is the length of the shortest converted data type tuple.
    
    Returns tuple of common types that match. If either identifier is None, return None if support_untyped is True, 
    else () - indicating no match

    :param source_identifier: string of first identifier
    :param target_identifier: string of second identifier
    """
    if not source_identifier:
        return None if support_flags & MatchFlags.source_untyped else ()

    if not target_identifier:
        return None if support_flags & MatchFlags.target_untyped else ()

    type_a = identifier_to_tuple(source_identifier)
    type_b = identifier_to_tuple(target_identifier)

    return find_common_sequence(type_a, type_b)


def find_common_sequence(left, right):
    matches = []
    for a, b in zip(left, right):
        if a != b:
            break
        matches.append(a)
    return tuple(matches)


def is_subtype(data_type, base_type):
    base_as_tuple = identifier_to_tuple(base_type)
    type_as_tuple = identifier_to_tuple(data_type)

    common_sequence = find_common_sequence(base_as_tuple, type_as_tuple)
    return len(common_sequence) == len(base_as_tuple)
