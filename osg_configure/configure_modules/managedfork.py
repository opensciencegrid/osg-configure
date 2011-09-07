#!/usr/bin/env python

""" Module to handle attributes related to the Managed Fork jobmanager configuration """


import os
import ConfigParser

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import exceptions
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['ManagedForkConfiguration']

class ManagedForkConfiguration(BaseConfiguration):
  """Class to handle attributes related to managedfork job 
  manager configuration
  """
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(ManagedForkConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('ManagedForkConfiguration.__init__ started')    
    self.__mappings = {'enabled': 'OSG_MANAGEDFORK',
                       'condor_location': 'OSG_CONDOR_LOCATION',
                       'condor_config': 'OSG_CONDOR_CONFIG',
                       'accept_limited': 'accept_limited'}
    self.__optional = ['condor_location', 
                       'condor_config',
                       'accept_limited']
    condor_location = os.environ.get('CONDOR_LOCATION', '/usr')
    self.__defaults = {'condor_location' : condor_location,
                       'accept_limited' : 'False'}
    
    self.config_section = "Managed Fork"
    self.logger.debug('ManagedForkConfiguration.__init__ completed')    
    
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('ManagedForkConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('ManagedFork.parseConfiguration completed')
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('ManagedFork.parseConfiguration completed')
      self.attributes[self.__mappings['enabled']] = 'N'
      return True
       
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting, 
                                   self.__optional, 
                                   self.__defaults)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)
       
    if self.__mappings['enabled']:
      self.attributes[self.__mappings['enabled']] = 'Y'

    if (configuration.has_option(self.config_section, 'condor_config') or
        configuration.has_option(self.config_section, 'condor_location')):
      self.logger.warning("condor_config and/or condor_location found in " \
                          "%s section, these settings are not used and " \
                          "will be ignored" % self.config_section)
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
    self.logger.debug('ManagedForkConfiguration.parseConfiguration completed')    

  def getAttributes(self):
    """Return settings"""
    self.logger.debug('ManagedForkConfiguration.getAttributes started')    
    self.logger.debug('ManagedForkConfiguration.getAttributes completed')    
    return self.attributes

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('ManagedForkConfiguration.checkAttributes started')    
    attributes_ok = True

    if not self.enabled:
      self.logger.debug('Not enabled, returning True')
      self.logger.debug('ManagedForkConfiguration.checkAttributes completed')
      return attributes_ok
    
    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('ManagedForkConfiguration.checkAttributes completed')
      return attributes_ok
    
    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        raise exceptions.SettingError("Missing setting for %s in % section" %
                                      (setting, self.config_section))

    self.logger.debug('ManagedForkConfiguration.checkAttributes completed')    
    return attributes_ok 

# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""

    self.logger.debug('ManagedForkConfiguration.configure started')

    # diable configuration for now
    self.logger.warning("ManagedFork disabled")
    self.logger.debug('ManagedForkConfiguration.configure completed')
    return True
    
    configure_globus = os.path.join("/usr/sbin/configure_globus_gatekeeper")
    if not os.path.exists(configure_globus):
      self.logger.debug("Configuration script '%s' does not exist.  Not applying globus-gatekeeper configuration in managedfork.py" % configure_globus)
      return True
    
    if not self.enabled:
      self.logger.debug('ManagedFork not enabled')
      self.logger.debug('Configuring gatekeeper to use regular fork service')
      self.__disable_service()
      self.logger.debug('ManagedForkConfiguration.configure completed')
      return True

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('ManagedForkConfiguration.configure completed')
      return True

    self.logger.debug("Setting managed fork to be the default jobmanager")
    arguments = ['--managed-fork', 'y']
    if utilities.service_enabled('globus-gatekeeper'):
      arguments = ['--managed-fork', 'y', '--server', 'y']

    # The accept_limited argument was added for Steve Timm.  We are not adding
    # it to the default config.ini template because we do not think it is
    # useful to a wider audience.
    # See VDT RT ticket 7757 for more information.
    if self.attributes[self.__mappings['accept_limited']].upper() == "TRUE":
      arguments.append("--accept-limited")

    if not utilities.configure_service('configure_globus_gatekeeper', 
                                       arguments):
      self.logger.error("Error while making managed fork the default jobmanager")
      raise exceptions.ConfigureError("Error configuring Managed Fork")    

    self.logger.debug('ManagedForkConfiguration.configure completed')
    return True
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "ManagedFork"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return False
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
  
  def __disable_service(self):
    """
    Set the gatekeeper to use the regular fork service
    """
    self.logger.debug("ManagedForkConfiguration.__disable_service started")

    self.logger.debug("Setting managed fork to be the default jobmanager")
    arguments = ['--managed-fork', 'n']
    if utilities.service_enabled('globus-gatekeeper'):
      arguments = ['--managed-fork', 'n', '--server', 'y']
    if not utilities.configure_service('configure_globus_gatekeeper', 
                                       arguments):
      self.logger.error("Error changing to the regular fork manager")
      raise exceptions.ConfigureError("Error disabling Managed Fork")    
    
    self.logger.debug("ManagedForkConfiguration.__disable_service completed")
