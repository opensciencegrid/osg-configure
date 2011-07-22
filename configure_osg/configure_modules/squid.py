#!/usr/bin/python

""" Module to handle squid configuration and setup """

import ConfigParser, os

from configure_osg.modules import exceptions
from configure_osg.modules import utilities
from configure_osg.modules.configurationbase import BaseConfiguration

__all__ = ['SquidConfiguration']


class SquidConfiguration(BaseConfiguration):
  """Class to handle attributes related to squid configuration and setup"""
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(SquidConfiguration, self).__init__(*args, **kwargs)
    self.logger.debug('SquidConfiguration.__init__ started')
    self.attributes = {'OSG_SQUID_LOCATION' : 'UNAVAILABLE',
                       'OSG_SQUID_POLICY' : 'UNAVAILABLE',
                       'OSG_SQUID_CACHE_SIZE' : 'UNAVAILABLE',
                       'OSG_SQUID_MEM_CACHE' : 'UNAVAILABLE'}        
    self.__mappings = {'location': 'OSG_SQUID_LOCATION', 
                       'policy': 'OSG_SQUID_POLICY',
                       'cache_size': 'OSG_SQUID_CACHE_SIZE',
                       'memory_size': 'OSG_SQUID_MEM_CACHE'}
    self.__local_dir = None
    self.config_section = 'Squid'
    self.logger.debug('SquidConfiguration.__init__ completed')
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('SquidConfiguration.parseConfiguration started')
    
    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('SquidConfiguration.parseConfiguration completed')
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('RsvConfiguration.parseConfiguration completed')    
      return True

    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = utilities.get_option(configuration, 
                                  self.config_section, 
                                  setting)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)
    
    if (self.enabled and 
        self.attributes[self.__mappings['location']] is not None):
      location = self.attributes[self.__mappings['location']]
      if '/' in location:
        self.__local_dir = location
        self.attributes[self.__mappings['location']] = \
          "%s:3128" % utilities.get_hostname()        
      elif ":" not in location:        
        self.attributes[self.__mappings['location']] += ":3128"        
        
      
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))   
    self.logger.debug('SquidConfiguration.parseConfiguration completed')

  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('SquidConfiguration.checkAttributes started')
    attributes_ok = True
    if not self.enabled:
      self.logger.debug('squid not enabled')
      self.logger.debug('SquidConfiguration.checkAttributes completed')
      return attributes_ok

    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('SquidConfiguration.checkAttributes completed')
      return attributes_ok

    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        raise exceptions.SettingError("Missing setting for %s in %s section" %
                                      (setting, self.config_section)) 
    if (self.__local_dir is not None and
        not utilities.valid_location(self.__local_dir)):
      self.logger.error("In %s section" % self.config_section)
      self.logger.error("Value given in location does not exist: %s" % 
                          self.attributes[self.__mappings['location']])
      attributes_ok = False
    (hostname, port) = self.attributes[self.__mappings['location']].split(':')
    if not utilities.valid_domain(hostname, True):
      self.logger.error("In %s section, problem with hostname setting" % self.config_section)
      self.logger.error("Can't invalid hostname for squid location: %s" % \
                        self.attributes[self.__mappings['location']])
      attributes_ok = False
    try:
      int(port)
    except ValueError:
      self.logger.error("In %s section, problem with squid location setting" % \
                        self.config_section)
      self.logger.error("The port must be a number(e.g. host:3128) for squid " \
                        "location: %s" % self.attributes[self.__mappings['location']])
      
      attributes_ok = False
    
    if not utilities.blank(self.attributes[self.__mappings['memory_size']]):
      try:
        int(self.attributes[self.__mappings['memory_size']])
      except ValueError:
        self.logger.error("In %s section, memory_size must be an integer " \
                          "giving the in memory size of the squid " \
                          "proxy in MB" % self.config_section)      
        attributes_ok = False

    if not utilities.blank(self.attributes[self.__mappings['cache_size']]):
      try:
        int(self.attributes[self.__mappings['cache_size']])
      except ValueError:
        self.logger.error("In %s section, cache_size must be an integer " \
                          "giving the disk cache size of the squid " \
                          "proxy in MB" % self.config_section)      
        attributes_ok = False
        
    self.logger.debug('SquidConfiguration.checkAttributes completed')
    return attributes_ok 
  
# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('SquidConfiguration.configure started')

    if not self.enabled:
      self.logger.debug('squid not enabled')
      self.logger.debug('SquidConfiguration.configure completed')
      return True

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('SquidConfiguration.configure completed')
      return True

    arguments = [os.path.join(utilities.get_vdt_location(),
                              'vdt',
                              'setup',
                              'configure_squid')]
    arguments.append('--server')
    arguments.append(' ')
    arguments.append('y')
    
    if self.attributes[self.__mappings['location']][0] == '/' and \
       self.attributes[self.__mappings['location']].startswith(utilities.get_vdt_location()):
      # squid is installed on the server and is part of this installation
      arguments.append("--mem-cache-size")
      arguments.append(" ")
      arguments.append(self.attributes[self.__mappings['memory_size']])
      arguments.append("--cache-size")
      arguments.append(" ")
      arguments.append(self.attributes[self.__mappings['cache_size']])
      self.logger.info("Running configure_squid as: %s" % (" ".join(arguments)))
      if not utilities.run_vdt_configure(arguments):
        self.logger.error("Error while configuring squid")
        raise exceptions.ConfigureError("Error configuring squid")
    self.logger.debug('SquidConfiguration.configure completed')
    return True     

  def generateConfigFile(self, attribute_list, config_file):
    """Take a list of (key, value) tuples in attribute_list and add the 
    appropriate configuration options to the config file"""
    
    self.logger.debug("SquidConfiguration.generateConfigFile started")
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
        
    if (config_file.has_option(self.config_section, 'location') and
        config_file.get(self.config_section, 'location').upper() == 'UNAVAILABLE'):
      config_file.set(self.config_section, 'enabled', 'False')
    elif not config_file.has_option(self.config_section, 'location'):
      config_file.set(self.config_section, 'enabled', 'False')
    else:
      config_file.set(self.config_section, 'enabled', 'True')
    
    if config_file.getboolean(self.config_section, 'enabled'):
      self.logger.debug('Not enabled, setting all options to UNAVAILABLE')
      for key in self.__mappings:
        if not config_file.has_option(self.config_section, key):
          config_file.set(self.config_section, 'enabled', 'UNAVAILABLE')
    
    self.logger.debug("SquidConfiguration.generateConfigFile completed")    
    return config_file   

  def moduleName(self):
    """Return a string with the name of the module"""
    return "Squid"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
