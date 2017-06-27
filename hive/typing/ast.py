from derp.ast import AST, iter_child_nodes


Type = AST.subclass("Type")
CompositeType = Type.subclass("CompositeType")
SequenceType = CompositeType.subclass("SequenceType", "type etype")
MappingType = CompositeType.subclass("MappingType", "type ktype vtype")

SimpleType = Type.subclass("SimpleType")
TypeName = SimpleType.subclass("TypeName", "type_name")
AnyType = SimpleType.subclass("AnyType")


def get_match_score(match_ast, depth=1):
    score = depth

    if isinstance(match_ast, AnyType):
        return 0

    if isinstance(match_ast, TypeName):
        score += len(match_ast.type_name)

    for child in iter_child_nodes(match_ast):
        child_score = get_match_score(child, depth + 1)
        if child_score > score:
            score = child_score

    return score
