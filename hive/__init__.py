import logging.config

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'ERROR',
            'propagate': True
        }
    }
}

logging.config.dictConfig(logging_config)

from .hive import (hive, dyna_hive, meta_hive, HiveBuilder, RuntimeHive, MetaHivePrimitive, HiveObject,
                   validate_external_name, validate_internal_name)
from .typing import (data_types_match, MatchFlags, parse_type_string, data_type_is_untyped, is_valid_data_type,
                     find_matching_ast, type_asts_match, CompositeType, SimpleType, SequenceType, MappingType, Type,
                     TypeName, AnyType, get_base_data_type)
from .identifier import is_valid_identifier
from .contexts import (get_building_hive, get_mode, get_run_hive, get_matchmaker_validation_enabled,
                       set_matchmaker_validation_enabled,
                       matchmaker_validation_enabled_as)
from .manager import memo_property, memoize, MemoProperty, ModeFactory
from .public import attribute, modifier, method, plugin, property, socket
from .private import READ_WRITE, READ, WRITE
from .policies import SingleOptional, SingleRequired, MultipleOptional, MultipleRequired
from .parameter import parameter
from .exception import HiveException
from .annotations import (types, options, return_type, get_argument_options, get_argument_types, get_return_type,
                          update_wrapper, typed_property)
