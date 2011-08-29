#!/usr/bin/python

""" Module to handle attributes related to the lsf jobmanager 
configuration """

import ConfigParser, os

from configure_osg.modules import utilities
from configure_osg.modules import configfile
from configure_osg.modules import validation
from configure_osg.modules import exceptions
from configure_osg.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['LSFConfiguration']

class LSFConfiguration(JobManagerConfiguration):
  """Class to handle attributes related to lsf job manager configuration"""
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(LSFConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('LSFConfiguration.__init__ started')    
    self.__mappings = {'lsf_location': 'OSG_LSF_LOCATION',
                       'job_contact': 'OSG_JOB_CONTACT',
                       'util_contact': 'OSG_UTIL_CONTACT',
                       'wsgram': 'OSG_WS_GRAM'}
    self.config_section = 'LSF'
    self.__using_prima = False
    self.logger.debug('LSFConfiguration.__init__ completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('LSFConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)
    
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug('LSF section not found in config file')
      self.logger.debug('LSFConfiguration.parseConfiguration completed')    
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('LSFConfiguration.parseConfiguration completed')    
      return True
       
    self.attributes['OSG_JOB_MANAGER'] = 'LSF'
    for setting in self.__mappings:
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)

    if configuration.getboolean(self.config_section, 'wsgram'):
      self.attributes[self.__mappings['wsgram']] = 'Y'
    else:
      self.attributes[self.__mappings['wsgram']] = 'N'      
     
    # set OSG_JOB_MANAGER_HOME
    self.attributes['OSG_JOB_MANAGER_HOME'] = \
      self.attributes[self.__mappings['lsf_location']]
      
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
      
    if (configuration.has_section('Misc Services') and
        configuration.has_option('Misc Services', 'authorization_method') and
        configuration.get('Misc Services', 'authorization_method') in ['xacml', 'prima']):
      self.__using_prima = True

    self.logger.debug('LSFConfiguration.parseConfiguration completed')    

  def getAttributes(self):
    """Return settings"""
    self.logger.debug('LSFConfiguration.getAttributes started')    
    if not self.enabled:
      self.logger.debug('LSF not enabled, returning empty dictionary')
      self.logger.debug('LSFConfiguration.parseConfiguration completed')    
      return {}
    self.logger.debug('LSFConfiguration.parseConfiguration completed')    
    return self.attributes
  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('LSFConfiguration.checkAttributes started')
    
    attributes_ok = True

    if not self.enabled:
      self.logger.debug('LSF not enabled, returning True')
      self.logger.debug('LSFConfiguration.checkAttributes completed')    
      return attributes_ok
    

    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('LSFConfiguration.checkAttributes completed')    
      return attributes_ok

    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        raise exceptions.SettingError("Missing setting for %s in %s section" % 
                                      (setting, self.config_section))

    # make sure locations exist
    if not validation.valid_location(self.attributes[self.__mappings['lsf_location']]):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      self.logger.error("%s points to non-existent location: %s" % 
                          ('lsf_location',
                           self.attributes[self.__mappings['lsf_location']]))

    if not self.validContact(self.attributes[self.__mappings['job_contact']], 
                             'lsf'):
      attributes_ok = False
      self.logger.error("%s is not a valid job contact: %s" % 
                        ('job_contact',
                         self.attributes[self.__mappings['job_contact']]))
      
    if not self.validContact(self.attributes[self.__mappings['util_contact']], 
                             'lsf'):
      attributes_ok = False
      self.logger.error("%s is not a valid util contact: %s" % 
                        ('util_contact',
                         self.attributes[self.__mappings['util_contact']]))
      
    if self.attributes[self.__mappings['wsgram']] not in ('Y', 'N'):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      self.logger.error("wsgram is not set correctly, it should be True or False")

    self.logger.debug('LSFConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('LSFConfiguration.configure started')
    # disable configuration for now
    self.logger.debug('LSF not enabled, returning True')    
    self.logger.debug('LSFConfiguration.configure completed')    
    return True
        
    if not self.enabled:
      self.logger.debug('LSF not enabled, returning True')    
      self.logger.debug('LSFConfiguration.configure completed')    
      return True

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('LSFConfiguration.configure completed')    
      return True

    self.logger.debug("Enabling gatekeeper service")
    if not utilities.enable_service('globus-gatekeeper'):
      self.logger.error("Error while enabling globus-gatekeeper")
      raise exceptions.ConfigureError("Error configuring globus-gatekeeper") 

    if self.attributes[self.__mappings['wsgram']] == 'Y':
      self.logger.debug("Enabling ws-gram")
      if not utilities.enable_service('globus-ws'):
        self.logger.error("Error while enabling globus-ws")
        raise exceptions.ConfigureError("Error configuring globus-gatekeeper")
      self.writeSudoExample(os.path.join(attributes['OSG_LOCATION'],
                                         'osg',
                                         'etc',
                                         'sudo-example.txt'),
                            attributes['GLOBUS_LOCATION'],
                            self.__using_prima)

    self.logger.debug('LSFConfiguration.configure started')    
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
