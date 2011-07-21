#!/usr/bin/python

""" Module to handle attributes and configuration related to the condor 
jobmanager configuration """

import os, ConfigParser

from configure_osg.modules import utilities
from configure_osg.modules import exceptions
from configure_osg.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['CondorConfiguration']

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
                       'wsgram': 'OSG_WS_GRAM'}
    self.__optional = ['condor_location',
                       'condor_config',
                       'wsgram']
    self.__defaults = {'wsgram' : 'Y',
                       'condor_location' : utilities.get_condor_location(),
                       'condor_config' : 'UNAVAILABLE'}
    self.__using_prima = False
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
      temp = utilities.get_option(configuration, 
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
      
    if configuration.getboolean(self.config_section, 'wsgram'):
      self.attributes[self.__mappings['wsgram']] = 'Y'
    else:
      self.attributes[self.__mappings['wsgram']] = 'N'
    
        
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
    if not utilities.valid_location(self.attributes[self.__mappings['condor_location']]):
      attributes_ok = False
      self.logger.error("%s points to non-existent location: %s" % 
                        ('condor_location',
                         self.attributes[self.__mappings['condor_location']]))

    self.logger.debug('checking condor_config')
    if not utilities.valid_file(self.attributes[self.__mappings['condor_config']]):
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

    self.logger.debug('checking wsgram')
    if self.attributes[self.__mappings['wsgram']] not in ('Y', 'N'):
      attributes_ok = False
      self.logger.error("%s is not set correctly, it should be True or False")

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
    
    self.logger.debug("Enabling globus gatekeeper")
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
        
      
    self.logger.debug('CondorConfiguration.configure completed')
    return True
  
  def generateConfigFile(self, attribute_list, config_file):
    """Take a list of (key, value) tuples in attribute_list and add the 
    appropriate configuration options to the config file"""

    self.logger.debug("CondorConfiguration.generateConfigFile started")
    # generate reverse mapping so that we can create the appropriate options
    reverse_mapping = {}
    for key in self.__mappings:
      reverse_mapping[self.__mappings[key]] = key
      
    if not config_file.has_section(self.config_section):
      self.logger.debug("Adding %s section to configuration file" % self.config_section)
      config_file.add_section(self.config_section)
      
    for (key, value) in attribute_list:
      if key in reverse_mapping:
        self.logger.debug("Found %s in reverse mapping with value %s" % (key, value))
        self.logger.debug("Mapped to %s" % reverse_mapping[key])
        config_file.set(self.config_section, reverse_mapping[key], value)
      if key == "OSG_JOB_MANAGER" and value.lower() != "condor":
        self.logger.debug('Condor not job manager, removing Condor section')
        config_file.remove_section(self.config_section)
        self.logger.debug("CondorConfiguration.generateConfigFile completed")    
        return config_file

    if  not config_file.has_option(self.config_section, 'condor_location'):
      # no settings for this job manager, delete section
      # this is needed since all job managers will see various settings and add it
      self.logger.debug('Condor not enabled, removing Condor section')
      config_file.remove_section(self.config_section)
    else:
      config_file.set(self.config_section, 'enabled', 'True')
      if (config_file.has_option(self.config_section, 'wsgram') and
          config_file.get(self.config_section, 'wsgram').upper() == 'N'):
        config_file.set(self.config_section, 'wsgram', 'False')
      else:
        config_file.set(self.config_section, 'wsgram', 'True')            
    
    self.logger.debug("CondorConfiguration.generateConfigFile completed")    
    return config_file
  
    
  def moduleName(self):
    """Return a string with the name of the module"""
    return "Condor"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True

  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]  
