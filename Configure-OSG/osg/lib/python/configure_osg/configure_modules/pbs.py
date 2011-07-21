#!/usr/bin/python

""" Module to handle attributes related to the pbs jobmanager 
configuration """

import ConfigParser, os

from configure_osg.modules import utilities
from configure_osg.modules import exceptions
from configure_osg.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['PBSConfiguration']

class PBSConfiguration(JobManagerConfiguration):
  """Class to handle attributes related to pbs job manager configuration"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(PBSConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('PBSConfiguration.__init__ started')    
    self.__using_prima = False
    self.__mappings = {'pbs_location': 'OSG_PBS_LOCATION',
                       'job_contact': 'OSG_JOB_CONTACT',
                       'util_contact': 'OSG_UTIL_CONTACT',
                       'wsgram': 'OSG_WS_GRAM'}
    self.config_section = "PBS"
    self.logger.debug('PBSConfiguration.__init__ completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('PBSConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.logger.debug('PBS section not found in config file')
      self.logger.debug('PBSConfiguration.parseConfiguration completed')    
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('PBSConfiguration.parseConfiguration completed')    
      return True

    
    self.attributes['OSG_JOB_MANAGER'] = 'PBS'
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)        
      temp = utilities.get_option(configuration, 
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
      self.attributes[self.__mappings['pbs_location']]

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
      
    self.logger.debug('PBSConfiguration.parseConfiguration completed')    

  def getAttributes(self):
    """Return settings"""
    self.logger.debug('PBSConfiguration.getAttributes started')    
    if not self.enabled:
      self.logger.debug('PBS not enabled, returning empty dictionary')
      self.logger.debug('PBSConfiguration.parseConfiguration completed')    
      return {}
    self.logger.debug('PBSConfiguration.parseConfiguration completed')    
    return self.attributes
  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('PBSConfiguration.checkAttributes started')    

    attributes_ok = True

    if not self.enabled:
      self.logger.debug('PBS not enabled, returning True')
      self.logger.debug('PBSConfiguration.checkAttributes completed')    
      return attributes_ok
    
    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('PBSConfiguration.checkAttributes completed')    
      return attributes_ok

    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        raise exceptions.SettingError("Missing setting for %s in %s section " % 
                                      (setting, self.config_section))

    # make sure locations exist
    if not utilities.valid_location(self.attributes[self.__mappings['pbs_location']]):
      attributes_ok = False
      self.logger.warning("%s points to non-existent location: %s" % 
                          ('pbs_location',
                           self.attributes[self.__mappings['pbs_location']]))

    if not self.validContact(self.attributes[self.__mappings['job_contact']], 
                             'pbs'):
      attributes_ok = False
      self.logger.error("%s is not a valid job contact: %s" % 
                        ('job_contact',
                         self.attributes[self.__mappings['job_contact']]))
      
    if not self.validContact(self.attributes[self.__mappings['util_contact']], 
                             'pbs'):
      attributes_ok = False
      self.logger.error("%s is not a valid util contact: %s" % 
                        ('util_contact',
                         self.attributes[self.__mappings['util_contact']]))
            
    if self.attributes[self.__mappings['wsgram']] not in ('Y', 'N'):
      attributes_ok = False
      self.logger.warning("%s is not set correctly, it should be True or False")
      
    
    self.logger.debug('PBSConfiguration.checkAttributes completed')    
    return attributes_ok 
  
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('PBSConfiguration.configure started')
    
    if not self.enabled:
      self.logger.debug('PBS not enabled, returning True')
      self.logger.debug('PBSConfiguration.configure completed')    
      return True

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('PBSConfiguration.configure completed')    
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
      
    self.logger.debug('PBSConfiguration.configure completed')    
    return True

  
  def generateConfigFile(self, attribute_list, config_file):
    """Take a list of (key, value) tuples in attribute_list and add the 
    appropriate configuration options to the config file"""
    # generate reverse mapping so that we can create the appropriate options
    self.logger.debug("PBSConfiguration.generateConfigFile started")
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
      if key == "OSG_JOB_MANAGER" and value.lower() != "pbs":
        self.logger.debug('PBS not job manager, removing PBS section')
        config_file.remove_section(self.config_section)
        self.logger.debug("PBSConfiguration.generateConfigFile completed")    
        return config_file

    if  not config_file.has_option(self.config_section, 'pbs_location'):
      # no settings for this job manager, delete section
      # this is needed since all job managers will see various settings and add it
      self.logger.debug('PBS not enabled, removing PBS section')
      config_file.remove_section(self.config_section)
    else:
      config_file.set(self.config_section, 'enabled', 'True')
      if (config_file.has_option(self.config_section, 'wsgram') and
          config_file.get(self.config_section, 'wsgram').upper() == 'N'):
        config_file.set(self.config_section, 'wsgram', 'False')
      else:
        config_file.set(self.config_section, 'wsgram', 'True')
    
    self.logger.debug("PBSConfiguration.generateConfigFile completed")    
    return config_file
  

  def moduleName(self):
    """Return a string with the name of the module"""
    return "PBS"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
