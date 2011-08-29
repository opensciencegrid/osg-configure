#!/usr/bin/python

""" Module to handle attributes related to the site location and details """

import os

from configure_osg.modules import exceptions
from configure_osg.modules import utilities
from configure_osg.modules import configfile
from configure_osg.modules import validation
from configure_osg.modules.configurationbase import BaseConfiguration

__all__ = ['InstallLocations']


class InstallLocations(BaseConfiguration):
  """Class to handle attributes related to installation locations"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(InstallLocations, self).__init__(*args, **kwargs)
    self.logger.debug('InstallLocations.configure started')    
    self.__mappings = {'osg': 'OSG_LOCATION', 
                       'globus': 'GLOBUS_LOCATION',
                       'user_vo_map': 'OSG_USER_VO_MAP',
                       'gridftp_log': 'OSG_GRIDFTP_LOG'}
    self.__defaults = {'osg' : '/etc/osg',
                       'user_vo_map' : '/etc/osg/osg-user-vo-map.txt',
                       'gridftp_log' : '/var/log/gridftp/gridftp.log',
                       'globus' : '/'}
    self.config_section = 'Install Locations'
    self.__optional = ['osg', 
                       'globus',
                       'user_vo_map',
                       'gridftp_log']
    self.__self_configured = False
    self.logger.debug('InstallLocations.configure completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('InstallLocations.parseConfiguration started')

    self.checkConfig(configuration)


    if not configuration.has_section(self.config_section):
      self.logger.debug('Install Locations section not found in config file')
      self.logger.debug('Automatically configuring')
      self.__auto_configure()
      self.logger.debug('InstallLocations.parseConfiguration completed')
      self.__self_configured = True    
      return
    else:
      self.logger.warning("Install Locations section found and will " \
                          "be used to configure your resource, however," \
                          "this section is not needed for typical " \
                          "resources and can be deleted from your config file")
    
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting, 
                                   optional_settings = self.__optional,
                                   defaults = self.__defaults)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)      
        
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))   
    self.logger.debug('InstallLocations.parseConfiguration completed')    
     

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('InstallLocations.checkAttributes started')
    attributes_ok = True
    
    if self.__self_configured:
      return True
    
    # make sure locations exist
    for location in self.__mappings:
      if location == 'user_vo_map':
        continue
      if not validation.valid_location(self.attributes[self.__mappings[location]]):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        self.logger.error("%s points to non-existent location: %s" % 
                          (location,self.attributes[self.__mappings[location]]))
    
    self.logger.debug('InstallLocations.checkAttributes completed')        
    return attributes_ok 

  def configure(self, attributes):
    """
    Setup basic osg/vdt services
    """

    self.logger.debug("InstallLocations.configure started")
    status = True
    
    self.logger.debug("InstallLocations.configure completed")    
    return status

  def moduleName(self):
    """Return a string with the name of the module"""
    return "InstallLocations"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]

  def __auto_configure(self):
    """
    Configure settings for Install Locations based on defaults
    """
    self.logger.debug("InstallLocations.__auto_configure started")    
    for setting in self.__mappings:
      self.logger.debug("Setting value for %s" % setting)
      self.attributes[self.__mappings[setting]] = self.__defaults[setting]
    self.logger.debug("InstallLocations.__auto_configure completed")    
    
