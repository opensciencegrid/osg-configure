import logging
import re
from configparser import NoSectionError, NoOptionError, InterpolationError, ConfigParser

from osg_configure.modules import exceptions
from osg_configure.modules import utilities

REQUIRED = "required"
REQUIRED_FOR_SUBCLUSTER = "required for subcluster"
REQUIRED_FOR_RESOURCE_ENTRY = "required for resource entry"
OPTIONAL = "optional"

STRING = "str"
POSITIVE_INT = "positive int"
POSITIVE_FLOAT = "positive float"
LIST = "list"
BOOLEAN = "boolean"

ENTRIES = {
    "name": (REQUIRED, STRING),
    "cpu_vendor": (OPTIONAL, STRING),
    "cpu_model": (OPTIONAL, STRING),
    "cores_per_node": (REQUIRED_FOR_SUBCLUSTER, POSITIVE_INT), # also used by resource entry
    "cpucount": (OPTIONAL, POSITIVE_INT), # alias for cores_per_node
    "node_count": (OPTIONAL, POSITIVE_INT),
    "cpus_per_node": (OPTIONAL, POSITIVE_INT),
    "cpu_speed_mhz": (OPTIONAL, POSITIVE_FLOAT),
    "ram_mb": (REQUIRED_FOR_SUBCLUSTER, POSITIVE_INT), # also used by resource entry
    "maxmemory": (OPTIONAL, POSITIVE_INT), # alias for ram_mb
    "swap_mb": (OPTIONAL, POSITIVE_INT),
    "SI00": (OPTIONAL, POSITIVE_FLOAT),
    "HEPSPEC": (OPTIONAL, POSITIVE_FLOAT),
    "SF00": (OPTIONAL, POSITIVE_FLOAT),
    "inbound_network": (OPTIONAL, BOOLEAN),
    "outbound_network": (OPTIONAL, BOOLEAN),
    "cpu_platform": (OPTIONAL, STRING),
    "allowed_vos": (OPTIONAL, STRING),
    "max_wall_time": (OPTIONAL, POSITIVE_INT),
    "extra_requirements": (OPTIONAL, STRING),
    "extra_transforms": (OPTIONAL, STRING),
    "queue": (REQUIRED_FOR_RESOURCE_ENTRY, STRING),
    "subclusters": (OPTIONAL, LIST),
    "vo_tag": (OPTIONAL, STRING),
}

BANNED_ENTRIES = {
    "name": "SUBCLUSTER_NAME",
    "ram_mb": "MB_OF_RAM",
    "maxmemory": "MAX_MB_OF_RAM_ALLOCATED_TO_JOB",
    "cores_per_node": "#_CORES_PER_NODE",
    "cpucount": "CPUS_ALLOCATED_TO_JOB",
    "max_wall_time": "MAX_MINUTES_OF_RUNTIME",
    "queue": "CHANGEME",
}

ENTRY_RANGES = {
    'ram_mb': (512, 8388608),
    'maxmemory': (512, 8388608),
    'cores_per_node': (1, 8192),
    'cpucount': (1, 8192),
}


def check_entry(config, section, option, status, kind):
    """
    Check entries to make sure that they conform to the correct range of values
    """
    entry = None
    try:
        entry = str(config.get(section, option)).strip()
    except (NoSectionError, NoOptionError, InterpolationError):
        pass
    is_subcluster = section.lower().startswith('subcluster')
    if not entry:
        if (status == REQUIRED
            or (status == REQUIRED_FOR_SUBCLUSTER and is_subcluster)
            or (status == REQUIRED_FOR_RESOURCE_ENTRY and not is_subcluster)):
            raise exceptions.SettingError("Can't get value for mandatory setting %s in section %s." % \
                                          (option, section))
        else:
            return None
    if kind == STRING:
        # No parsing we can do for strings.
        return entry
    elif kind == POSITIVE_INT:
        try:
            entry = int(entry)
            if entry < 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise exceptions.SettingError("Value of option `%s` in section " \
                                          "`%s` should be a positive integer, but it is `%s`" % \
                                          (option, section, entry))
        return entry
    elif kind == POSITIVE_FLOAT:
        try:
            entry = float(entry)
            if entry < 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise exceptions.SettingError("Value of option `%s` in section " \
                                          "`%s` should be a positive float, but it is `%s`" % \
                                          (option, section, entry))
        return entry
    elif kind == BOOLEAN:
        entry = entry.lower()
        possible_vals = ['t', 'true', 'yes', 'y', 'enable', 'enabled', 'f',
                         'false', 'no', 'n', 'disable', 'disabled']
        positive_vals = ['t', 'true', 'yes', 'y', 'enable', 'enabled']
        if entry not in possible_vals:
            raise exceptions.SettingError("Value of option `%s` in section " \
                                          "`%s` should be a boolean, but it is `%s`" % (option,
                                                                                        section,
                                                                                        entry))
        return entry in positive_vals
    elif kind == LIST:
        regex = re.compile(r'\s*,*\s*')
        entry = regex.split(entry)
        return entry

    else:
        # Kind of entry isn't known... OK for now.
        return entry


