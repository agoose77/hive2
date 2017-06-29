def is_valid_identifier(identifier):
    if identifier is None:
        return True

    return isinstance(identifier, str)