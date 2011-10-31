#!/usr/bin/python

""" Module to handle attributes and configuration related to the condor 
jobmanager configuration """

import os, ConfigParser

from osg_configure.modules import utilities
from osg_configure.modules import validation
from osg_configure.modules import configfile
from osg_configure.modules import exceptions
from osg_configure.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['CondorConfiguration']

CONDOR_CONFIG_FILE = '/etc/grid-services/available/jobmanager-condor'


class CondorConfiguration(JobManagerConfiguration):
  """Class to handle attributes related to condor job manager configuration"""
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(CondorConfiguration, self).__init__(*args, **kwargs)
    self.logger.debug('CondorConfiguration.__init__ started')    
    self.config_section = "Condor"
    self.__mappings = {'condor_location': 'OSG_CONDOR_LOCATION',
                       'condor_config': 'OSG_CONDOR_CONFIG',
                       'job_contact': 'OSG_JOB_CONTACT',
                       'util_contact': 'OSG_UTIL_CONTACT',
                       'accept_limited': 'accept_limited'}
    self.__optional = ['condor_location',
                       'condor_config',
                       'accept_limited']
    self.__defaults = {'condor_location' : utilities.get_condor_location(),
                       'condor_config' : 'UNAVAILABLE',
                       'accept_limited' : 'False'}
    self.__set_default = True
    self.logger.debug('CondorConfiguration.__init__ completed')    
      
  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('CondorConfiguration.parseConfiguration started')

    self.checkConfig(configuration)
      
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('CondorConfiguration.parseConfiguration completed')
      return

    if not self.setStatus(configuration):
      self.logger.debug('CondorConfiguration.parseConfiguration completed')
      return True
           
    self.attributes['OSG_JOB_MANAGER'] = 'Condor'

    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting, 
                                   self.__optional, 
                                   self.__defaults)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)  

    if (not configuration.has_option(self.config_section, 'condor_location') or
        utilities.blank(configuration.get(self.config_section, 'condor_location'))):
      # Warn admin that condor_location was set from an environment variable
      self.logger.debug("Set condor location from an environment variable")
      
    if (self.__mappings['condor_config'] not in self.attributes or
        utilities.blank(self.attributes[self.__mappings['condor_config']])):
      if (self.__mappings['condor_location'] in self.attributes and
          not utilities.blank(self.attributes[self.__mappings['condor_location']])):
        temp = os.path.join(self.attributes[self.__mappings['condor_location']], 
                            "etc", 
                            "condor_config")
      else:
        temp = ""
      self.attributes[self.__mappings['condor_config']] = \
        utilities.get_condor_config(temp)
      


    self.attributes['OSG_JOB_MANAGER_HOME'] = \
      self.attributes[self.__mappings['condor_location']]
      
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
      
    if (configuration.has_section('Managed Fork') and
        configuration.has_option('Managed Fork', 'enabled') and
        configuration.get('Managed Fork', 'enabled').upper() == 'TRUE'):
      self.__set_default = False

    self.logger.debug('CondorConfiguration.parseConfiguration completed')        

  def getAttributes(self):
    """Return settings"""
    self.logger.debug('CondorConfiguration.getAttributes started')
    if not self.enabled:
      self.logger.debug('not enabled, returning empty dictionary')
      return {}
    self.logger.debug('CondorConfiguration.getAttributes finished')
    return self.attributes
  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('CondorConfiguration.checkAttributes started')

    if not self.enabled:
      self.logger.debug('CondorConfiguration.checkAttributes completed returning True')
      return True
    
    if self.ignored:
      self.logger.debug('CondorConfiguration.checkAttributes completed returning True')
      return True

    attributes_ok = True
    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        self.logger.error("In [Condor] section: %s option is not present" % setting)
        raise exceptions.SettingError("Missing setting for %s in %s section" %
                                      (setting, self.config_section))

    # make sure locations exist
    self.logger.debug('checking condor_location')
    if not validation.valid_location(self.attributes[self.__mappings['condor_location']]):
      attributes_ok = False
      self.logger.error("%s points to non-existent location: %s" % 
                        ('condor_location',
                         self.attributes[self.__mappings['condor_location']]))

    self.logger.debug('checking condor_config')
    if not validation.valid_file(self.attributes[self.__mappings['condor_config']]):
      attributes_ok = False
      self.logger.error("%s points to non-existent location: %s" % 
                        ('condor_config',
                         self.attributes[self.__mappings['condor_config']]))

    if not self.validContact(self.attributes[self.__mappings['job_contact']], 
                             'condor'):
      attributes_ok = False
      self.logger.error("%s is not a valid job contact: %s" % 
                        ('job_contact',
                         self.attributes[self.__mappings['job_contact']]))
      
    if not self.validContact(self.attributes[self.__mappings['util_contact']], 
                             'condor'):
      attributes_ok = False
      self.logger.error("%s is not a valid util contact: %s" % 
                        ('util_contact',
                         self.attributes[self.__mappings['util_contact']]))


    self.logger.debug('CondorConfiguration.checkAttributes completed returning %s' \
                       % attributes_ok)
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('CondorConfiguration.configure started')

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('CondorConfiguration.configure completed')
      return True

    if not self.enabled:
      self.logger.debug('condor not enabled')
      self.logger.debug('CondorConfiguration.configure completed')
      return True
            
    # The accept_limited argument was added for Steve Timm.  We are not adding
    # it to the default config.ini template because we do not think it is
    # useful to a wider audience.
    # See VDT RT ticket 7757 for more information.
    if self.attributes[self.__mappings['accept_limited']].upper() == "TRUE":
      if not self.enable_accept_limited(CONDOR_CONFIG_FILE):
          self.logger.error('Error writing to condor configuration')
          self.logger.debug('CondorConfiguration.configure completed')
          return False
    elif self.attributes[self.__mappings['accept_limited']].upper() == "FALSE":
      if not self.disable_accept_limited(CONDOR_CONFIG_FILE):
          self.logger.error('Error writing to condor configuration')
          self.logger.debug('CondorConfiguration.configure completed')
          return False
      
    if self.__set_default:
        self.logger.debug('Configuring gatekeeper to use regular fork service')
        self.set_default_jobmanager('fork')
      
    self.logger.debug('CondorConfiguration.configure completed')
    return True    
    
  def moduleName(self):
    """Return a string with the name of the module"""
    return "Condor"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True

  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]  
