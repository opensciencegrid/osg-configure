#!/usr/bin/python

""" Module to handle site specific local settings """

from osg_configure.modules.configurationbase import BaseConfiguration
import sys

__all__ = ['LocalSettings']

class LocalSettings(BaseConfiguration):
  """Class to handle site specific local settings"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(LocalSettings, self).__init__(*args, **kwargs)  
    self.logger.debug('LocalSettings.__init__ started')    
    self.config_section = 'Local Settings'  
    self.logger.debug('LocalSettings.__init__ completed')
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('LocalSettings.parseConfiguration started')    

    self.checkConfig(configuration)

    # Parser preserves case so need to create a mapping between normalized sections
    # and actual names to find if this section is present
    sections = configuration.sections()
    section_map = {}
    for section in sections:
      section_map[section.lower()] = section
    
    if not self.config_section.lower() in section_map:
      self.logger.debug("%s section not found in config file" % self.config_section)    
      return
    else:
      section_name = section_map[self.config_section.lower()]
    
    # variables from default section appear, so we need to cross reference
    # the ini defaults and then skip the variable if it also appears in the 
    # defaults section  
    for (name, value) in configuration.items(section_name):
      self.logger.debug("Found %s key with value %s" % (name, value))    
      if name in configuration.defaults():
        self.logger.debug("%s is a default, skipping" % (name))
        continue 
      self.attributes[name] = value
    self.logger.debug('LocalSettings.parseConfiguration completed')    
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "LocalSettings"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True

  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
