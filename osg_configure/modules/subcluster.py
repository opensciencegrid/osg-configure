import logging
import re
from typing import Optional
from configparser import NoSectionError, NoOptionError, InterpolationError, ConfigParser

from osg_configure.modules import exceptions
from osg_configure.modules import utilities

REQUIRED = "required"
REQUIRED_FOR_SUBCLUSTER = "required for subcluster"
REQUIRED_FOR_RESOURCE_ENTRY = "required for resource entry"
REQUIRED_FOR_PILOT = "required for pilot"
OPTIONAL = "optional"

STRING = "str"
POSITIVE_INT = "positive int"
POSITIVE_FLOAT = "positive float"
LIST = "list"
BOOLEAN = "boolean"

ENTRIES = {
    "name":                (OPTIONAL, STRING),
    "cores_per_node":      (OPTIONAL, POSITIVE_INT),  # also used by resource entry
    "ram_mb":              (OPTIONAL, POSITIVE_INT),  # also used by resource entry and pilot
    "allowed_vos":         (OPTIONAL, STRING),
    "max_wall_time":       (OPTIONAL, POSITIVE_INT),
    "extra_transforms":    (OPTIONAL, STRING),
    # added for Resource Entries
    "cpucount":            (OPTIONAL, POSITIVE_INT),  # alias for cores_per_node, also used by pilots
    "maxmemory":           (OPTIONAL, POSITIVE_INT),  # alias for ram_mb
    "queue":               (REQUIRED_FOR_RESOURCE_ENTRY, STRING),  # also used by pilots
    "subclusters":         (OPTIONAL, LIST),
    "vo_tag":              (OPTIONAL, STRING),
    # added for Pilots
    "gpucount":            (OPTIONAL, POSITIVE_INT),
    "max_pilots":          (REQUIRED_FOR_PILOT, POSITIVE_INT),
    "os":                  (OPTIONAL, STRING),
    "require_singularity": (OPTIONAL, BOOLEAN),
    "send_tests":          (OPTIONAL, BOOLEAN),
    "whole_node":          (OPTIONAL, BOOLEAN),
    # only used in BDII
    "cpu_model":           (OPTIONAL, STRING),
    "cpu_platform":        (OPTIONAL, STRING),
    "cpu_speed_mhz":       (OPTIONAL, POSITIVE_FLOAT),
    "cpu_vendor":          (OPTIONAL, STRING),
    "cpus_per_node":       (OPTIONAL, POSITIVE_INT),
    "inbound_network":     (OPTIONAL, BOOLEAN),
    "node_count":          (OPTIONAL, POSITIVE_INT),
    "outbound_network":    (OPTIONAL, BOOLEAN),
    # other optional attributes
    "HEPSPEC":          (OPTIONAL, POSITIVE_FLOAT),
    "SF00":             (OPTIONAL, POSITIVE_FLOAT),
    "SI00":             (OPTIONAL, POSITIVE_FLOAT),
    "swap_mb":          (OPTIONAL, POSITIVE_INT),
    ## uncomment this if somebody really asks for this feature
    # "extra_requirements": (OPTIONAL, STRING),
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

CPUCOUNT_DEFAULT = 1
RAM_MB_DEFAULT = 2500

log = logging.getLogger(__name__)


def is_subcluster(section: str) -> bool:
    return section.lstrip().lower().startswith("subcluster")


def is_resource_entry(section: str) -> bool:
    return section.lstrip().lower().startswith("resource entry")


def is_pilot(section: str) -> bool:
    return section.lstrip().lower().startswith("pilot")


def check_entry(config, section, option, status, kind):
    """
    Check entries to make sure that they conform to the correct range of values
    """
    entry = None
    try:
        entry = str(config.get(section, option)).strip()
    except (NoSectionError, NoOptionError, InterpolationError):
        pass
    if not entry:
        if (status == REQUIRED
                or (status == REQUIRED_FOR_SUBCLUSTER and is_subcluster(section))
                or (status == REQUIRED_FOR_RESOURCE_ENTRY and is_resource_entry(section))
                or (status == REQUIRED_FOR_PILOT and is_pilot(section))):

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
                                          "`%s` should be a non-negative integer, but it is `%s`" % \
                                          (option, section, entry))
        return entry
    elif kind == POSITIVE_FLOAT:
        try:
            entry = float(entry)
            if entry < 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise exceptions.SettingError("Value of option `%s` in section " \
                                          "`%s` should be a non-negative float, but it is `%s`" % \
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
        return utilities.split_comma_separated_list(entry)

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
                raise exceptions.SettingError(msg)
        except KeyError:
            pass

    # Special case: Pilot sections either need "os" specified or "require_singularity=true"
    if is_pilot(section):
        require_singularity = utilities.config_safe_getboolean(config, section, "require_singularity", True)
        os = utilities.config_safe_get(config, section, "os", None)

        if not require_singularity and not os:
            msg = "'os' must be specified in section %s if 'require_singularity' is false" % section
            raise exceptions.SettingError(msg)


def check_config(config: ConfigParser) -> bool:
    """
    Check all subcluster definitions in an entire config
    :return: True if there are any subcluster definitions, False otherwise
    """
    has_sc = False
    for section in config.sections():
        if is_pilot(section) or is_subcluster(section) or is_resource_entry(section):
            has_sc = True
            check_section(config, section)
    return has_sc


def rce_section_get_name(config: ConfigParser, section: str) -> Optional[str]:
    """Return the name of a Subcluster/Resource Entry/Pilot

    If the `name` attribute is present, use that; otherwise, use the section name,
    so `[Subcluster red.unl.edu]` gives the name `red.unl.edu`.

    Returns None if the section is not a Subcluster/Resource Entry/Pilot section.
    """
    m = re.search(r"(?i:subcluster|resource entry|pilot)\s+(.+)", section)
    if not m:
        return
    default_name = m.group(1)
    return config[section].get("name", default_name).strip()


class ResourceCatalog:  # forward declaration for type checking
    def compose_text(self) -> str:
        pass


def resource_catalog_from_config(config: ConfigParser, default_allowed_vos: str = None) -> ResourceCatalog:
    """
    Create a ResourceCatalog from the subcluster entries in a config
    :param default_allowed_vos: The allowed_vos to use if the user specified "*"
    """
    logger = logging.getLogger(__name__)
    assert isinstance(config, ConfigParser)
    from osg_configure.modules.resourcecatalog import ResourceCatalog, RCEntry

    def safeget(option: str, default=None) -> str:
        return utilities.config_safe_get(config, section, option, default)

    def safegetbool(option: str, default=None) -> bool:
        return utilities.config_safe_getboolean(config, section, option, default)

    rc = ResourceCatalog()

    # list of section names of all subcluster sections
    subcluster_sections = [section for section in config.sections() if is_subcluster(section)]
    subcluster_names = [rce_section_get_name(config, section) for section in subcluster_sections]

    sections_without_max_wall_time = []
    for section in config.sections():
        if not (is_subcluster(section) or is_resource_entry(section) or is_pilot(section)):
            continue

        check_section(config, section)

        rcentry = RCEntry()
        rcentry.name = rce_section_get_name(config, section)

        rcentry.cpus = (
                safeget("cpucount") or
                safeget("cores_per_node") or
                CPUCOUNT_DEFAULT
        )
        rcentry.cpus = int(rcentry.cpus)

        rcentry.memory = (
                safeget("maxmemory") or
                safeget("ram_mb") or
                RAM_MB_DEFAULT
        )
        rcentry.memory = int(rcentry.memory)

        rcentry.allowed_vos = utilities.split_comma_separated_list(safeget("allowed_vos", default="").strip())
        if not rcentry.allowed_vos or not rcentry.allowed_vos[0]:
            logger.error("No allowed_vos specified for section '%s'."
                         "\nThe factory will not send jobs to these subclusters/resources. Specify the allowed_vos"
                         "\nattribute as either a list of VOs, or a '*' to use an autodetected VO list based on"
                         "\nthe user accounts available on your CE." % section)
            raise exceptions.SettingError("No allowed_vos for %s" % section)
        if rcentry.allowed_vos == ["*"]:
            if default_allowed_vos:
                rcentry.allowed_vos = default_allowed_vos
            else:
                rcentry.allowed_vos = []

        max_wall_time = safeget("max_wall_time")
        if not max_wall_time:
            rcentry.max_wall_time = 1440
            sections_without_max_wall_time.append(section)
        else:
            rcentry.max_wall_time = max_wall_time.strip()
        rcentry.queue = safeget("queue")

        scs = utilities.split_comma_separated_list(safeget("subclusters", ""))
        if scs:
            for sc in scs:
                if sc not in subcluster_names:
                    raise exceptions.SettingError("Undefined subcluster '%s' mentioned in section '%s'" % (sc, section))
            rcentry.subclusters = scs
        else:
            rcentry.subclusters = None

        rcentry.vo_tag = safeget("vo_tag")

        # The ability to specify extra requirements is disabled until admins demand it
        # rcentry.extra_requirements = utilities.config_safe_get(config, section, 'extra_requirements')
        rcentry.extra_requirements = None
        rcentry.extra_transforms = safeget("extra_transforms")

        rcentry.gpus = safeget("gpucount")
        if is_pilot(section):
            rcentry.max_pilots = safeget("max_pilots")
            rcentry.whole_node = safegetbool("whole_node", False)
            if rcentry.whole_node:
                rcentry.cpus = None
                rcentry.memory = None
            rcentry.require_singularity = safegetbool("require_singularity", True)
            rcentry.os = safeget("os")
            rcentry.send_tests = safegetbool("send_tests", True)

        rc.add_rcentry(rcentry)
    # end for section in config.sections()

    if sections_without_max_wall_time:
        logger.warning("No max_wall_time specified for some sections; defaulting to 1440."
                       "\nAdd 'max_wall_time=1440' to the following section(s) to clear this warning:"
                       "\n'%s'" % "', '".join(sections_without_max_wall_time))

    return rc
