# SPDX-FileCopyrightText: 2021 Konrad Weihmann
# SPDX-FileCopyrightText: 2023 Henrik Sandklef
# SPDX-License-Identifier: Unlicensed

import csv
import json
import os
from enum import Enum, unique

OSADL_MATRIX = os.path.join(os.path.dirname(__file__), 'osadl-matrix.csv')
OSADL_MATRIX_JSON = os.path.join(os.path.dirname(__file__), 'osadl-matrix.json')
__osadl_db = {}


@unique
class OSADLCompatibility(Enum):
    """
    YES - licenses are compatible
    NO - licenses are NOT compatible
    UNKNOWN - license compatibility is uncertain
    CHECKDEP - compatibility has depencies that need to be checked
    UNDEF - at least one of the licenses are not present in the OSADL matrix
    """
    YES = 'Yes'
    NO = 'No'
    UNKNOWN = 'Unknown'
    CHECKDEP = 'Check dependency'
    UNDEF = 'Undefined license'

    @staticmethod
    def from_text(_in):
        _map = {
            'Yes': OSADLCompatibility.YES,
            'No': OSADLCompatibility.NO,
            'Unknown': OSADLCompatibility.UNKNOWN,
            'Check dependency': OSADLCompatibility.CHECKDEP,
            'Same': OSADLCompatibility.YES,
        }
        return _map.get(_in, OSADLCompatibility.UNDEF)


def __read_db(customdb=None):
    """reads (first call only) matrix file
    """
    global __osadl_db
    if not __osadl_db:
        try:
            with open(customdb or OSADL_MATRIX_JSON) as i:
                __osadl_db = json.load(i)
                # The below will raise KeyError if any of them are
                # removed. Keep as is to make sure we detect when keys changes.
                __osadl_db.pop('timestamp')
                __osadl_db.pop('timeformat')
        except json.JSONDecodeError:
            if customdb:  # pragma: no cover
                with open(customdb) as i:
                    _reader = csv.DictReader(i, delimiter=',', quotechar='"')
                    for row in _reader:
                        key = row['Compatibility*']
                        for k, v in row.items():
                            if k == 'Compatibility*':
                                continue
                            if key not in __osadl_db:
                                __osadl_db[key] = {}
                            __osadl_db[key][k] = v


def is_compatible(outbound, inbound, customdb=None):
    """checks if the 'outbound' license is compatible with the 'inbound'
   license. If the licenses can be found in the matrix and the
   licenses are compatible, True is returned. In all other cases False
   is returned.

    Args:
        outbound (string): SPDX ID for an outbound license, e.g. the license used for distribution of an application
        inbound (string): SPDX ID for an inbound license, e.g. the license used for a dependency of the application

    Returns:
        True or False

    """
    return get_compatibility(outbound, inbound, customdb) == OSADLCompatibility.YES


def get_compatibility(outbound, inbound, customdb=None):
    """returns the compatibility status between the 'outbound' and the
    'inbound' licenses. If any (or both) of the licenses are not
    present in the OSADL matrix, then UNDEF is returned.

    Args:
        outbound (string): SPDX ID for an outbound license, e.g. the license used for distribution of an application
        inbound (string): SPDX ID for an inbound license, e.g. the license used for a dependency of the application

    Returns:
        [OSADLCompatibility]: Either yes, no, unknown or undefined

    """
    __read_db(customdb=customdb)
    try:
        return OSADLCompatibility.from_text(__osadl_db.get(outbound).get(inbound))
    except AttributeError:
        return OSADLCompatibility.UNDEF


def supported_licenses(customdb=None):
    """returns the supported licenses (i.e. which licenses for which
    there is a known compatibility status).
    """
    __read_db(customdb=customdb)
    return __osadl_db.keys()
