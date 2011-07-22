#!/usr/bin/python

""" Base class for all configuration classes """

import ConfigParser

__all__ = ['BaseConfiguration']


class BaseConfiguration(object):
  """Base class for inheritance by configuration"""
  # pylint: disable-msg=W0613
  def __init__(self, *args, **kwargs):
    self.attributes = {}
    self.logger = kwargs['logger']
    self.ignored = False
    self.enabled = False
    self.config_section = ""
      
  def setStatus(self, configuration):
    """
    Check the enable option and then set the appropriate attributes based on that.
    
    Returns False if the section is not enabled or set to ignore
    """
    
    try:
      if not configuration.has_option(self.config_section, 'enabled'):
        self.logger.debug("%s not enabled" % self.config_section)
        self.enabled = False
        return False
      elif configuration.get(self.config_section, 'enabled').lower() == 'ignore':
        self.logger.debug("%s will be ignored" % self.config_section)
        self.ignored  = True
        self.enabled = False
        return False
      elif not configuration.getboolean(self.config_section, 'enabled'):
        self.logger.debug("%s not enabled" % self.config_section)
        self.enabled = False
        return False
      else:
        self.enabled = True
        return True
    except ConfigParser.NoOptionError:
      raise exceptions.SettingError("Can't get value for enable option " \
                                    "in %s section" % self.config_section) 

    
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    pass

  def getAttributes(self):
    """Return settings"""
    return self.attributes

# pylint: disable-msg=W0613
# pylint: disable-msg=R0201
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    attributes_ok = True
    return attributes_ok 

# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""
    return True
  
# pylint: disable-msg=W0613
  def generateConfigFile(self, attribute_list, config_file):
    """Take a list of (key, value) tuples in attribute_list and add the 
    appropriate configuration options to the config file"""
    return config_file
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "BaseConfiguration"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return False
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return []
  
  def checkConfig(self, configuration):
    """
    Make sure config argument is of the correct type
    """
    
    if configuration is None or \
       (configuration.__class__.__name__ is not 'ConfigParser' and \
        configuration.__class__.__name__ is not 'SafeConfigParser'):
      raise TypeError('Invalid type for configuration, must be a ' + 
                      'ConfigParser or SafeConfigParser object')    