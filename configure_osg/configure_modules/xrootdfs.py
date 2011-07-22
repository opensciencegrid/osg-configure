#!/usr/bin/python

"""
Module to handle attributes related to the bestman configuration 
"""


import re, ConfigParser

from configure_osg.modules import utilities
from configure_osg.modules import exceptions
from configure_osg.modules.configurationbase import BaseConfiguration

__all__ = ['XrootdFSConfiguration']

class XrootdFSConfiguration(BaseConfiguration):
  """
  Class to handle attributes related to XRootdFS configuration
  """
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(XrootdFSConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('XrootdFSConfiguration.__init__ started')    
    self.__mappings = {'user' : 'user',
                       'redirector_host' : 'redirector_host',
                       'mount_point' : 'mount_point',
                       'redirector_storage_path' : 'redirector_storage_path'}
    self.config_section = "XrootdFS"
    self.logger.debug('XrootdFSConfiguration.__init__ completed')    
    
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('XrootdFSConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('XrootdFS.parseConfiguration completed')
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('XrootdFS.parseConfiguration completed')
      return True
       
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = utilities.get_option(configuration, 
                                  self.config_section, 
                                  setting)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)

    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
    self.logger.debug('XrootdFSConfiguration.parseConfiguration completed')    

  def getAttributes(self):
    """Return settings"""
    self.logger.debug('XrootdFSConfiguration.getAttributes started')    
    self.logger.debug('XrootdFSConfiguration.getAttributes completed')    
    return {}

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('XrootdFSConfiguration.checkAttributes started')
    attributes_ok = True
    if not self.enabled:
      self.logger.debug('Not enabled, return True')
      self.logger.debug('XrootdFSConfiguration.checkAttributes completed')
      return attributes_ok
    
    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('XrootdFSConfiguration.checkAttributes completed')
      return attributes_ok
    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        raise exceptions.SettingError("Missing setting for %s in % section" %
                                      (setting, self.config_section))

    if not utilities.valid_user(self.attributes['user']):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      self.logger.error("user does not give a valid user: %s" % 
                        (self.attributes['user']))
      
    
    if not utilities.valid_domain(self.attributes['redirector_host'], True):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      err_msg = "redirector_host should point to a valid domain "
      err_msg += "got %s instead" % (self.attributes['redirector_host'])
      self.logger.error(err_msg)
      
    if utilities.blank(self.attributes['redirector_storage_path']):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      self.logger.error("redirector_storage_cache must be specified")

    if not utilities.valid_location(self.attributes['mount_point']):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      err_msg = "mount_point should point to a valid location "
      err_msg += "got %s instead" % (self.attributes['mount_point'])
      self.logger.error(err_msg)
      
    self.logger.debug('XrootdFSConfiguration.checkAttributes completed')
    return attributes_ok 

# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('XrootdFSConfiguration.configure started')
    
    if not self.enabled:
      self.logger.debug('XrootdFS not enabled')
      self.logger.debug('XrootdFSConfiguration.configure completed')
      return True

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('XrootdFSConfiguration.configure completed')
      return True

    arguments = ['--user',
                 self.attributes['user'],
                 '--xrdr-storage-path',
                 self.attributes['redirector_storage_path'],
                 '--cache',
                 self.attributes['mount_point'],
                 '--xrdr-host',
                 self.attributes['redirector_host']]
          
    if not utilities.configure_service('configure_xrootdfs', 
                                       arguments):
      self.logger.error("Error configuring xrootdfs")
      raise exceptions.ConfigureError("Error configuring XrootdFS")    

    self.logger.debug('Enabling XrootdFS')
    if not utilities.enable_service('xrootdfs'):
      self.logger.error("Error while enabling xrootdfs")
      raise exceptions.ConfigureError("Error configuring XrootdFS")    
    self.logger.debug('XrootdFSConfiguration.configure completed')    
    return True
  
  def generateConfigFile(self, attribute_list, config_file):
    """Take a list of (key, value) tuples in attribute_list and add the 
    appropriate configuration options to the config file"""
    # generate reverse mapping so that we can create the appropriate options
    self.logger.debug("XrootdFSConfiguration.generateConfigFile started")
    reverse_mapping = {}
    for key in self.__mappings:
      reverse_mapping[self.__mappings[key]] = key
      
    if not config_file.has_section(self.config_section):
      self.logger.debug("Adding %s section to configuration file" % self.config_section)
      config_file.add_section(self.config_section)
      
    for (key, value) in attribute_list:
      if key in reverse_mapping:
        if value.upper() == 'Y':
          self.logger.debug("Found %s in reverse mapping with value True" % (key))
          self.logger.debug("Mapped to %s" % reverse_mapping[key])
          config_file.set(self.config_section, reverse_mapping[key], 'True')
        elif value.upper() == 'N':
          self.logger.debug("Found %s in reverse mapping with value False" % (key))
          self.logger.debug("Mapped to %s" % reverse_mapping[key])
          config_file.set(self.config_section, reverse_mapping[key], 'False')
        else:
          self.logger.debug("Found %s in reverse mapping with value %s" % (key, value))
          self.logger.debug("Mapped to %s" % reverse_mapping[key])
          config_file.set(self.config_section, reverse_mapping[key], value)        
    
    self.logger.debug("XrootdFSConfiguration.generateConfigFile completed")    
    return config_file

  def moduleName(self):
    """
    Return a string with the name of the module
    """
    return "XrootdFS"
  
  def separatelyConfigurable(self):
    """
    Return a boolean that indicates whether this module can be configured separately
    """
    return True
  
  def parseSections(self):
    """
    Returns the sections from the configuration file that this module handles
    """
    return [self.config_section]
  
  
  def __check_tokens(self, token_list):
    """
    Returns True or False depending whether the token_list is a valid list
    of space tokens. 
    A valid list consists of gsiftp urls separated by commas, 
    e.g. gsiftp://server1.example.com,gsiftp://server2.example.com:2188
    """
    
    valid = True
    token_regex = re.compile('[a-zA-Z0-9]+\[desc:[A-Za-z0-9]+\]\[\d+\]')
    for token in [token.strip() for token in token_list.split(';')]:
      if token == "":
        continue
      match = token_regex.match(token)
      if match is None:
        valid = False
        self.logger.error("In %s section:" % self.config_section)
        error = "%s is a malformed token in "  % token 
        error += "token_list setting"
        self.logger.error(error)
    return valid
