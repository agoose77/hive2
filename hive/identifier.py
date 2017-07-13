def is_valid_identifier(identifier) -> bool:
    if identifier is None:
        return True

    return isinstance(identifier, str)
