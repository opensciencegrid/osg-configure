#!/usr/bin/env python

""" Module to handle attributes and configuration for RSV service """

import os, re, pwd, shutil, ConfigParser, logging

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import validation
from osg_configure.modules import configfile
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['RsvConfiguration']


class RsvConfiguration(BaseConfiguration):
  """Class to handle attributes and configuration related to osg-rsv services"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(RsvConfiguration, self).__init__(*args, **kwargs)    
    self.log('RsvConfiguration.__init__ started')    
    self.options = {'enable_local_probes' : 
                      configfile.Option(name = 'enable_local_probes',
                                        required = configfile.Option.OPTIONAL,
                                        opt_type = bool,
                                        default_value = True),
                    'gratia_probes' : 
                      configfile.Option(name = 'gratia_probes',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL),
                    'ce_hosts' : 
                      configfile.Option(name = 'ce_hosts',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL),
                    'gridftp_hosts' : 
                      configfile.Option(name = 'gridftp_hosts',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL),
                    'gridftp_dir' : 
                      configfile.Option(name = 'gridftp_dir',
                                        default_value = '/tmp'),
                    'gums_hosts' : 
                      configfile.Option(name = 'gums_hosts',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL),
                    'srm_hosts' : 
                      configfile.Option(name = 'srm_hosts',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL),
                    'srm_dir' : 
                      configfile.Option(name = 'srm_dir',
                                        required = configfile.Option.OPTIONAL),
                    'srm_webservice_path' : 
                      configfile.Option(name = 'srm_webservice_path',
                                        required = configfile.Option.OPTIONAL),
                    'service_cert' : 
                      configfile.Option(name = 'service_cert',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = '/etc/grid-security/rsv/rsvcert.pem'),
                    'service_key' : 
                      configfile.Option(name = 'service_key',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = '/etc/grid-security/rsv/rsvkey.pem'),
                    'service_proxy' : 
                      configfile.Option(name = 'service_proxy',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = '/tmp/rsvproxy'),
                    'user_proxy' : 
                      configfile.Option(name = 'user_proxy',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL),
                    'legacy_proxy' : 
                      configfile.Option(name = 'legacy_proxy',
                                        required = configfile.Option.OPTIONAL,
                                        opt_type = bool,
                                        default_value = False),
                    'enable_gratia' : 
                      configfile.Option(name = 'enable_gratia',
                                        opt_type = bool),
                    'gratia_collector' : 
                      configfile.Option(name = 'gratia_collector',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = 'rsv.grid.iu.edu:8880'),
                    'condor_location' : 
                      configfile.Option(name = 'condor_location',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL),
                    'enable_nagios' : 
                      configfile.Option(name = 'enable_nagios',
                                        opt_type = bool),
                    'nagios_send_nsca' : 
                      configfile.Option(name = 'nagios_send_nsca',
                                        required = configfile.Option.OPTIONAL,
                                        opt_type = bool,
                                        default_value = False)}

    self.__rsv_user = "rsv"
    self.__ce_hosts = []
    self.__gridftp_hosts = []
    self.__gums_hosts = []
    self.__srm_hosts = []
    self.__gratia_probes_2d = []
    self.__gratia_metric_map = {}
    self.__enable_rsv_downloads = False
    self.__meta = ConfigParser.RawConfigParser()
    self.use_service_cert = True
    self.grid_group = 'OSG'
    self.site_name = 'Generic Site'
    self.config_section = "RSV"
    self.rsv_control = os.path.join('/', 'usr', 'bin', 'rsv-control')
    self.rsv_meta_dir = os.path.join('/', 'etc', 'rsv', 'meta', 'metrics')
    self.uid = None
    self.gid = None
    self.log('RsvConfiguration.__init__ completed')

  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or 
    SafeConfigParser object given by configuration and write recognized settings 
    to attributes dict
    """
    self.log('RsvConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)
    
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)    
      self.log('RsvConfiguration.parseConfiguration completed')    
      return True

    if not utilities.rpm_installed('rsv-core'):
      self.enabled = False
      self.log('rsv-core rpm not installed, disabling RSV configuration')
      if configuration.has_section(self.config_section):        
        self.log('Your configuration has configuration information for RSV ' +
                 'but RSV is not installed. RSV configuration will be ' +
                 'ignored.',
                 level = logging.WARNING)
      return True

    if not self.setStatus(configuration):
      self.log('RsvConfiguration.parseConfiguration completed')    
      return True

    self.getOptions(configuration, ignore_options = ['enabled'])
    (self.uid, self.gid) = pwd.getpwnam(self.__rsv_user)[2:4]

    # If we're on a CE, get the grid group if possible
    if configuration.has_section('Site Information'): 
      if configuration.has_option('Site Information', 'group'):
        self.grid_group = configuration.get('Site Information', 'group')

      if configuration.has_option('Site Information', 'resource'):
        self.site_name = configuration.get('Site Information', 'resource')
      elif configuration.has_option('Site Information', 'site_name'):
        self.site_name = configuration.get('Site Information', 'site_name')


    # Parse lists
    self.__ce_hosts = split_list(self.options['ce_hosts'].value)
    self.__gums_hosts = split_list(self.options['gums_hosts'].value)
    self.__srm_hosts = split_list(self.options['srm_hosts'].value)

    # If the gridftp hosts are not defined then they default to the CE hosts
    if self.options['gridftp_hosts'].value == '':
      # check to see if the setting is in the config file
      if configuration.has_option(self.config_section, 'gridftp_hosts'):
        # present and set to default so we don't want gridftp tests
        self.__gridftp_hosts = []
      else:
        # option is commented out, use ce_hosts setting
        self.__gridftp_hosts = self.__ce_hosts
    else:
      self.__gridftp_hosts = split_list(self.options['gridftp_hosts'].value)

    
    if self.options['gratia_probes'].value != '':
      self.__gratia_probes_2d = self.split_2d_list(self.options['gratia_probes'].value)

    self.log('RsvConfiguration.parseConfiguration completed')    
  

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """
    Check attributes currently stored and make sure that they are consistent
    """

    self.log('RsvConfiguration.checkAttributes started')
    attributes_ok = True

    if not self.enabled:
      self.log('Not enabled, returning True')
      self.log('RsvConfiguration.checkAttributes completed')    
      return attributes_ok

    if self.ignored:
      self.log('Ignored, returning True')
      self.log('RsvConfiguration.checkAttributes completed')    
      return attributes_ok

    # Slurp in all the meta files which will tell us what type of metrics
    # we have and if they are enabled by default.
    self.load_rsv_meta_files()

    attributes_ok &= self.__check_auth_settings()
    
    # check hosts
    attributes_ok &= self.__validate_host_list(self.__ce_hosts, "ce_hosts")
    attributes_ok &= self.__validate_host_list(self.__gums_hosts, "gums_hosts")
    attributes_ok &= self.__validate_host_list(self.__srm_hosts, "srm_hosts")
    attributes_ok &= self.__check_gridftp_settings()
    attributes_ok &= self.__check_srm_settings()
    # check Gratia list
    attributes_ok &= self.__check_gratia_settings()

    # Make sure that the condor_location is valid if it is supplied
    attributes_ok &= self.__check_condor_location()

    self.log('RsvConfiguration.checkAttributes completed')    
    return attributes_ok 


  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('RsvConfiguration.configure started')    

    if self.ignored:
      self.log("%s configuration ignored" % self.config_section,
               level = logging.WARNING)
      self.log('RsvConfiguration.configure completed') 
      return True

    if not self.enabled:
      self.log('Not enabled, returning True')
      self.log('RsvConfiguration.configure completed') 
      return True

    # Reset always?
    if not self.__reset_configuration():
      return False

    # Put proxy information into rsv.ini
    if not self.__configure_cert_info():
      return False
    
    # Enable consumers
    if not self.__configure_consumers():
      return False

    # Enable metrics
    if not self.__configure_ce_metrics():
      return False

    if not self.__configure_gums_metrics():
      return False

    if not self.__configure_gridftp_metrics():
      return False

    if not self.__configure_gratia_metrics():
      return False

    if not self.__configure_local_metrics():
      return False

    if not self.__configure_srm_metrics():
      return False

    # Setup Apache?  I think this is done in the RPM

    # Fix the Gratia ProbeConfig file to point at the appropriate collector
    self.__set_gratia_collector(self.options['gratia_collector'].value)

    if not self.__configure_condor_location():
      return False

    self.log('RsvConfiguration.configure completed')
    return True

  def moduleName(self):
    """Return a string with the name of the module"""
    return "RSV"

  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True  

  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]


  def __check_gridftp_settings(self):
    """ Check gridftp settings and make sure they are valid """
    status_check = self.__validate_host_list(self.__gridftp_hosts, "gridftp_hosts")

    if utilities.blank(self.options['gridftp_dir'].value):
      self.log("Invalid gridftp_dir given: %s" %
               self.options['gridftp_dir'].value,
               section = self.config_section,
               option = 'gridftp_dir',
               level = logging.ERROR)
      status_check = False

    return status_check 

  def __check_auth_settings(self):
    """ Check authorization/certificate settings and make sure that they are valid """

    check_value = True

    # Do not allow both the service cert settings and proxy settings
    # first create some helper variables
    blank_service_vals = (utilities.blank(self.options['service_cert'].value) and
                          utilities.blank(self.options['service_key'].value) and
                          utilities.blank(self.options['service_proxy'].value))

    default_service_vals = (self.options['service_cert'].value == 
                            self.options['service_cert'].default_value)
    default_service_vals &= (self.options['service_key'].value == 
                             self.options['service_key'].default_value)
    default_service_vals &= (self.options['service_proxy'].value == 
                             self.options['service_proxy'].default_value)

    blank_user_proxy = utilities.blank(self.options['user_proxy'].value)

    if (not blank_user_proxy and default_service_vals):
      self.log('User proxy specified and service_cert, service_key, ' +
               'service_proxy at default values, assuming user_proxy ' +
               'takes precedence in ' + self.config_section + ' section')
      self.use_service_cert = False
    elif not blank_user_proxy and not blank_service_vals:
      self.log("You cannot specify user_proxy with any of (service_cert, " +
               "service_key, service_proxy).  They are mutually exclusive " +
               "options in %s section." % self.config_section,
               level = logging.ERROR)
      check_value = False

    # Make sure that either a service cert or user cert is selected
    if not ((self.options['service_cert'].value and
             self.options['service_key'].value and
             self.options['service_proxy'].value)
            or
            self.options['user_proxy'].value):
      self.log("You must specify either service_cert/service_key/" +
               "service_proxy *or* user_proxy in order to provide " +
               "credentials for RSV to run jobs in " +
               " %s section" % self.config_section,
               level = logging.ERROR)
      check_value = False

    if not blank_user_proxy:
      # if not using a service certificate, make sure that the proxy file exists
      value = self.options['user_proxy'].value
      if utilities.blank(value) or not validation.valid_file(value):
        self.log("user_proxy does not point to an existing file: %s" % value,
                 section = self.config_section,
                 option = 'user_proxy',
                 level = logging.ERROR)
        check_value = False      
    else:
      value = self.options['service_cert'].value
      if utilities.blank(value) or not validation.valid_file(value):
        self.log("service_cert must point to an existing file: %s" % value,
                 section = self.config_section,
                 option = 'service_cert',
                 level = logging.ERROR)
        check_value = False

      value = self.options['service_key'].value
      if utilities.blank(value) or not validation.valid_file(value):
        self.log("service_key must point to an existing file: %s" % value,
                 section = self.config_section,
                 option = 'service_key',
                 level = logging.ERROR)
        check_value = False

      value = self.options['service_proxy'].value
      if utilities.blank(value):
        self.log("service_proxy must have a valid location: %s" % value,
                 section = self.config_section,
                 option = 'service_proxy',
                 level = logging.ERROR)
        check_value = False

      value = os.path.dirname(self.options['service_proxy'].value)
      if not validation.valid_location(value):
        self.log("service_proxy must be located in a valid " +
                 "directory: %s" % value,
                 section = self.config_section,
                 option = 'service_proxy',
                 level = logging.ERROR)
        check_value = False

    return check_value


  def __reset_configuration(self):
    """ Reset all metrics and consumers to disabled """

    self.log("Resetting all metrics and consumers to disabled")

    parent_dir = os.path.join('/', 'etc', 'rsv')
    for filename in os.listdir(parent_dir):
      if not re.search('\.conf$', filename):
        continue

      if filename == "rsv.conf" or filename == "rsv-nagios.conf":
        continue

      path = os.path.join(parent_dir, filename)
      self.log("Removing %s as part of reset" % path)
      os.unlink(path)

    # Remove any host specific metric configuration
    parent_dir = os.path.join('/', 'etc', 'rsv', 'metrics')
    for directory in os.listdir(parent_dir):
      path = os.path.join(parent_dir, directory)
      if not os.path.isdir(path):
        continue

      shutil.rmtree(path)
      
    return True    


  def __get_metrics_by_type(self, metric_type, enabled=True):
    """
    Examine meta info and return the metrics that are enabled by default 
    for the defined type
    """

    metrics = []
    
    for metric in self.__meta.sections():
      if re.search(" env$", metric):
        continue

      if self.__meta.has_option(metric, "service-type"):
        if self.__meta.get(metric, "service-type") == metric_type:
          if not enabled:
            metrics.append(metric)
          else:
            if self.__meta.has_option(metric, "enable-by-default"):
              if self.__meta.get(metric, "enable-by-default") == "true":
                metrics.append(metric)

    return metrics


  def __enable_metrics(self, host, metrics, args = None):
    """ Given a host and array of metrics, enable them via rsv-control """

    # need this to prevent weird behaviour if [] as a default argument in function def
    args = args or []
    if not metrics:
      return True

    if not utilities.run_script([self.rsv_control, "-v0", "--enable", "--host", host] +
                                args + 
                                metrics):
      self.log("ERROR: Attempt to enable metrics via rsv-control failed",
               level = logging.ERROR)
      self.log("Host: %s" % host,
               level = logging.ERROR)
      self.log("Metrics: %s" % " ".join(metrics),
               level = logging.ERROR)
      return False

    return True

  def __configure_ce_metrics(self):
    """
    Enable appropriate CE metrics
    """

    if not self.__ce_hosts:
      self.log("No ce_hosts defined.  Not configuring CE metrics")
      return True

    ce_metrics = self.__get_metrics_by_type("OSG-CE")

    for ce in self.__ce_hosts:
      self.log("Enabling CE metrics for host '%s'" % ce)
      if not self.__enable_metrics(ce, ce_metrics):
        return False

    return True


  def __configure_gridftp_metrics(self):
    """ Enable GridFTP metrics for each GridFTP host declared    """

    if not self.__gridftp_hosts:
      self.log("No gridftp_hosts defined.  Not configuring GridFTP metrics")
      return True

    gridftp_dirs = split_list(self.options['gridftp_dir'].value)
    if len(self.__gridftp_hosts) != len(gridftp_dirs) and len(gridftp_dirs) != 1:
      self.log("RSV.gridftp_dir is set incorrectly.  When enabling GridFTP " +
               "metrics you must specify either exactly 1 entry, or the same "+
               "number of entries in the gridftp_dir variable as you have in " +
               "the gridftp_hosts section.  There are %i host entries " \
               "and %i gridftp_dir entries." % (len(self.__gridftp_hosts), 
                                                len(gridftp_dirs)),
               level = logging.ERROR)
      raise exceptions.ConfigureError("Failed to configure RSV")

    gridftp_metrics = self.__get_metrics_by_type("GridFTP")

    count = 0
    for gridftp_host in self.__gridftp_hosts:
      self.log("Enabling GridFTP metrics for host '%s'" % gridftp_host)

      if len(gridftp_dirs) == 1:
        directories = gridftp_dirs[0]
      else:
        directories = gridftp_dirs[count]

      args = ["--arg", "destination-dir=%s" % directories]

      if not self.__enable_metrics(gridftp_host, gridftp_metrics, args):
        return False

      count += 1
             
    return True



  def __configure_gums_metrics(self):
    """ Enable GUMS metrics for each GUMS host declared """

    if not self.__gums_hosts:
      self.log("No gums_hosts defined.  Not configuring GUMS metrics")
      return True

    gums_metrics = self.__get_metrics_by_type("OSG-GUMS")

    if not gums_metrics:
      self.log("No current GUMS metrics.  No configuration to do at this time.")
      return True

    for gums_host in self.__gums_hosts:
      self.log("Enabling GUMS metrics for host '%s'" % gums_host)
      if not self.__enable_metrics(gums_host, gums_metrics):
        return False

    return True


  def __configure_local_metrics(self):
    """ Enable appropriate local metrics """

    if not self.options['enable_local_probes'].value:
      self.log("Local probes disabled.")
      return True

    local_metrics = self.__get_metrics_by_type("OSG-Local-Monitor")

    self.log("Enabling local metrics for host '%s'" % utilities.get_hostname())
    if not self.__enable_metrics(utilities.get_hostname(), local_metrics):
      return False
    
    return True


  def __configure_srm_metrics(self):
    """ Enable SRM metric """

    if not self.__srm_hosts:
      self.log("No srm_hosts defined.  Not configuring SRM metrics")
      return True

    # Do some checking on the values.  perhaps this should be in the validate section?
    srm_dirs = split_list(self.options['srm_dir'].value)
    if len(self.__srm_hosts) != len(srm_dirs):
      self.log("When enabling SRM metrics you must specify the same number " +
               "of entries in the srm_dir variable as you have in the " +
               "srm_hosts section.  There are %i host entries and %i " \
               "srm_dir entries." % (len(self.__srm_hosts), len(srm_dirs)),
               level = logging.ERROR)
      raise exceptions.ConfigureError("Failed to configure RSV")

    srm_ws_paths = []
    if not utilities.blank(self.options['srm_webservice_path'].value):
      srm_ws_paths = split_list(self.options['srm_webservice_path'].value)

      if len(self.__srm_hosts) != len(srm_ws_paths):
        self.log("If you set srm_webservice_path when enabling SRM metrics " +
                 "you must specify the same number of entries in the " +
                 "srm_webservice_path variable as you have in the srm_hosts " +
                 "section.  There are %i host entries and %i " \
                 "srm_webservice_path entries." % (len(self.__srm_hosts), 
                                                   len(srm_ws_paths)),
                 level = logging.ERROR)
        raise exceptions.ConfigureError("Failed to configure RSV")

    # Now time to do the actual configuration
    srm_metrics = self.__get_metrics_by_type("OSG-SRM")
    count = 0
    for srm_host in self.__srm_hosts:
      self.log("Enabling SRM metrics for host '%s'" % srm_host)

      args = ["--arg", "srm-destination-dir=%s" % srm_dirs[count]]
      if srm_ws_paths:
        args += ["--arg", "srm-webservice-path=%s" % srm_ws_paths[count]]

      if not self.__enable_metrics(srm_host, srm_metrics, args):
        return False

      count += 1
      
    return True


  def __map_gratia_metric(self, gratia_type):
    """
    Map gratia type to rsv metric 
    """
    # The first time through we will populate the map.  It will be cached as a
    # data member in this class so that we don't have to do this each time
    if not self.__gratia_metric_map:
      ce_metrics = self.__get_metrics_by_type("OSG-CE", enabled=False)
      for metric in ce_metrics:
        match = re.search("\.gratia\.(\S+)$", metric)
        if match:
          self.__gratia_metric_map[match.group(1)] = metric
          self.log("Gratia map -> %s = %s" % (match.group(1), metric))

    # Now that we have the mapping, simply return the appropriate type.
    # This is the only code that should execute every time after the data structure is loaded.
    if gratia_type in self.__gratia_metric_map:
      return self.__gratia_metric_map[gratia_type]
    else:
      return None


  def __check_gratia_settings(self):
    """ Check to see if gratia settings are valid """

    tmp_2d = []

    # While checking the Gratia settings we will translate them to a list of
    # the actual probes to enable.
    status_check = True
    for item_list in self.__gratia_probes_2d:
      tmp = []
      for metric_type in item_list:
        metric = self.__map_gratia_metric(metric_type)
        if metric:
          tmp.append(metric)
        else:
          status_check = False
          self.log("In %s section, gratia_probes setting: Probe %s is " \
                   "not a valid probe" % (self.config_section , metric_type),
                   level = logging.ERROR)

      tmp_2d.append(tmp)

    self.__gratia_probes_2d = tmp_2d

    return status_check


  def __configure_gratia_metrics(self):
    """
    Enable Gratia metrics
    """

    if not self.__gratia_probes_2d:
      self.log("Skipping Gratia metric configuration because gratia_probes_2d is empty")
      return True

    if not self.__ce_hosts:
      self.log("Skipping Gratia metric configuration because ce_hosts is empty")
      return True

    num_ces = len(self.__ce_hosts)
    num_gratia = len(self.__gratia_probes_2d)
    if num_ces != num_gratia and num_gratia != 1:
      self.log("The number of CE hosts does not match the number of " +
               "Gratia host definitions",
               level = logging.ERROR)
      self.log("Number of CE hosts: %s" % num_ces,
               level = logging.ERROR)
      self.log("Number of Gratia host definitions: %s" % num_gratia,
               level = logging.ERROR)
      self.log("They must match, or you must have only one Gratia host " +
               "definition (which will be used for all hosts",
               level = logging.ERROR)
      return False

    i = 0
    for ce in self.__ce_hosts:
      gratia = None

      # There will either be a Gratia definition for each host, or else a single Gratia
      # definition which we will use across all hosts.
      if num_gratia == 1:
        gratia = self.__gratia_probes_2d[0]
      else:
        gratia = self.__gratia_probes_2d[i]
        i += 1

      if not self.__enable_metrics(ce, gratia):
        return False

    return True


  def __check_condor_location(self):
    """ Make sure that a supplied Condor location is valid """

    if not self.options['condor_location'].value:
      self.log("Skipping condor_location validation because it is empty")
      return True

    condor_bin = os.path.join(self.options['condor_location'].value, "bin")
    condor_sbin = os.path.join(self.options['condor_location'].value, "sbin")

    if not os.path.exists(condor_bin) or not os.path.exists(condor_sbin):
      self.log("There is not a bin/ or sbin/ subdirectory at the supplied " +
               "condor_location (%s)" % (self.options['condor_location'].value),
               level=logging.ERROR)
      return False

    return True


  def __configure_condor_location(self):
    """ Put the Condor location into the necessary places """

    # Note: make sure that we write empty files if condor_location is not set
    # so that we can reverse the action of someone setting condor_location

    condor_dir = self.options['condor_location'].value

    # Put the location into the condor-cron-env.sh file so that the condor-cron
    # wrappers and init script have the binaries in their PATH
    sysconf_file = os.path.join('/', 'etc', 'sysconfig', 'condor-cron')
    try:
      sysconf = open(sysconf_file, 'w')
      if self.options['condor_location'].value:
        sysconf.write("PATH=%s/bin:%s/sbin:$PATH\n" % (condor_dir,
                                                       condor_dir))
        sysconf.write("export PATH\n")
      sysconf.close()
    except IOError, err:
      self.log("Error trying to write to file (%s): %s" % (sysconf_file, err))
      return False

    # Adjust the Condor-Cron configuration
    conf_file = os.path.join('/', 'etc', 'condor-cron', 'config.d', 'condor_location')
    try:
      config = open(conf_file, 'w')
      if self.options['condor_location'].value:
        config.write("RELEASE_DIR = %s" % condor_dir)
      config.close()
    except IOError, err:
      self.log("Error trying to write to file (%s): %s" % (conf_file, err))
      return False
      
    
    return True
  
      
  def __validate_host_list(self, hosts, setting):
    """ Validate a list of hosts """
    ret = True
    for host in hosts:
      # Strip off the port
      if ':' in host:
        (hostname, port) = host.split(':')
      else:
        hostname = host
        port = False
      if not validation.valid_domain(hostname):
        self.log("Invalid domain in [%s].%s: %s" % (self.config_section, 
                                                    setting, host),
                 level = logging.ERROR)
        ret = False

      if port and re.search('\D', port):
        self.log("Invalid port in [%s].%s: %s" % (self.config_section, 
                                                  setting, host),
                 level = logging.ERROR)

    return ret


  def __configure_cert_info(self):
    """ Configure certificate information """

    # Load in the existing configuration file
    config_file = os.path.join('/', 'etc', 'rsv', 'rsv.conf')
    config = ConfigParser.RawConfigParser()
    config.optionxform = str

    if os.path.exists(config_file):
      config.read(config_file)

    if not config.has_section('rsv'):
      config.add_section('rsv')

    # Set the appropriate options in the rsv.conf file
    if self.use_service_cert:
      config.set('rsv', 'service-cert', self.options['service_cert'].value)
      config.set('rsv', 'service-key', self.options['service_key'].value)
      config.set('rsv', 'service-proxy', self.options['service_proxy'].value)
    else:
      config.set('rsv', 'proxy-file', self.options['user_proxy'].value)

      # Remove these keys or they will override the proxy-file setting in rsv-control
      config.remove_option('rsv', 'service-cert')
      config.remove_option('rsv', 'service-key')
      config.remove_option('rsv', 'service-proxy')

    if self.options['legacy_proxy'].value:
      config.set('rsv', 'legacy-proxy', 'True')
    else:
      config.remove_option('rsv', 'legacy-proxy')

    # Write back to disk
    config_fp = open(config_file, 'w')
    config.write(config_fp)
    config_fp.close()

    return True


  def __configure_consumers(self):
    """ Enable the appropriate consumers """

    # The current logic is:
    #  - we ALWAYS want the html-consumer if we are told to install consumers
    #  - we want the gratia-consumer if enable_gratia is True
    #  - we want the nagios-consumer if enable_nagios is True

    consumers = ["html-consumer"]

    if self.options['enable_gratia'].value:
      consumers.append("gratia-consumer")
      # TODO - set up Gratia directories?  Look at setup_gratia() in configure_rsv

    if self.options['enable_nagios'].value:
      consumers.append("nagios-consumer")
      self.__configure_nagios_files()

    consumer_list = " ".join(consumers)
    self.log("Enabling consumers: %s " % consumer_list)

    if utilities.run_script([self.rsv_control, "-v0", "--enable"] + consumers):
      return True
    else:
      return False


  def __configure_nagios_files(self):
    """ Store the nagios configuration """

    # The Nagios conf file contains a password so set it to mode 0400 owned by rsv
    pw_file = os.path.join('/', 'etc', 'rsv', 'rsv-nagios.conf')
    os.chown(pw_file, self.uid, self.gid)
    os.chmod(pw_file, 0400)
    
    # Add the configuration file 
    nagios_conf_file = os.path.join('/', 'etc', 'rsv', 'consumers', 'nagios-consumer.conf')
    config = ConfigParser.RawConfigParser()
    config.optionxform = str
    
    if os.path.exists(nagios_conf_file):
      config.read(nagios_conf_file)
      
    if not config.has_section('nagios-consumer'):
      config.add_section('nagios-consumer')

    args = "--conf-file %s" % pw_file
    if self.options['nagios_send_nsca'].value:
      args += " --send-nsca"

    config.set("nagios-consumer", "args", args)
    
    config_fp = open(nagios_conf_file, 'w')
    config.write(config_fp)
    config_fp.close()

    return


  def load_rsv_meta_files(self):
    """ All the RSV meta files are in INI format.  Pull them in so that we know what
    metrics to enable """

    if not os.path.exists(self.rsv_meta_dir):
      self.log("In RSV configuration, meta dir (%s) does not exist." % self.rsv_meta_dir)
      return
      
    files = os.listdir(self.rsv_meta_dir)

    for filename in files:
      if re.search('\.meta$', filename):
        self.__meta.read(os.path.join(self.rsv_meta_dir, filename))

    return

  def split_2d_list(self, item_list):
    """ 
    Split a comma/whitespace separated item_list of item_list of items.
    Each item_list needs to be enclosed in parentheses and separated by whitespace and/or a comma.
    Parentheses are optional if only one item_list is supplied.
    
    Valid examples include:
    (1,2,3),(4,5)
    1,2,3,4,5
    (1,2), (4) , (5,6)  (8),    # comma at end is ok, comma between lists is optional

    Invalid examples:
    (1,2,3), 4    # 4 needs to be in parentheses
    1,2,3, (4,5)  # 1,2,3 needs to be parenthesized
    (1,2, (3, 4)  # missing a right parenthesis
    """

    if not item_list:
      return [[]]
          
    original_list = item_list

    # If there are no parentheses then just treat this like a normal comma-separated item_list
    # and return it as a 2-D array (with only one element in one direction)
    if not re.search("\(", item_list) and not re.search("\)", item_list):
      return [split_list(item_list)]

    # We want to grab parenthesized chunks
    pattern = re.compile("\s*\(([^()]+)\)\s*,?")
    array = []
    while 1:
      match = re.match(pattern, item_list)
      if not match:
        # If we don't have a match then we are either finished processing, or there is
        # a syntax error.  So if we have anything left in the string we will bail
        if re.search("\S", item_list):
          self.log("ERROR: syntax error in parenthesized item_list",
                   level = logging.ERROR)
          self.log("ERROR: Supplied item_list:\n\t%s" % original_list,
                   level = logging.ERROR)
          self.log("ERROR: Leftover after parsing:\n\t%s" % item_list,
                   level = logging.ERROR)
          return False
        else:
          return array

      array.append(split_list(match.group(1)))
    
      # Remove what we just matched so that we get the next chunk on the next iteration
      match_length = len(match.group(0))
      item_list = item_list[match_length:]

    # We shouldn't reach here, but just in case...
    return array


  def __set_gratia_collector(self, collector):
    """ Put the appropriate collector URL into the ProbeConfig file """

    if not self.options['enable_gratia'].value:
      self.log("Not configuring Gratia collector because enable_gratia is not true")
      return True

    probe_conf = os.path.join('/', 'etc', 'gratia', 'metric', 'ProbeConfig')

    self.log("Putting collector '%s' into Gratia conf file '%s'" % (collector, probe_conf))

    conf = open(probe_conf).read()

    conf = re.sub("CollectorHost=\".+\"", "CollectorHost=\"%s\"" % collector, conf)
    conf = re.sub("SSLHost=\".+\"", "SSLHost=\"%s\"" % collector, conf)
    conf = re.sub("SSLRegistrationHost=\".+\"", "SSLRegistrationHost=\"%s\"" % collector, conf)
    conf = re.sub(r'(\s*)EnableProbe\s*=.*', r'\1EnableProbe="1"', conf, 1)
    conf = re.sub(r'(\s*)Grid\s*=.*', r'\1Grid="' + self.grid_group + '"', conf, 1)
    conf = re.sub(r'(\s*)SiteName\s*=.*', r'\1SiteName="' + self.site_name + '"', conf, 1)

    # Set logging to whatever is appropriate.  We'll just go with level=1, rotate=7 for now
    conf = re.sub(r'(\s*)LogLevel\s*=.*', r'\1LogLevel="1"', conf, 1)
    conf = re.sub(r'(\s*)LogRotate\s*=.*', r'\1LogRotate="7"', conf, 1)

    # Also, set up the directories to use the proper log/data/working dirs
    parent_dir = os.path.join('/', 'var', 'log', 'gratia', 'rsv')

    log_folder = os.path.join(parent_dir, 'logs')
    if not os.path.exists(log_folder):
      utilities.make_directory(log_folder, 0755, self.uid, self.gid)
    elif os.path.isdir(log_folder):
      os.chown(log_folder, self.uid, self.gid)
    conf = re.sub(r'(\s*)LogFolder\s*=.*', r'\1LogFolder="' + log_folder + '"', conf, 1)

    data_folder = os.path.join(parent_dir, 'data')
    if not os.path.exists(data_folder):
      utilities.make_directory(data_folder, 0755, self.uid, self.gid)
    elif os.path.isdir(data_folder):
      os.chown(data_folder, self.uid, self.gid)
    conf = re.sub(r'(\s*)DataFolder\s*=.*', r'\1DataFolder="' + data_folder + '"', conf, 1)

    working_folder = os.path.join(parent_dir, 'tmp')
    if not os.path.exists(working_folder):
      utilities.make_directory(working_folder, 0755, self.uid, self.gid)
    elif os.path.isdir(working_folder):
      os.chown(working_folder, self.uid, self.gid)
    conf = re.sub(r'(\s*)WorkingFolder\s*=.*', 
                  r'\1WorkingFolder="' + working_folder + '"', 
                  conf,
                  1)
  

    if not utilities.atomic_write(probe_conf, conf):
      self.log("Error while configuring metric probe: can't " +
               "write to %s" % probe_conf,
               level = logging.ERROR)
      raise exceptions.ConfigureError("Error configuring gratia")

    return True
  
  def __check_srm_settings(self):
    """
    Check srm settings to make sure settings are consistent and properly
    set
    """
    if (self.__srm_hosts == [] or 
        self.__srm_hosts is None or 
        utilities.blank(self.options['srm_hosts'].value)):
      return True

    if self.options['srm_dir'].value.upper() == 'DEFAULT':
      self.log("srm_dir has to be set and can't be set to DEFAULT for each "+ 
               "srm host defined (set to %s)" % dir,
               option = 'srm_dir',
               section = 'rsv',
               level = logging.ERROR)
      
    srm_dirs = split_list(self.options['srm_dir'].value)    
    if len(self.__srm_hosts) != len(srm_dirs):
      self.log("When enabling SRM metrics you must specify the same number " +
               "of entries in the srm_dir variable as you have in the " +
               "srm_hosts section.  There are %i host entries and %i " \
               "srm_dir entries." % (len(self.__srm_hosts), len(srm_dirs)),
               level = logging.ERROR)
      return False
    for directory in srm_dirs:
      if directory.upper() == 'DEFAULT':
        self.log("srm_dir has to be set and can't be set to DEFAULT for each "+ 
                 "srm host defined (set to %s)" % directory,
                 option = 'srm_dir',
                 section = 'rsv',
                 level = logging.ERROR)
        
    
    srm_ws_paths = []
    if not utilities.blank(self.options['srm_webservice_path'].value):      
      srm_ws_paths = split_list(self.options['srm_webservice_path'].value)
      if len(self.__srm_hosts) != len(srm_ws_paths):
        self.log("If you set srm_webservice_path when enabling SRM metrics " +
                 "you must specify the same number of entries in the " +
                 "srm_webservice_path variable as you have in the srm_hosts " +
                 "section.  There are %i host entries and %i " \
                 "srm_webservice_path entries." % (len(self.__srm_hosts), 
                                                   len(srm_ws_paths)),
                 level = logging.ERROR)
        return False
      
    return True

  def enabledServices(self):
    """Return a list of  system services needed for module to work
    """
    if self.enabled and not self.ignored:
      return ['rsv']
    else:
      return []

def split_list(item_list):
  """ Split a comma separated list of items """

  # Special case - when the list just contains UNAVAILABLE we want to ignore it
  if utilities.blank(item_list):
    return []
  
  items = []
  for entry in item_list.split(','):
    items.append(entry.strip())
    
  return items

