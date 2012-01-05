#!/usr/bin/python

""" Module to handle attributes related to the site location and details """

import os, logging

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['InstallLocations']


class InstallLocations(BaseConfiguration):
  """Class to handle attributes related to installation locations"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(InstallLocations, self).__init__(*args, **kwargs)
    self.log('InstallLocations.configure started')    
    self.options = {'globus' : 
                      configfile.Option(name = 'globus',
                                        default_value = '/usr',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'GLOBUS_LOCATION'),
                    'user_vo_map' : 
                      configfile.Option(name = 'user_vo_map',
                                        default_value = '/var/lib/osg/user-vo-map',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_USER_VO_MAP'),
                    'gridftp_log' : 
                      configfile.Option(name = 'gridftp_log',
                                        default_value = '/var/log/gridftp.log',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_GRIDFTP_LOG')}
    self.config_section = 'Install Locations'
    self.__self_configured = False
    self.log('InstallLocations.configure completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.log('InstallLocations.parseConfiguration started')

    self.checkConfig(configuration)


    if not configuration.has_section(self.config_section):
      self.log('Install Locations section not found in config file')
      self.log('Automatically configuring')
      self.__auto_configure()
      self.log('InstallLocations.parseConfiguration completed')
      self.__self_configured = True    
      return
    else:
      self.log("Install Locations section found and will be used to configure "\
               "your resource, however, this section is not needed for typical "\
               "resources and can be deleted from your config file",
               level = logging.WARNING)
    
    for option in self.options.values():
      self.log("Getting value for %s" % option.name)
      configfile.get_option(configuration,
                            self.config_section, 
                            option)
      self.log("Got %s" % option.value)
        
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.options.keys(),
                                        configuration.defaults().keys())
    for option in temp:
      self.log("Found unknown option",
               option = option, 
               section = self.config_section,
               level = logging.WARNING)
    self.log('InstallLocations.parseConfiguration completed')    
     

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('InstallLocations.checkAttributes started')
    attributes_ok = True
    
    if self.__self_configured:
      return True
    
    # make sure locations exist
    for option in self.options.values():
      if option.name == 'user_vo_map':
        # skip the user vo map check since we'll create it later if it doesn't
        # exist
        continue
      if not validation.valid_location(option.value):
        attributes_ok = False
        self.log("Invalid location: %s" % option.value,
                 option = option.name,
                 section = self.config_section,
                 level = logging.ERROR)
    
    self.log('InstallLocations.checkAttributes completed')        
    return attributes_ok 

  def configure(self, attributes):
    """
    Setup basic osg/vdt services
    """

    self.log("InstallLocations.configure started")
    status = True
    
    self.log("InstallLocations.configure completed")    
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
    self.log("InstallLocations.__auto_configure started")    
    for option in self.options.values():
      self.log("Setting value for %s" % option.name)
      option.value = option.default_value 
    self.log("InstallLocations.__auto_configure completed")    
    
