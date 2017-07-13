from itertools import product
from operator import itemgetter
from typing import List, Tuple, NamedTuple

from ..contexts import register_bee
from ..exception import MatchFailedError, HiveConnectionError
from ..interfaces import (ConnectSourceBase, ConnectSourceDerived, ConnectTargetBase, ConnectTargetDerived, BeeBase,
                          Bee, ConnectTarget, ConnectSource, ConnectCandidate)
from ..manager import memoize, HiveModeFactory
from ..typing import get_match_score, find_matching_ast, MatchFlags, parse_type_string


class ScoredConnectPair(NamedTuple):
    score: int
    candidate: ConnectCandidate


TypedCandidates = Tuple[Tuple[ConnectCandidate, ConnectCandidate], ...]

_first_item = itemgetter(0)


def sorted_candidates_from_scored(scored_candidates: List[ScoredConnectPair]) -> TypedCandidates:
    """Return sorted tuple of candidate pairs from list of scored candidates
    
    :param scored_candidates: sequence of (score, source, target) items
    """
    return tuple(x.candidate for x in sorted(scored_candidates, key=_first_item, reverse=True))


def find_connection_candidates(source_hive: ConnectSourceDerived, target_hive: ConnectTargetDerived):
    """Finds appropriate connections between ConnectionSources and ConnectionTargets

    :param source_hive: ConnectSourceDerived instance
    :param target_hive: ConnectTargetDerived instance
    """
    scored_typed_candidates = []
    scored_untyped_candidates = []

    sources = source_hive._hive_find_connect_sources()
    targets = target_hive._hive_find_connect_targets()

    for source_candidate, target_candidate in product(sources, targets):
        source_bee = getattr(source_hive, source_candidate.bee_name)
        target_bee = getattr(target_hive, target_candidate.bee_name)

        # Check if both general types match and no configuration issues
        try:
            source_bee._hive_is_connectable_source(target_bee)
            target_bee._hive_is_connectable_target(source_bee)
        except HiveConnectionError:
            continue

        # Use new match API & score API
        source_data_type = source_candidate.data_type
        target_data_type = target_candidate.data_type

        left_ast = parse_type_string(source_data_type)
        right_ast = parse_type_string(target_data_type)

        # First match without permitting untyped targets
        try:
            match = find_matching_ast(left_ast, right_ast, MatchFlags.match_shortest)

        except MatchFailedError:
            # Then fall back on matching untyped targets
            try:
                match = find_matching_ast(left_ast, right_ast, MatchFlags.match_shortest | MatchFlags.permit_any_target)
            except MatchFailedError:
                continue

            untyped_score = get_match_score(match)
            candidate = ScoredConnectPair(untyped_score, ConnectCandidate(source_candidate, target_candidate))
            scored_untyped_candidates.append(candidate)

        else:
            typed_score = get_match_score(match)
            candidate = ScoredConnectPair(typed_score, ConnectCandidate(source_candidate, target_candidate))
            scored_typed_candidates.append(candidate)

    # Sort candidates according to length of match (largest first)
    typed_candidates = sorted_candidates_from_scored(scored_typed_candidates)

    # Only return untyped candidates if no typed candidates available
    # This prevents counting multiple matches where we've been "scraping the barrel"
    if not typed_candidates:
        return sorted_candidates_from_scored(scored_untyped_candidates)

    return typed_candidates


# TODO allow multiple connections when they're all unique!
def find_connection_between_hives(source_hive, target_hive):
    """Find best connection between two runtime hives.
    
    For each legal connection, first attempt to find typed target connection between source and target.
    If a typed target connection cannot be made, attempt a typed source untyped target connection
    """
    candidates = find_connection_candidates(source_hive, target_hive)
    if not candidates:
        raise ValueError("No matching connections found")

    # TODO - allow multiple if not more than 1 untyped
    if len(candidates) > 1:
        candidate_names = [(a.bee_name, b.bee_name) for a, b in candidates]
        raise TypeError("Multiple matches found between {} and {}: {}"
                        .format(source_hive, target_hive, candidate_names))

    source_candidate, target_candidate = candidates[0]

    # Get runtime public
    source = getattr(source_hive, source_candidate.bee_name)
    target = getattr(target_hive, target_candidate.bee_name)

    return source, target


def resolve_endpoints(source: [ConnectSource, ConnectSourceDerived], target: ConnectTargetBase) -> Tuple[
    ConnectSource, ConnectTarget]:
    """Find resolved endpoints for source/targets which are dervived connection sources/targets (Hives)"""
    hive_source = isinstance(source, ConnectSourceDerived)
    hive_target = isinstance(target, ConnectTargetDerived)

    # TODO: register connection, or insert a listener function in between
    if hive_source and hive_target:
        source, target = find_connection_between_hives(source, target)

    else:
        if hive_source:
            source = source._hive_get_connect_source(target)

        elif hive_target:
            target = target._hive_get_connect_target(source)

    return source, target


def build_connection(source: ConnectSourceBase, target: ConnectTargetBase):
    """Runtime connection builder between source and target"""
    validate_endpoints(source, target)
    source_resolved, target_resolved = resolve_endpoints(source, target)

    # raises an Exception if incompatible
    source_resolved._hive_is_connectable_source(target_resolved)
    target_resolved._hive_is_connectable_target(source_resolved)

    target_resolved._hive_connect_target(source_resolved)
    source_resolved._hive_connect_source(target_resolved)


class ConnectionBuilder(BeeBase):
    def __init__(self, source: ConnectSourceBase, target: ConnectTargetBase):
        validate_endpoints(source, target)

        self._source = source
        self._target = target

        super().__init__()

        register_bee(self)

    @memoize
    def bind(self, run_hive):
        source = self._source.bind(run_hive)
        target = self._target.bind(run_hive)

        return build_connection(source, target)

    def __repr__(self):
        return "ConnectionBuilder({!r}, {!r})".format(self._source, self._target)


def validate_endpoints(source, target):
    if isinstance(source, Bee):
        assert source.implements(ConnectSourceBase), source
        assert target.implements(ConnectTargetBase), target

    else:
        assert isinstance(source, ConnectSourceBase), source
        assert isinstance(target, ConnectTargetBase), target


connect = HiveModeFactory("hive.connect", IMMEDIATE=build_connection, BUILD=ConnectionBuilder)
