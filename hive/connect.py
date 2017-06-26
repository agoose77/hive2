from collections import namedtuple
from itertools import product
from operator import itemgetter

from .classes import HiveBee
from .debug import get_debug_context
from .manager import get_mode, memoize, register_bee
from .mixins import ConnectSourceBase, ConnectSourceDerived, ConnectTargetBase, ConnectTargetDerived, Bee, Bindable, \
    Exportable
from .typing import match_identifiers, MatchFlags

ConnectionCandidate = namedtuple("ConnectionCandidate", ("bee_name", "data_type"))

_first_item = itemgetter(0)


def sorted_candidates_from_scored(scored_candidates):
    """Return sorted list of candidate pairs from list of scored candidates
    
    :param scored_candidates: sequence of (score, source, target) items
    """
    return tuple(x[1:] for x in sorted(scored_candidates,key=_first_item, reverse=True))


def get_connection_score(source_candidate, target_candidate, match_flags):
    """Score the quality of the connection match
    
    Return None if no valid match according to match glags
    """
    # Score connection by length of type match
    source_data_type = source_candidate.data_type
    target_data_type = target_candidate.data_type
    common_sequence = match_identifiers(source_data_type, target_data_type, match_flags)

    if common_sequence:
        return len(common_sequence)

    elif common_sequence is None:
        # Worst case match - untyped source/target
        return -1

    return None


def find_connection_candidates(source_hive, target_hive):
    """Finds appropriate connections between ConnectionSources and ConnectionTargets

    :param sources: connection sources
    :param targets: connection targets
    :param support_untyped_target: require target type definitions to be declared
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
        except ConnectionError:
            continue

        # First preferentially try typed target match
        typed_score = get_connection_score(source_candidate, target_candidate, MatchFlags.none)
        if typed_score:
            scored_typed_candidates.append((typed_score, source_candidate, target_candidate))

        else:
            # If we cannot find a typed match, allow target to have no target type specified
            # At this point, we may still not find a match, because the generic _hive_is_connectable methods
            # Support target or source being untyped
            untyped_score = get_connection_score(source_candidate, target_candidate, MatchFlags.target_untyped)
            if untyped_score:
                scored_untyped_candidates.append((untyped_score, source_candidate, target_candidate))

    # Sort candidates according to length of match (largest first)
    typed_candidates = sorted_candidates_from_scored(scored_typed_candidates)

    # Only return untyped candidates if no typed candidates available
    # This prevents counting multiple matches where we've been "scraping the barrel"
    if not typed_candidates:
        return sorted_candidates_from_scored(scored_untyped_candidates)

    return typed_candidates


# TODO allow multiple connections when they're all unique!


def find_connection_between_hives(source_hive, target_hive):
    """Find best connection between two hives.
    
    For each legal connection, first attempt to find typed target connection between source and target.
    If a typed target connection cannot be made, attempt a typed source untyped targte connection
    """
    if not source_hive._hive_can_connect_hive(target_hive):
        raise ValueError("Both hives must be either Hive runtimes or Hive objects")

    # First try: match candidates with named data_type
    candidates = find_connection_candidates(source_hive, target_hive)

    if not candidates:
        raise ValueError("No matching connections found")

    elif len(candidates) > 1:
        candidate_names = [(a.bee_name, b.bee_name) for a, b in candidates]
        raise TypeError("Multiple matches found between {} and {}: {}"
                        .format(source_hive, target_hive, candidate_names))

    source_candidate, target_candidate = candidates[0]

    source = getattr(source_hive, source_candidate.bee_name)
    target = getattr(target_hive, target_candidate.bee_name)

    return source, target


def resolve_endpoints(source, target):
    """Find resolved endpoints for source/targets which are dervived connection sources/targets (Hives)"""
    # TODO: register connection, or insert a listener function in between
    hive_source = isinstance(source, ConnectSourceDerived)
    hive_target = isinstance(target, ConnectTargetDerived)

    # Find appropriate bees to connect within respective hives
    if hive_source and hive_target:
        source, target = find_connection_between_hives(source, target)

    else:
        if hive_source:
            source = source._hive_get_connect_source(target)

        elif hive_target:
            target = target._hive_get_connect_target(source)

    return source, target


def build_connection(source, target):
    """Runtime connection builder between source and target"""
    source, target = resolve_endpoints(source, target)

    # raises an Exception if incompatible
    source._hive_is_connectable_source(target)
    target._hive_is_connectable_target(source)

    debug_context = get_debug_context()
    if debug_context is not None:
        debug_context.build_connection(source, target)

    else:
        target._hive_connect_target(source)
        source._hive_connect_source(target)


class Connection(Bindable):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def __repr__(self):
        return "<Connection {} ~> {}>".format(self.source.repr(), self.target)

    @memoize
    def bind(self, run_hive):
        source = self.source
        if isinstance(source, Bindable):
            source = source.bind(run_hive)

        target = self.target

        if isinstance(target, Bindable):
            target = target.bind(run_hive)

        return build_connection(source, target)


class ConnectionBee(HiveBee):
    def __init__(self, source, target):
        super(ConnectionBee, self).__init__()

        self.source = source
        self.target = target

    def __repr__(self):
        return "<{}: ({}, {})>".format(self.__class__.__name__, *self.args)

    @memoize
    def getinstance(self, hive_object):
        source = self.source
        target = self.target

        if isinstance(source, Bee):
            if isinstance(source, Exportable):
                source = source.export()

            source = source.getinstance(hive_object)

        if isinstance(target, Bee):
            if isinstance(target, Exportable):
                target = target.export()

            target = target.getinstance(hive_object)

        if get_mode() == "immediate":
            return build_connection(source, target)

        else:
            return Connection(source, target)


def connect(source, target):
    if isinstance(source, Bee):
        assert source.implements(ConnectSourceBase), source
        assert target.implements(ConnectTargetBase), target

    else:
        assert isinstance(source, ConnectSourceBase), source
        assert isinstance(target, ConnectTargetBase), target

    if get_mode() == "immediate":
        build_connection(source, target)

    else:
        connection_bee = ConnectionBee(source, target)
        register_bee(connection_bee)
        return connection_bee
