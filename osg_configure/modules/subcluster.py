import re
import ConfigParser

from osg_configure.modules.resourcecatalog import ResourceCatalog
from osg_configure.modules import exceptions
from osg_configure.modules import utilities


REQUIRED = "required"
OPTIONAL = "optional"

STRING = "str"
POSITIVE_INT = "positive int"
POSITIVE_FLOAT = "positive float"
LIST = "list"
BOOLEAN = "boolean"

ENTRIES = {
   "name": (REQUIRED, STRING),
   "cpu_vendor": (REQUIRED, STRING),
   "cpu_model": (REQUIRED, STRING),
   "cores_per_node": (REQUIRED, POSITIVE_INT),
   "node_count": (REQUIRED, POSITIVE_INT),
   "cpus_per_node": (REQUIRED, POSITIVE_INT),
   "cpu_speed_mhz": (REQUIRED, POSITIVE_FLOAT),
   "ram_mb": (REQUIRED, POSITIVE_INT),
   "swap_mb": (OPTIONAL, POSITIVE_INT),
   "SI00": (OPTIONAL, POSITIVE_FLOAT),
   "HEPSPEC": (OPTIONAL, POSITIVE_FLOAT),
   "SF00": (OPTIONAL, POSITIVE_FLOAT),
   "inbound_network": (REQUIRED, BOOLEAN),
   "outbound_network": (REQUIRED, BOOLEAN),
   "cpu_platform": (REQUIRED, STRING),
   "allowed_vos": (OPTIONAL, STRING),
}

BANNED_ENTRIES = {
   "name": "SUBCLUSTER_NAME",
   "node_count": "NUMBER_OF_NODE",
   "ram_mb": "MB_OF_RAM",
   "cpu_model": "CPU_MODEL_FROM_/proc/cpuinfo",
   "cpu_vendor": "VENDOR_AMD_OR_INTEL",
   "cpu_speed_mhz": "CLOCK_SPEED_MHZ",
   "cpu_platform": "x86_64_OR_i686",
   "cpus_per_node": "#_PHYSICAL_CHIPS_PER_NODE",
   "cores_per_node": "#_CORES_PER_NODE",
}

ENTRY_RANGES = {
  'SF00': (500, 5000),
  'SI00': (500, 5000),
  'HEPSPEC': (2, 50),
  'ram_mb': (500, 102400),
  'swap_mb': (500, 102400),
  'cpus_per_node': (1, 128),
  'cores_per_node': (1, 256),
}


def check_entry(config, section, option, status, kind):
  """
  Check entries to make sure that they conform to the correct range of values
  """
  entry = None
  try:
    entry = str(config.get(section, option)).strip()
  except (ConfigParser.NoSectionError, ConfigParser.NoOptionError, ConfigParser.InterpolationError):
    pass
  if not entry and status == REQUIRED:
    raise exceptions.SettingError("Can't get value for mandatory setting %s in section %s." %\
                                  (option, section))
  elif not entry and status == OPTIONAL:
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
  if section.lower().find('changeme') >= 0:
    msg = "You have a section named 'Subcluster CHANGEME', you must change this name.\n"
    msg += "'Subcluster Main' is an example"
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
    if not section.lower().startswith('subcluster'):
      continue
    has_sc = True
    check_section(config, section)
  return has_sc


def resource_catalog_from_config(config):
  """
  Create a ResourceCatalog from the subcluster entries in a config
  :type config: ConfigParser.ConfigParser
  :rtype: ResourceCatalog
  """
  assert isinstance(config, ConfigParser.ConfigParser)
  rc = ResourceCatalog()
  for section in config.sections():
    if section.lower().startswith('subcluster'):
      check_section(config, section)
      name = config.get(section, 'name')
      cpus = config.getint(section, 'cores_per_node')
      memory = config.getint(section, 'ram_mb')
      allowed_vos = utilities.config_safe_get(config, section, 'allowed_vos')
      rc.add_entry(name=name,
                   cpus=cpus,
                   memory=memory,
                   allowed_vos=allowed_vos)
  return rc
