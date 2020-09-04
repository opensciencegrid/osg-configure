#!/usr/bin/env python
import errno
import fnmatch
import pwd
import re
import sys
import logging

from collections import namedtuple


DEFAULT_VOMS_MAPFILE = "/usr/share/osg/voms-mapfile-default"
VOMS_MAPFILE = " /etc/grid-security/voms-mapfile "
BAN_MAPFILE = "/etc/grid-security/ban-voms-mapfile"


class Mapping(namedtuple('Mapping', 'pattern user')):
    """Pairs of VOMS attrib patterns and Unix users"""
    __slots__ = ()


def read_mapfiles():
    """Get the VO pattern -> username mappings from the VOMS mapfiles, if they exist
    
    :return: List of Mappings
    """
    mappings = []

    # matches stuff like
    #   "/GLOW/*" glow
    #   "/cms/Role=pilot/Capability=NULL" cmspilot
    # and extracts the stuff between the quotes, and the username in the second field
    regex = re.compile(r'^\s*["](/[^"]+)["]\s+([A-Za-z0-9_]+)\s*(?:$|[#])')
    for filepath in [DEFAULT_VOMS_MAPFILE, VOMS_MAPFILE]:
        try:
            with open(filepath, "r", encoding="latin-1") as filehandle:
                for line in filehandle:
                    match = regex.match(line)
                    if not match:
                        continue
                    else:
                        mappings.append(Mapping(match.group(1), match.group(2)))
        except EnvironmentError as err:
            if err.errno == errno.ENOENT:
                continue
            else:
                raise

    return mappings


def read_banfile():
    """Get the banned VOMS attrib patterns
    
    :return: List of banned patterns
    """
    # matches stuff like
    #    "/GLOW/*"
    # and extracts the stuff between the quotes
    regex = re.compile(r'^\s*["](/[^"]+)["]\s*(?:$|[#])')
    bans = []

    try:
        with open(BAN_MAPFILE, "r", encoding="latin-1") as filehandle:
            for line in filehandle:
                match = regex.match(line)
                if not match:
                    continue
                else:
                    bans.append(match.group(1))
    except EnvironmentError as err:
        if err.errno == errno.ENOENT:
            logging.getLogger(__name__).warning("%s not found - all mappings might fail!", BAN_MAPFILE)
        else:
            raise

    return bans


def filter_out_bans(mappings, bans):
    """Get a list of mappings minus any that match the patterns in ``bans``
    
    :return: List of Mappings
    """
    new_mappings = []
    for mapping in mappings:
        for ban in bans:
            if fnmatch.fnmatch(mapping.pattern, ban):
                break
        else:
            new_mappings.append(mapping)
    return new_mappings


def filter_by_existing_users(mappings):
    """Get a list of mappings minus any that do not have corresponding Unix users
    
    :return: List of Mappings
    """
    usernames = [x[0] for x in pwd.getpwall()]
    new_mappings = [mapping for mapping in mappings if mapping.user in usernames]
    return new_mappings


def get_vos(mappings):
    """Get the VOs from a list of mappings (assumption is that the first VO group in the pattern matches the VO name)

    :return: Set of VOs
    """
    regex = re.compile("^/(\w+)/")
    patterns = (m.pattern for m in mappings)
    matches = filter(None, (regex.match(p) for p in patterns))
    vo_groups = set(m.group(1).lower() for m in matches)

    return vo_groups


def get_allowed_vos():
    """Get a set of all the VOs that might be allowed on this site (based on voms-mapfiles and Unix users on the CE)
    :return: Set of VOs
    """
    return get_vos(filter_by_existing_users(filter_out_bans(read_mapfiles(), read_banfile())))


def main(*args):
    """main function for testing"""
    logging.basicConfig(level=logging.WARNING)
    print(get_allowed_vos())
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
