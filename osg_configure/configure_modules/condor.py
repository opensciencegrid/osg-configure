""" Module to handle attributes and configuration related to the condor 
jobmanager configuration """

import os
import logging
import re

from osg_configure.modules import utilities
from osg_configure.modules import validation
from osg_configure.modules import configfile
from osg_configure.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['CondorConfiguration']



class CondorConfiguration(JobManagerConfiguration):
  """Class to handle attributes related to condor job manager configuration"""
  
  CONDOR_CONFIG_FILE = '/etc/grid-services/available/jobmanager-condor'
  GRAM_CONFIG_FILE = '/etc/globus/globus-condor.conf'
  HTCONDOR_CE_CONFIG_FILE = '/etc/condor-ce/config.d/50-osg-configure.conf'

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(CondorConfiguration, self).__init__(*args, **kwargs)
    self.log('CondorConfiguration.__init__ started')    
    self.config_section = "Condor"
    self.options = {'condor_location' : 
                      configfile.Option(name = 'condor_location',
                                        default_value = utilities.get_condor_location(),
                                        mapping = 'OSG_CONDOR_LOCATION'),
                    'condor_config' : 
                      configfile.Option(name = 'condor_config',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = utilities.get_condor_config(),
                                        mapping = 'OSG_CONDOR_CONFIG'),
                    'job_contact' : 
                      configfile.Option(name = 'job_contact',
                                        mapping = 'OSG_JOB_CONTACT'),
                    'util_contact' : 
                      configfile.Option(name = 'util_contact',
                                        mapping = 'OSG_UTIL_CONTACT'),
                    'accept_limited' : 
                      configfile.Option(name = 'accept_limited',
                                        required = configfile.Option.OPTIONAL,
                                        opt_type = bool,
                                        default_value = False)}
    self.__set_default = True
    self.log('CondorConfiguration.__init__ completed')
      
  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    super(CondorConfiguration, self).parseConfiguration(configuration)

    self.log('CondorConfiguration.parseConfiguration started')

    self.checkConfig(configuration)
      
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)
      self.log('CondorConfiguration.parseConfiguration completed')
      return

    if not self.setStatus(configuration):
      self.log('CondorConfiguration.parseConfiguration completed')
      return True
           
    self.getOptions(configuration, ignore_options = ['enabled'])
    
    # set OSG_JOB_MANAGER and OSG_JOB_MANAGER_HOME
    self.options['job_manager'] = configfile.Option(name = 'job_manager',
                                                    value = 'Condor',
                                                    mapping = 'OSG_JOB_MANAGER')
    self.options['home'] = configfile.Option(name = 'job_manager_home',
                                             value = self.options['condor_location'].value,
                                             mapping = 'OSG_JOB_MANAGER_HOME')

    if (configuration.has_section('Managed Fork') and
        configuration.has_option('Managed Fork', 'enabled') and
        configuration.getboolean('Managed Fork', 'enabled')):
      self.__set_default = False

    self.log('CondorConfiguration.parseConfiguration completed')

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('CondorConfiguration.checkAttributes started')

    if not self.enabled:
      self.log('CondorConfiguration.checkAttributes completed returning True')
      return True
    
    if self.ignored:
      self.log('CondorConfiguration.checkAttributes completed returning True')
      return True

    attributes_ok = True

    # make sure locations exist
    self.log('checking condor_location')
    if not validation.valid_location(self.options['condor_location'].value):
      attributes_ok = False
      self.log("Non-existent location given: %s" % 
                          (self.options['condor_location'].value),
                option = 'condor_location',
                section = self.config_section,
                level = logging.ERROR)

    self.log('checking condor_config')
    if not validation.valid_file(self.options['condor_config'].value):
      attributes_ok = False
      self.log("Non-existent location given: %s" % 
                          (self.options['condor_config'].value),
                option = 'condor_config',
                section = self.config_section,
                level = logging.ERROR)

    if not validation.valid_contact(self.options['job_contact'].value, 
                                    'condor'):
      attributes_ok = False
      self.log("Invalid job contact: %s" % 
                         (self.options['job_contact'].value),
               option = 'job_contact',
               section = self.config_section,
               level = logging.ERROR)
      
    if not validation.valid_contact(self.options['util_contact'].value, 
                                    'condor'):
      attributes_ok = False
      self.log("Invalid util contact: %s" % 
                        (self.options['util_contact'].value),
               option = 'util_contact',
               section = self.config_section,
               level = logging.ERROR)


    self.log('CondorConfiguration.checkAttributes completed returning %s' \
                       % attributes_ok)
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('CondorConfiguration.configure started')

    if self.ignored:
      self.log("%s configuration ignored" % self.config_section, 
               level = logging.WARNING)
      self.log('CondorConfiguration.configure completed')
      return True

    if not self.enabled:
      self.log('condor not enabled')
      self.log('CondorConfiguration.configure completed')
      return True
            
    if self.gram_gateway_enabled:

      # The accept_limited argument was added for Steve Timm.  We are not adding
      # it to the default config.ini template because we do not think it is
      # useful to a wider audience.
      # See VDT RT ticket 7757 for more information.
      if self.options['accept_limited'].value:
        if not self.enable_accept_limited(CondorConfiguration.CONDOR_CONFIG_FILE):
          self.log('Error writing to ' + CondorConfiguration.CONDOR_CONFIG_FILE,
                   level = logging.ERROR)
          self.log('CondorConfiguration.configure completed')
          return False
      else:
        if not self.disable_accept_limited(CondorConfiguration.CONDOR_CONFIG_FILE):
          self.log('Error writing to ' + CondorConfiguration.CONDOR_CONFIG_FILE,
                   level = logging.ERROR)
          self.log('CondorConfiguration.configure completed')
          return False

      if not self.setupGramConfig():
        self.log('Error writing to ' + CondorConfiguration.GRAM_CONFIG_FILE,
                 level = logging.ERROR)
        return False
      if self.__set_default:
        self.log('Configuring gatekeeper to use regular fork service')
        self.set_default_jobmanager('fork')

    if self.htcondor_gateway_enabled:
      if not self.setupHTCondorCEConfig():
        self.log('Error writing to ' + CondorConfiguration.HTCONDOR_CE_CONFIG_FILE,
                 level=logging.ERROR)
        return False

    self.log('CondorConfiguration.configure completed')
    return True    
    
  def moduleName(self):
    """Return a string with the name of the module"""
    return "Condor"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True

  def setupGramConfig(self):
    """
    Populate the gram config file with correct values
    
    Returns True if successful, False otherwise
    """

    buf = open(CondorConfiguration.GRAM_CONFIG_FILE).read()
    bin_location = os.path.join(self.options['condor_location'].value,
                                'bin',
                                'condor_submit')
    if validation.valid_file(bin_location):
      re_obj = re.compile('^condor_submit=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("condor_submit=\"%s\"" % bin_location, 
                                 buf,
                                 1)
      if count == 0:
        buf += "condor_submit=\"%s\"\n" % bin_location
    bin_location = os.path.join(self.options['condor_location'].value,
                                'bin',
                                'condor_rm')
    if validation.valid_file(bin_location):
      re_obj = re.compile('^condor_rm=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("condor_rm=\"%s\"" % bin_location,
                                 buf,
                                 1)
      if count == 0:
        buf += "condor_rm=\"%s\"\n" % bin_location
    if not utilities.blank(self.options['condor_config'].value):
      re_obj = re.compile('^condor_config=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("condor_config=\"%s\"" % 
                                 self.options['condor_config'].value,
                                 buf,
                                 1)
      if count == 0:
        buf += "condor_config=\"%s\"\n" % self.options['condor_config'].value
        
    
    if not utilities.atomic_write(CondorConfiguration.GRAM_CONFIG_FILE, buf):
      return False
    
    return True

  def setupHTCondorCEConfig(self):
    """
    Populate the config file that tells htcondor-ce where the condor
    pool is and where the spool directory is.

    Returns True if successful, False otherwise
    """
    if not utilities.rpm_installed('htcondor-ce'):
      self.log("Unable to configure htcondor-ce for Condor: htcondor-ce not installed", level=logging.ERROR)
      return False

    def add_or_replace(old_buf, variable, new_value):
      """
      If there is a line setting 'variable' in 'old_buf', change it to set
      variable to new_value. If there is no such line, add a line to the end
      of buf setting variable to new_value. Return the modified buf.
      """
      new_line = '%s=%s' % (variable, new_value)
      new_buf, count = re.subn(r'(?m)^\s*%s\s*=.*$' % re.escape(variable), new_line, old_buf, 1)
      if count == 0:
        new_buf += new_line + "\n"
      return new_buf

    def get_condor_ce_config_val(variable):
      return utilities.get_condor_config_val(variable, executable='condor_ce_config_val')

    # Get values for the settings we want to update. We can get the
    # values from condor_config_val; in the case of JOB_ROUTER_SCHEDD2_NAME,
    # we have FULL_HOSTNAME as a fallback in case SCHEDD_NAME is missing.
    # We also get the current / default value from condor_ce_config_val;
    # only update the setting in case the value from
    # condor_config_val is different from the value from condor_ce_config_val.
    condor_ce_config = {}
    for condor_ce_config_key, condor_config_keys in [
        ('JOB_ROUTER_SCHEDD2_NAME', ['SCHEDD_NAME', 'FULL_HOSTNAME']),
        ('JOB_ROUTER_SCHEDD2_POOL', ['COLLECTOR_HOST']),
        ('JOB_ROUTER_SCHEDD2_SPOOL', ['SPOOL'])]:

      condor_config_value = None
      for condor_config_value in (utilities.get_condor_config_val(k) for k in condor_config_keys):
        if condor_config_value:
          break

      condor_ce_config_value = get_condor_ce_config_val(condor_ce_config_key)
      if not (condor_config_value or condor_ce_config_value):
        self.log("Unable to determine value for %s from %s and default not set; check your Condor config" %
                 (condor_ce_config_key, ' or '.join(condor_config_keys)), level=logging.ERROR)
        return False
      elif not condor_ce_config_value or (condor_config_value and condor_ce_config_value != condor_config_value):
        condor_ce_config[condor_ce_config_key] = condor_config_value

    if condor_ce_config:
      buf = utilities.read_file(CondorConfiguration.HTCONDOR_CE_CONFIG_FILE,
                                default="# This file is managed by osg-configure\n")
      for key, value in condor_ce_config.items():
        buf = add_or_replace(buf, key, value)

      if not utilities.atomic_write(CondorConfiguration.HTCONDOR_CE_CONFIG_FILE, buf):
        return False

    return True


  @staticmethod
  def getCondorLocation(configuration):
    """
    Get the condor location based on the information in a configParser 
    object (configuration argument) and environment variables if possible
    """
    
    location = configfile.Option(name = 'condor_location',
                                 default_value = utilities.get_condor_location())
    configfile.get_option(configuration, 'Condor', location)
    return location.value

  @staticmethod
  def getCondorConfig(configuration):
    """
    Get the condor config location based on the information in a configParser 
    object (configuration argument) and environment variables if possible
    """
    
    location = configfile.Option(name = 'condor_config',
                                 required = configfile.Option.OPTIONAL,
                                 default_value = utilities.get_condor_config())
    configfile.get_option(configuration, 'Condor', location)
    return location.value
    
  def enabledServices(self):
    """Return a list of system services needed for module to work
    """
    if not self.enabled or self.ignored:
      return set()

    return set(['globus-gridftp-server']).union(self.gatewayServices())
