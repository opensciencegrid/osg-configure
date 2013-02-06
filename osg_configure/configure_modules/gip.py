"""Class for verifying gip information"""

import os
import re
import pwd
import logging

from osg_configure.modules import exceptions
from osg_configure.modules.configurationbase import BaseConfiguration
from osg_configure.modules import utilities
from osg_configure.modules import validation

__all__ = ['GipConfiguration']

REQUIRED = "required"
OPTIONAL = "optional"

STRING = "str"
POSITIVE_INT = "positive int"
POSITIVE_FLOAT = "positive float"
LIST = "list"
BOOLEAN = "boolean"

OSG_ENTRIES = { \
   "Site Information": ["host_name", "site_name", "sponsor", "site_policy",
                        "contact", "email", "city", "longitude", "latitude"],
   "Storage": ["app_dir", "data_dir", "worker_node_temp"],
}

SC_ENTRIES = { \
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
}

SC_BANNED_ENTRIES = { \
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


SE_ENTRIES = { \
   "name": (REQUIRED, STRING),
   "unique_name": (OPTIONAL, STRING),
   "srm_endpoint": (REQUIRED, STRING),
   "srm_version": (OPTIONAL, STRING),
   "transfer_endpoints": (OPTIONAL, STRING),
   "provider_implementation": (OPTIONAL, STRING),
   "implementation": (REQUIRED, STRING),
   "version": (REQUIRED, STRING),
   "default_path": (REQUIRED, STRING),
   "allowed_vos": (OPTIONAL, LIST),
   "mount_point": (OPTIONAL, LIST),
}

SE_BANNED_ENTRIES = { \
   "name": "SE_CHANGEME",
   "srm_endpoint" : "httpg://srm.example.com:8443/srm/v2/server",
}

# Error messages
mount_point_error = """\
You have enabled the mount_point option, but your input, %(input)s, is invalid
because of:
%(reason)s

mount_point should be enabled for sites where the SE is mounted on the worker
nodes and provides a POSIX-like interface (POSIX-like includes Lustre, HDFS,
XrootDFS, but not dCache PNFS).
The value of `mount_point` should be two paths; first, the path where the
file system is mounted on the worker nodes, followed by the exported directory
of the file system.  If you mount your file system on the worker nodes with
the following command:
  $ mount -t nfs nfs.example.com:/exported/dir /mnt/nfs
then mount_point should look like this:
   mount_point = /mnt/nfs,/exported/dir

Paths are lightly validated; they must start with "/" and contain alphanumeric
characters plus "-" or "_".
"""

class GipConfiguration(BaseConfiguration):
  """
  Class to handle attributes related to GIP.
  """
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(GipConfiguration, self).__init__(*args, **kwargs)
    self.log('GipConfiguration.__init__ started')
    self.config_section = "GIP"
    self.vo_dir = "VONAME"  # default to allowing substitution in vo_dir
    self._valid_batch_opt = ['pbs',
                             'lsf',
                             'condor',
                             'sge',
                             'slurm',
                             'forwarding']
    self.gip_user = 'tomcat'
    self.log('GipConfiguration.__init__ completed')
    
  def _check_entry(self, config, section, option, status, kind):
    """
    Check entries to make sure that they conform to the correct range of values 
    """
    self.log('GipConfiguration._check_entry started')
    has_entry = True
    try:
      entry = config.get(section, option)
    # pylint: disable-msg=W0703
    except Exception:
      has_entry = False
    if not has_entry and status == REQUIRED:
      self.log("Mandatory setting %s in section %s not found." % \
                        (option, section))
      raise exceptions.SettingError("Can't get value for %s in section %s." %\
                                    (option, section))
    elif not has_entry and status == OPTIONAL:
      self.log('GipConfiguration._check_entry completed')
      return None
    if kind == STRING:
      # No parsing we can do for strings.
      self.log('GipConfiguration._check_entry completed')
      return entry
    elif kind == POSITIVE_INT:
      try:
        entry = int(entry)
        if entry < 0:
          raise ValueError()
      except:
        raise exceptions.SettingError("Value of option `%s` in section " \
                                      "`%s` should be a positive integer, but it is `%s`" % \
                                      (option, section, entry))
      self.log('GipConfiguration._check_entry completed')
      return entry
    elif kind == POSITIVE_FLOAT:
      try:
        entry = float(entry)
        if entry < 0:
          raise ValueError()
      except:
        raise exceptions.SettingError("Value of option `%s` in section " \
                                      "`%s` should be a positive float, but it is `%s`" % \
                                      (option, section, entry))
      self.log('GipConfiguration._check_entry completed')
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
      self.log('GipConfiguration._check_entry completed')
      return entry in positive_vals
    elif kind == LIST:
      regex = re.compile('\s*,*\s*')
      entry = regex.split(entry)
      self.log('GipConfiguration._check_entry completed')
      return entry

    else:
      # Kind of entry isn't known... OK for now.
      self.log('GipConfiguration._check_entry completed')
      return entry

  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser
    object given by configuration and write recognized settings to attributes
    dict
    """
    self.log('GipConfiguration.parseConfiguration started')

    if not utilities.ce_installed():
      self.log('Not a CE configuration, disabling GIP')
      self.log('GipConfiguration.parseConfiguration completed')
      self.enabled = False
      return
    else:
      self.enabled = True
    
    self.checkConfig(configuration)

    if configuration.has_option(self.config_section, 'batch'):
      batch_opt = configuration.get(self.config_section, 'batch').lower()
      if (not utilities.blank(batch_opt) and
          batch_opt not in self._valid_batch_opt):        
        msg = "The batch setting in %s must be a valid option " \
              "(e.g. %s), %s was given" % (self.config_section, 
                                           ",".join(self._valid_batch_opt),
                                           batch_opt)
        self.log(msg, level = logging.ERROR)
        raise exceptions.SettingError(msg)
    
    has_sc = False
    for section in configuration.sections():
      if not section.lower().startswith('subcluster'):
        continue
      has_sc = True
      self.checkSC(configuration, section)
    if not has_sc:
      try:
        self._check_entry(configuration, "GIP", "sc_number", REQUIRED,
                          POSITIVE_INT)
      except:
        msg = "There is no `subcluster` section and the old-style subcluster" + \
              "setup in GIP is not configured. " + \
              " Please see the configuration documentation."
        raise exceptions.SettingError(msg)

    # Check for the presence of the classic SE
    has_classic_se = True
    try:
      has_classic_se = configuration.getboolean("GIP", "advertise_gsiftp")
    # pylint: disable-msg=W0702
    # pylint: disable-msg=W0703
    # pylint: disable-msg=W0704
    except Exception:
      pass

    has_se = False
    for section in configuration.sections():
      if not section.lower().startswith('se'):
        continue
      has_se = True
      self.checkSE(configuration, section)
    if not has_se and not has_classic_se:
      try:
        self._check_entry(configuration, "GIP", "se_name", REQUIRED, STRING)
      except:
        msg = "There is no `SE` section, the old-style SE" + \
              "setup in GIP is not configured, and there is no classic SE. " + \
              " At least one must be configured.  Please see the configuration"\
              " documentation."
        raise exceptions.SettingError(msg)
    
    if configuration.has_option(self.config_section, 'user'):
      username = configuration.get(self.config_section, 'user')
      if not validation.valid_user(username):
        err_msg = "%s is not a valid account on this system" % username
        self.log(err_msg,
                 section = self.config_section,
                 option = 'user',
                 level = logging.ERROR)
        raise exceptions.SettingError(err_msg)
      self.gip_user = username
    self.log('GipConfiguration.parseConfiguration completed')

  def checkSC(self, config, section):
    """
    Check attributes related to a SE and make sure that they are consistent
    """
    self.log('GipConfiguration.checkSC started')
    attributes_ok = True
    if section.lower().find('changeme') >= 0:
      msg = "You have a section named 'Subcluster CHANGEME', you must change this name.\n"
      msg += "'Subcluster Main' is an example"
      raise exceptions.SettingError(msg)
    
    for option, value in SC_ENTRIES.items():
      status, kind = value
      entry = self._check_entry(config, section, option, status, kind)
      if option in SC_BANNED_ENTRIES and entry == SC_BANNED_ENTRIES[option]:
        raise exceptions.SettingError("Value for %s in section %s is " \
                                      "a default or banned entry (%s); " \
                                      "you must change this value." % \
                                      (option, section, SC_BANNED_ENTRIES[option]))      
      if entry == None:
        continue
      if (option in ['SF00', 'SI00'] ) and \
         (entry < 500 or entry > 5000):
        raise exceptions.SettingError("Value for %s in section %s is " \
                                      "outside allowed range, 500-5000" % 
                                      (option, section))
      elif option == 'HEPSPEC' and (entry < 2 or entry > 50):
        raise exceptions.SettingError("Value for %s in section %s is " \
          "outside allowed range, 2-50.  The conversion factor from HEPSPEC"
          " to SI2K is 250." % (option, section))
      elif (option in ['ram_mb', 'swap_mb'] ) and \
           (entry < 500 or entry > 128000):
        raise exceptions.SettingError("Value for %s in section %s is " \
                                      "outside allowed range, 500-128000" % 
                                      (option, section))
      if (option in ['cpus_per_node', 'cores_per_node'] ) and \
         (entry < 1 or entry > 32):
        raise exceptions.SettingError("Value for %s in section %s, %s, is" \
                                      " outside allowed range, 1-32" % 
                                      (option, section, entry))
    self.log('GipConfiguration.checkSC completed')
    return attributes_ok
    
  def checkSE(self, config, section):
    """
    Check attributes currently stored and make sure that they are consistent
    """
    self.log('GipConfiguration.checkSE started')
    attributes_ok = True

    enabled = True
    try:
      if config.has_option(section, 'enabled'):
        enabled = config.getboolean(section, 'enabled')
    # pylint: disable-msg=W0703
    except Exception:
      enabled = False
      
    if not enabled:
      # if section is disabled, we can exit
      return attributes_ok
    
    if section.lower().find('changeme') >= 0:
      msg = "You have a section named 'SE CHANGEME', but it is not turned off.\n"
      msg += "'SE CHANGEME' is an example; you must change it if it is enabled."
      raise exceptions.SettingError(msg)

    for option, value in SE_ENTRIES.items():
      status, kind = value
      entry = self._check_entry(config, section, option, status, kind)
      if option in SE_BANNED_ENTRIES and entry == SE_BANNED_ENTRIES[option]:
        raise exceptions.SettingError("Value for %s in section %s is " \
                                      "a default or banned entry (%s); " \
                                      "you must change this value." % \
                                      (option, section, SE_BANNED_ENTRIES[option]))
      if entry == None:
        continue

      # Validate the mount point information
      if option == 'mount_point':
        regex = re.compile("/(/*[A-Za-z0-9_\-]/*)*$")
        err_info = {'input': value}
        if len(entry) != 2:
          err_info['reason'] = "Only one path was specified!"
          msg = mount_point_error % err_info
          raise exceptions.SettingError(msg)
        if not regex.match(entry[0]):
          err_info['reason'] = "First path does not pass validation"
          msg = mount_point_error % err_info
          raise exceptions.SettingError(msg)
        if not regex.match(entry[1]):
          err_info['reason'] = "Second path does not pass validation"
          msg = mount_point_error % err_info
          raise exceptions.SettingError(msg)

      if option == 'srm_endpoint':
        regex = re.compile('([A-Za-z]+)://([A-Za-z0-9_\-.]+):([0-9]+)/(.+)')
        match = regex.match(entry)
        if not match or match.groups()[3].find('?SFN=') >= 0:
          msg = "Given SRM endpoint is not valid! It must be of the form " + \
                "srm://<hostname>:<port>/<path>.  The hostname, port, and path " + \
                "must be present.  The path should not contain the string '?SFN='"
          raise exceptions.SettingError(msg)
      elif option == 'allowed_vos':
        user_vo_map = None
        if config.has_option('Install Locations', 'user_vo_map'):
          user_vo_map = config.get('Install Locations', 'user_vo_map')
        vo_list = utilities.get_vos(user_vo_map)
        for vo in entry:
          if vo not in vo_list:
            msg = "The vo %s is explicity listed in the allowed_vos list in "  % vo
            msg += "section %s, but is not in the list of allowed VOs." % section
            if vo_list:
              msg += "  The list of allowed VOs are: %s." % ', '.join(vo_list)
            else:
              msg += "  There are no allowed VOs detected; contact the experts!"
            raise exceptions.SettingError(msg)
    self.log('GipConfiguration.checkSE completed')
    return attributes_ok
    
# pylint: disable-msg=W0613
  def configure(self, attributes):
    """
    Configure installation using attributes.
    """
    self.log('GipConfiguration.configure started')

    if not self.enabled:
      self.log('Not enabled, exiting...')         
      self.log('GipConfiguration.configure completed')   
      return 
    
    try:
      gip_pwent = pwd.getpwnam(self.gip_user)
    except Exception, e:
      self.log("Couldn't find username %s" % self.gip_user,
               exception = True,
               level = logging.ERROR)
      raise exceptions.ConfigureError("Couldn't find username %s: %s" % (self.gip_user, e))

    (gip_uid, gip_gid)  = gip_pwent[2:4]
    gip_tmpdir = os.path.join('/', 'var', 'tmp', 'gip')
    gip_logdir = os.path.join('/', 'var', 'log', 'gip')

    try:
      if not os.path.exists(gip_tmpdir):
        self.log("%s is not present, recreating" % gip_logdir)
        os.mkdir(gip_tmpdir)
      if not os.path.isdir(gip_tmpdir):
        self.log("%s is not a directory, " % gip_tmpdir +
                 "please remove it and recreate it as a directory ",
                 level = logging.ERROR)
        raise exceptions.ConfigureError("GIP tmp directory not setup: %s" % gip_tmpdir)
      os.chown(gip_tmpdir, gip_uid, gip_gid)
    except Exception, e:
      self.log("Can't set permissions on " + gip_tmpdir,
               exception = True,
               level = logging.ERROR)
      raise exceptions.ConfigureError("Can't set permissions on %s: %s" % (gip_tmpdir, e))

    try:
      if not os.path.exists(gip_logdir) or not os.path.isdir(gip_logdir):
        self.log("%s is not present or is not a directory, " % gip_logdir +
                 "gip did not install correctly",
                 level = logging.ERROR)
        raise exceptions.ConfigureError("GIP log directory not setup: %s" % gip_logdir)
      os.chown(gip_logdir, gip_uid, gip_gid)
    except Exception, e:
      self.log("Can't set permissions on " + gip_logdir,
               exception = True,
               level = logging.ERROR)
      raise exceptions.ConfigureError("Can't set permissions on %s: %s" % \
                                      (gip_logdir, e))        

    self.log('GipConfiguration.configure completed')   
    

  
# pylint: disable-msg=R0201
  def passThroughVariable(self, string):
    """Return true if string fits the format for the name of a pass through
    variable
    """
    if re.match("[A-Z0-9_]+", string):
      return True
    return False

  def moduleName(self):
    """
    Return a string with the name of the module
    """
    return "GIP"
  
  def separatelyConfigurable(self):
    """
    Return a boolean that indicates whether this module can be configured 
    separately
    """
    return True
  
