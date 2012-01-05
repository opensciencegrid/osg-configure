#!/usr/bin/python

""" Module to handle attributes related to the lsf jobmanager 
configuration """

import ConfigParser, os, re, types, logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules import exceptions
from osg_configure.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['LSFConfiguration']


class LSFConfiguration(JobManagerConfiguration):
  """Class to handle attributes related to lsf job manager configuration"""
  
  LSF_CONFIG_FILE = '/etc/grid-services/available/jobmanager-lsf'
  GRAM_CONFIG_FILE = '/etc/globus/globus-lsf.conf'

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(LSFConfiguration, self).__init__(*args, **kwargs)    
    self.log('LSFConfiguration.__init__ started')    
    # dictionary to hold information about options
    self.options = {'lsf_location' : configfile.Option(name = 'lsf_location',
                                                       default_value = '/usr',
                                                       mapping = 'OSG_LSF_LOCATION'),
                    'job_contact' : configfile.Option(name = 'job_contact',
                                                      mapping = 'OSG_JOB_CONTACT'),
                    'util_contact' : configfile.Option(name = 'util_contact',
                                                       mapping = 'OSG_UTIL_CONTACT'),
                    'seg_enabled' : configfile.Option(name = 'seg_enabled',
                                                      required = configfile.Option.OPTIONAL,
                                                      type = bool,
                                                      default_value = False),
                    'accept_limited' : configfile.Option(name = 'accept_limited',
                                                      required = configfile.Option.OPTIONAL,
                                                      type = bool,
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
       
    for option in self.options.values():
      self.log("Getting value for %s" % option.name)
      configfile.get_option(configuration,
                            self.config_section, 
                            option)
      self.log("Got %s" % option.value)

    # set OSG_JOB_MANAGER_HOME
    # set OSG_JOB_MANAGER and OSG_JOB_MANAGER_HOME
    self.options['job_manager'] = configfile.Option(name = 'job_manager',
                                                    value = 'LSF',
                                                    mapping = 'OSG_JOB_MANAGER')
    self.options['home'] = configfile.Option(name = 'job_manager_home',
                                             value = self.options['lsf_location'].value,
                                             mapping = 'OSG_JOB_MANAGER_HOME')
      
    # check and warn if unknown options found    
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.options.keys(),
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.log("Found unknown option",
               option = option, 
               section = self.config_section,
               level = logging.WARNING)
      
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
    buffer = open(LSFConfiguration.GRAM_CONFIG_FILE).read()
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'qsub')
    if validation.valid_file(bin_location):
      (buffer, count) = re.subn('^qsub=.*$', 
                                "qsub=\"%s\"" % bin_location, 
                                buffer, 
                                1)
      if count == 0:
        buffer = "qsub=\"%s\"\n" % bin_location + buffer
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'qstat')
    if validation.valid_file(bin_location):
      (buffer, count) = re.subn('^qstat=.*$',
                                "qstat=\"%s\"" % bin_location,
                                buffer,
                                1)
      if count == 0:
        buffer = "qstat=\"%s\"\n" % bin_location + buffer
    bin_location = os.path.join(self.options['lsf_location'].value,
                                'bin',
                                'qdel')
    if validation.valid_file(bin_location):
      (buffer, count) = re.subn('^qdel=.*$', "qdel=\"%s\"" % bin_location, 1)
      if count == 0:
        buffer = "qdel=\"%s\"\n" % bin_location + buffer
    if self.options['lsf_server'].value is not None:
      (buffer, count) = re.subn('^lsf_default=.*$',
                                "lsf_default=\"%s\"" % bin_location,
                                buffer,
                                1)
      if count == 0:
        buffer = "lsf_default=\"%s\"\n" % self.options['lsf_server'].value
        
    if self.options['seg_enabled'].value:
      if (self.options['log_directory'].value is None or
          not validation.valid_directory(self.options['log_directory'].value)):
        mesg = "%s is not a valid directory location " % self.options['log_directory'].value
        mesg += "for lsf_log files"
        self.logMessage(mesg, 
                        section = self.config_section,
                        option = 'log_directory',
                        level = logging.ERROR)
    
    if not utilities.atomic_write(LSFConfiguration.GRAM_CONFIG_FILE, buffer):
      return False
