""" Module to handle attributes related to the lsf jobmanager 
configuration """

import os
import re
import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['LSFConfiguration']


class LSFConfiguration(JobManagerConfiguration):
  """Class to handle attributes related to lsf job manager configuration"""
  
  LSF_CONFIG_FILE = '/etc/grid-services/available/jobmanager-lsf-seg'
  GRAM_CONFIG_FILE = '/etc/globus/globus-lsf.conf'

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(LSFConfiguration, self).__init__(*args, **kwargs)    
    self.log('LSFConfiguration.__init__ started')    
    # dictionary to hold information about options
    self.options = {'lsf_location' : 
                      configfile.Option(name = 'lsf_location',
                                        default_value = '/usr',
                                        mapping = 'OSG_LSF_LOCATION'),
                    'lsf_profile' : 
                      configfile.Option(name = 'lsf_profile'),
                    'job_contact' : 
                      configfile.Option(name = 'job_contact',
                                        mapping = 'OSG_JOB_CONTACT'),
                    'util_contact' : 
                      configfile.Option(name = 'util_contact',
                                        mapping = 'OSG_UTIL_CONTACT'),
                    'seg_enabled' : 
                      configfile.Option(name = 'seg_enabled',
                                        required = configfile.Option.OPTIONAL,
                                        opt_type = bool,
                                        default_value = False),
                    'log_directory' : 
                      configfile.Option(name = 'log_directory',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = ''),
                    'accept_limited' : configfile.Option(name = 'accept_limited',
                                                      required = configfile.Option.OPTIONAL,
                                                      opt_type = bool,
                                                      default_value = False)}    
    self.config_section = 'LSF'
    self.__set_default = True

    self.log('LSFConfiguration.__init__ completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.log('LSFConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)
    
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log('LSF section not found in config file')
      self.log('LSFConfiguration.parseConfiguration completed')    
      return
    
    if not self.setStatus(configuration):
      self.log('LSFConfiguration.parseConfiguration completed')    
      return True
       
    self.getOptions(configuration, ignore_options = ['enabled'])

    # set OSG_JOB_MANAGER_HOME
    # set OSG_JOB_MANAGER and OSG_JOB_MANAGER_HOME
    self.options['job_manager'] = configfile.Option(name = 'job_manager',
                                                    value = 'LSF',
                                                    mapping = 'OSG_JOB_MANAGER')
    self.options['home'] = configfile.Option(name = 'job_manager_home',
                                             value = self.options['lsf_location'].value,
                                             mapping = 'OSG_JOB_MANAGER_HOME')

    if (configuration.has_section('Managed Fork') and
        configuration.has_option('Managed Fork', 'enabled') and
        configuration.getboolean('Managed Fork', 'enabled')):
      self.__set_default = False

    self.log('LSFConfiguration.parseConfiguration completed')    

  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('LSFConfiguration.checkAttributes started')
    
    attributes_ok = True

    if not self.enabled:
      self.log('LSF not enabled, returning True')
      self.log('LSFConfiguration.checkAttributes completed')    
      return attributes_ok
    

    if self.ignored:
      self.log('Ignored, returning True')
      self.log('LSFConfiguration.checkAttributes completed')    
      return attributes_ok


    # make sure locations exist
    if not validation.valid_location(self.options['lsf_location'].value):
      attributes_ok = False
      self.log("Non-existent location given: %s" % 
                          (self.options['lsf_location'].value),
                option = 'lsf_location',
                section = self.config_section,
                level = logging.ERROR)

    if not validation.valid_file(self.options['lsf_profile'].value):
      attributes_ok = False
      self.log("Non-existent location given: %s" % 
                          (self.options['lsf_profile'].value),
                option = 'lsf_profile',
                section = self.config_section,
                level = logging.ERROR)

    if not self.validContact(self.options['job_contact'].value, 
                             'lsf'):
      attributes_ok = False
      self.log("Invalid job contact: %s" % 
                         (self.options['job_contact'].value),
               option = 'job_contact',
               section = self.config_section,
               level = logging.ERROR)
      
    if not self.validContact(self.options['util_contact'].value, 
                             'lsf'):
      attributes_ok = False
      self.log("Invalid util contact: %s" % 
                        (self.options['util_contact'].value),
               option = 'util_contact',
               section = self.config_section,
               level = logging.ERROR)
      
    self.log('LSFConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('LSFConfiguration.configure started')
        
    if not self.enabled:
      self.log('LSF not enabled, returning True')    
      self.log('LSFConfiguration.configure completed')    
      return True

    if self.ignored:
      self.log("%s configuration ignored" % self.config_section, 
               level = logging.WARNING)
      self.log('LSFConfiguration.configure completed')    
      return True

    # The accept_limited argument was added for Steve Timm.  We are not adding
    # it to the default config.ini template because we do not think it is
    # useful to a wider audience.
    # See VDT RT ticket 7757 for more information.
    if self.options['accept_limited'].value:
      if not self.enable_accept_limited(LSFConfiguration.LSF_CONFIG_FILE):
        self.log('Error writing to ' + LSFConfiguration.LSF_CONFIG_FILE, 
                 level = logging.ERROR)
        self.log('LSFConfiguration.configure completed')
        return False
    elif self.options['accept_limited'].value:
      if not self.disable_accept_limited(LSFConfiguration.LSF_CONFIG_FILE):
        self.log('Error writing to ' + LSFConfiguration.LSF_CONFIG_FILE, 
                 level = logging.ERROR)
        self.log('LSFConfiguration.configure completed')
        return False

    if not self.options['seg_enabled'].value:
      self.log("SEG must be enabled for LSF jobmanager",
                option = 'seg_enabled',
                section = self.config_section,
                level = logging.ERROR)
    self.enable_seg('lsf', LSFConfiguration.LSF_CONFIG_FILE)
    if not self.setupGramConfig():
      self.log('Error writing to ' + LSFConfiguration.GRAM_CONFIG_FILE,
               level = logging.ERROR)
      return False

    if self.__set_default:
      self.log('Configuring gatekeeper to use regular fork service')
      self.set_default_jobmanager('fork')

    self.log('LSFConfiguration.configure started')    
    return True
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "LSF"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True

  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]  

  def setupGramConfig(self):
    """
    Populate the gram config file with correct values
    
    Returns True if successful, False otherwise
    """    
    buf = open(LSFConfiguration.GRAM_CONFIG_FILE).read()
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'bsub')
    if validation.valid_file(bin_location):
      re_obj = re.compile('^bsub=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("bsub=\"%s\"" % bin_location, 
                                 buf, 
                                 1)
      if count == 0:
        buf += "bsub=\"%s\"\n" % bin_location
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'bqueues')
    if validation.valid_file(bin_location):
      re_obj = re.compile('^bqueues=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("bqueues=\"%s\"" % bin_location,
                                 buf,
                                 1)
      if count == 0:
        buf += "bqueues=\"%s\"\n" % bin_location
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'bjobs')
    if validation.valid_file(bin_location):
      re_obj = re.compile('^bjobs=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("bjobs=\"%s\"" % bin_location,
                                 buf,
                                 1)
      if count == 0:
        buf += "bjobs=\"%s\"\n" % bin_location
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'bhist')
    if validation.valid_file(bin_location):
      re_obj = re.compile('^bhist=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("bhist=\"%s\"" % bin_location,
                                 buf,
                                 1)
      if count == 0:
        buf += "bhist=\"%s\"\n" % bin_location
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'bacct')
    if validation.valid_file(bin_location):
      re_obj = re.compile('^bacct=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("bacct=\"%s\"" % bin_location,
                                 buf,
                                 1)
      if count == 0:
        buf += "bacct=\"%s\"\n" % bin_location
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'bkill')
    if validation.valid_file(bin_location):
      re_obj = re.compile('^bkill=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn("bkill=\"%s\"" % bin_location, buf, 1)
      if count == 0:
        buf += "bkill=\"%s\"\n" % bin_location
        
    if self.options['seg_enabled'].value:
      if (self.options['log_directory'].value is None or
          not validation.valid_directory(self.options['log_directory'].value)):
        mesg = "%s is not a valid directory location " % self.options['log_directory'].value
        mesg += "for lsf log files"
        self.log(mesg, 
                 section = self.config_section,
                 option = 'log_directory',
                 level = logging.ERROR)
        return False

      new_setting = "log_path=\"%s\"" % self.options['log_directory'].value
      re_obj = re.compile('^log_path=.*$', re.MULTILINE)
      (buf, count) = re_obj.subn(new_setting, buf, 1)
      if count == 0:
        buf += new_setting + "\n"
    
    new_setting = "lsf_profile=\"%s\"" % self.options['lsf_profile'].value
    re_obj = re.compile('^lsf_profile=.*$', re.MULTILINE)
    (buf, count) = re_obj.subn(new_setting, buf, 1)
    if count == 0:
      buf += new_setting + "\n"
      
    if not utilities.atomic_write(LSFConfiguration.GRAM_CONFIG_FILE, buf):
      return False
    return True

  def enabledServices(self):
    """Return a list of  system services needed for module to work
    """

    if not self.enabled or self.ignored:
      return set()
    
    services = set(['globus-gatekeeper', 'globus-gridftp-server'])
    if self.options['seg_enabled'].value:
      services.add('globus-scheduler-event-generator')
    return services 
  