def check_section(config, section):
    """
    Check attributes related to a subcluster and make sure that they are consistent
    """
    if "changeme" in section.lower():
        msg = "You have a section named '%s', you must change this name.\n" % section
        raise exceptions.SettingError(msg)

    for option, value in ENTRIES.items():
        status, kind = value
        entry = check_entry(config, section, option, status, kind)
        if option in BANNED_ENTRIES and entry == BANNED_ENTRIES[option]:
            raise exceptions.SettingError("Value for %s in section %s is " \
                                          "a default or banned entry (%s); " \
                                          "you must change this value." % \
                                          (option, section, BANNED_ENTRIES[option]))
        if entry is None:
            continue

        try:
            range_min, range_max = ENTRY_RANGES[option]

            if not (range_min <= entry <= range_max):
                msg = ("Value for %(option)s in section %(section)s is outside allowed range"
                       ", %(range_min)d-%(range_max)d" % locals())
                if option == 'HEPSPEC':
                    msg += '.  The conversion factor from HEPSPEC to SI2K is 250'
                raise exceptions.SettingError(msg)
        except KeyError:
            pass


def check_config(config):
    """
    Check all subcluster definitions in an entire config
    :type config: ConfigParser.ConfigParser
    :return: True if there are any subcluster definitions, False otherwise
    """
    has_sc = False
    for section in config.sections():
        lsection = section.lower()
        if not (lsection.startswith('subcluster') or lsection.startswith('resource entry')):
            continue
        has_sc = True
        check_section(config, section)
    return has_sc


def resource_catalog_from_config(config: ConfigParser, default_allowed_vos=None):
    """
    Create a ResourceCatalog from the subcluster entries in a config
    :type config: ConfigParser
    :rtype: resourcecatalog.ResourceCatalog
    """
    logger = logging.getLogger(__name__)
    assert isinstance(config, ConfigParser)
    from osg_configure.modules import resourcecatalog

    rc = resourcecatalog.ResourceCatalog()

    # list of section names of all subcluster sections
    subcluster_sections = [section for section in config.sections() if section.lower().startswith('subcluster')]
    subcluster_names = [config.get(section, 'name').strip() for section in subcluster_sections]

    sections_without_max_wall_time = []
    for section in config.sections():
        lsection = section.lower()
        if not (lsection.startswith('subcluster') or lsection.startswith('resource entry')):
            continue

        check_section(config, section)

        rcentry = resourcecatalog.RCEntry()
        rcentry.name = config.get(section, 'name')

        rcentry.cpus = utilities.config_safe_get(config, section, 'cpucount') or \
                       utilities.config_safe_get(config, section, 'cores_per_node')
        if not rcentry.cpus:
            raise exceptions.SettingError("cpucount / cores_per_node not found in section %s" % section)
        rcentry.cpus = int(rcentry.cpus)

        rcentry.memory = utilities.config_safe_get(config, section, 'maxmemory') or \
                         utilities.config_safe_get(config, section, 'ram_mb')
        if not rcentry.memory:
            raise exceptions.SettingError("maxmemory / ram_mb not found in section %s" % section)
        rcentry.memory = int(rcentry.memory)

        rcentry.allowed_vos = utilities.config_safe_get(config, section, 'allowed_vos', default="").strip()
        if not rcentry.allowed_vos:
            logger.error("No allowed_vos specified for section '%s'."
                         "\nThe factory will not send jobs to these subclusters/resources. Specify the allowed_vos"
                         "\nattribute as either a list of VOs, or a '*' to use an autodetected VO list based on"
                         "\nthe user accounts available on your CE." % section)
            raise exceptions.SettingError("No allowed_vos for %s" % section)
        if rcentry.allowed_vos == "*":
            if default_allowed_vos:
                rcentry.allowed_vos = default_allowed_vos
            else:
                rcentry.allowed_vos = None

        max_wall_time = utilities.config_safe_get(config, section, 'max_wall_time')
        if not max_wall_time:
            rcentry.max_wall_time = 1440
            sections_without_max_wall_time.append(section)
        else:
            rcentry.max_wall_time = max_wall_time.strip()
        rcentry.queue = utilities.config_safe_get(config, section, 'queue')

        scs = utilities.config_safe_get(config, section, 'subclusters')
        if scs:
            scs = re.split(r'\s*,\s*', scs)
            for sc in scs:
                if sc not in subcluster_names:
                    raise exceptions.SettingError("Undefined subcluster '%s' mentioned in section '%s'" % (sc, section))
        rcentry.subclusters = scs

        rcentry.vo_tag = utilities.config_safe_get(config, section, 'vo_tag')

        # The ability to specify extra requirements is disabled until admins demand it
        # rcentry.extra_requirements = utilities.config_safe_get(config, section, 'extra_requirements')
        rcentry.extra_requirements = None
        rcentry.extra_transforms = utilities.config_safe_get(config, section, 'extra_transforms')

        rc.add_rcentry(rcentry)
    # end for section in config.sections()

    if sections_without_max_wall_time:
        logger.warning("No max_wall_time specified for some sections; defaulting to 1440."
                       "\nAdd 'max_wall_time=1440' to the following section(s) to clear this warning:"
                       "\n'%s'" % "', '".join(sections_without_max_wall_time))

    return rc
