#!/usr/bin/python

"""
Module to handle attributes related to the bestman configuration 
"""


import ConfigParser

from configure_osg.modules import utilities
from configure_osg.modules import configfile
from configure_osg.modules import validation
from configure_osg.modules import exceptions
from configure_osg.modules.configurationbase import BaseConfiguration

__all__ = ['GridFTPConfiguration']

class GridFTPConfiguration(BaseConfiguration):
  """
  Class to handle attributes related to XRootdFS configuration
  """
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(GridFTPConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('GridFTPConfiguration.__init__ started')    
    self.__settings = ['mode',
                       'redirector',
                       'mount_point',
                       'redirector_storage_path']
    self.__optional = []
    self.__defaults = {}
    self.config_section = "Gridftp"
    self.logger.debug('GridFTPConfiguration.__init__ completed')    
    
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('GridFTPConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('GridFTP.parseConfiguration completed')
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('GridFTP.parseConfiguration completed')
      return True
    
    if (configuration.has_section('Xrootd') and
        configuration.has_option('Xrootd', 'redirector_storage_path')) :
      self.__defaults['redirector_storage_path'] = \
        configuration.get('Xrootd', 'redirector_storage_path')
       
    for setting in self.__settings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting, 
                                   self.__optional, 
                                   self.__defaults)
      self.attributes[setting] = temp
      self.logger.debug("Got %s" % temp)
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__settings,
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
    self.logger.debug('GridFTPConfiguration.parseConfiguration completed')    

  def getAttributes(self):
    """Return settings"""
    self.logger.debug('GridFTPConfiguration.getAttributes started')    
    self.logger.debug('GridFTPConfiguration.getAttributes completed')    
    return {}

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('GridFTPConfiguration.checkAttributes started')
    
    attributes_ok = True

    if not self.enabled:
      self.logger.debug('Not enabled, exiting')
      self.logger.debug('GridFTPConfiguration.checkAttributes completed')
      return attributes_ok
    
    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('GridFTPConfiguration.checkAttributes completed')
      return attributes_ok
    
    # Make sure all settings are present
    for setting in self.__settings:
      if setting not in self.attributes:
        raise exceptions.SettingError("Missing setting for %s in % section" %
                                      (setting, self.config_section))

    if self.attributes['mode'] not in ('xrootd', 'standalone'):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      err_msg = "%s should be set to either standalone or xrootd " % ('mode')
      err_msg += "got %s instead" % (self.attributes['mode'])
      self.logger.error(err_msg)
            
    
    if self.attributes['mode'] == 'xrootd':
      self.logger.debug('Checking xrootd options, since xrootd is enabled')
      if not validation.valid_domain(self.attributes['redirector'], True):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        err_msg = "redirector should point to a valid domain "
        err_msg += "got %s instead" % (self.attributes['redirector'])
        self.logger.error(err_msg)
        
      if utilities.blank(self.attributes['redirector_storage_path']):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        self.logger.error("redirector_storage_path must be specified")
      
      if utilities.blank(self.attributes['mount_point']):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        err_msg = "mount_point must be specified "
        err_msg += "got %s instead" % (self.attributes['mount_point'])
        self.logger.error(err_msg)

    self.logger.debug('GridFTPConfiguration.checkAttributes completed')    
    return attributes_ok 

# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('GridFTPConfiguration.configure started')    

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('GridFTPConfiguration.configure completed')
      return True

    # disable configuration for now
    self.logger.debug('GridFTP not enabled')
    self.logger.debug('GridFTPConfiguration.configure completed')
    return True
    
    if not self.enabled:
      self.logger.debug('GridFTP not enabled')
      self.logger.debug('GridFTPConfiguration.configure completed')
      return True

    arguments = ['--server', 'y']
    
    if self.attributes['mode'] == 'xrootd':
      arguments.append('--use-xrootd')
      arguments.append('--xrootd-host')
      arguments.append(self.attributes['redirector'])
      arguments.append('--xrootd-mount-point')
      arguments.append(self.attributes['mount_point'])
      arguments.append('--xrootd-storage-path')
      arguments.append(self.attributes['redirector_storage_path'])
          
    if not utilities.configure_service('configure_gridftp', 
                                       arguments):
      self.logger.error("Error configuring gridftp")
      raise exceptions.ConfigureError("Error configuring GridFTP")    

    self.logger.debug('Enabling GridFTP')
    if not utilities.enable_service('gsiftp'):
      self.logger.error("Error while enabling gridftp")
      raise exceptions.ConfigureError("Error configuring GridFTP")
    
          
    self.logger.debug('GridFTPConfiguration.configure completed')
    return True
  

  def moduleName(self):
    """
    Return a string with the name of the module
    """
    return "GridFTP"
  
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
  
  
