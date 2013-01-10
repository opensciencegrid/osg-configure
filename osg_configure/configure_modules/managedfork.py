""" Module to handle attributes related to the Managed Fork jobmanager configuration """

import os
import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules.jobmanagerbase import JobManagerConfiguration
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['ManagedForkConfiguration']


def convert_values(value):
  """
  Convert values to a string representation that can go into osg-attributes.conf
  
  arguments:
  value - item to convert
  """
  
  if type(value) == bool:
    if value:
      return 'Y'
    else:
      return 'N'
  return str(value)

class ManagedForkConfiguration(JobManagerConfiguration):
  """
  Class to handle attributes related to managedfork job 
  manager configuration
  """
  
  MANAGED_FORK_CONFIG_FILE = '/etc/grid-services/available/jobmanager-managedfork'
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(ManagedForkConfiguration, self).__init__(*args, **kwargs)    
    self.log('ManagedForkConfiguration.__init__ started')
    # dictionary to hold information about options
    self.options = {'condor_location' : 
                      configfile.Option(name = 'condor_location',
                                        required = configfile.Option.OPTIONAL,
                                        value = utilities.get_condor_location(),
                                        mapping = 'OSG_CONDOR_LOCATION'),
                    'condor_config' : 
                      configfile.Option(name = 'condor_config',
                                        required = configfile.Option.OPTIONAL,
                                        value = utilities.get_condor_config(),
                                        mapping = 'OSG_CONDOR_CONFIG'),
                    'enabled' : 
                      configfile.Option(name = 'enabled',
                                        required = configfile.Option.OPTIONAL,
                                        opt_type = bool,
                                        default_value = False,
                                        mapping = 'OSG_MANAGEDFORK'),
                    'accept_limited' : 
                      configfile.Option(name = 'accept_limited',
                                        required = configfile.Option.OPTIONAL,
                                        opt_type = bool,
                                        default_value = False)}
    self.section_present = False
    self.config_section = "Managed Fork"
    self.log('ManagedForkConfiguration.__init__ completed')    
    
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.log('ManagedForkConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.section_present = False
      self.log("%s section not in config file" % self.config_section)
      self.log('ManagedFork.parseConfiguration completed')
      return
    
    self.section_present = True
    if not self.setStatus(configuration):
      self.options['enabled'].value = False
      self.log('ManagedFork.parseConfiguration completed')
      return True
       
    self.getOptions(configuration)
       
    if configuration.has_option(self.config_section, 'condor_config'):
      self.log("This setting is not used and will be ignored",
               section = self.config_section,
               option = 'condor_config',
               level = logging.WARNING)
    elif configuration.has_option(self.config_section, 'condor_location'): 
      self.log("This setting is not used and will be ignored",
               section = self.config_section,
               option = 'condor_location',
               level = logging.WARNING)
    self.log('ManagedForkConfiguration.parseConfiguration completed')    


# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('ManagedForkConfiguration.checkAttributes started')    
    attributes_ok = True

    if not self.enabled:
      self.log('Not enabled, returning True')
      self.log('ManagedForkConfiguration.checkAttributes completed')
      return attributes_ok
    
    if self.ignored:
      self.log('Ignored, returning True')
      self.log('ManagedForkConfiguration.checkAttributes completed')
      return attributes_ok
    
    self.log('ManagedForkConfiguration.checkAttributes completed')    
    return attributes_ok 

# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""

    self.log('ManagedForkConfiguration.configure started')
    
    if self.ignored:
      # this needs to go before the self.enabled check to prevent any changes
      # in the configuration
      self.log("%s configuration ignored" % self.config_section, 
               level = logging.WARNING)
      self.log('ManagedForkConfiguration.configure completed')
      return True

    if not self.enabled:
      self.log('ManagedFork not enabled')
      if self.section_present:
        # Only switch job managers if this is a CE configuration
        self.log('Configuring gatekeeper to use regular fork service')
        if not self.set_default_jobmanager('fork'):
          self.log('ManagedForkConfiguration.configure completed')
          return False 
      self.log('ManagedForkConfiguration.configure completed')
      return True


    self.log("Setting managed fork to be the default jobmanager")
    if not os.path.exists(ManagedForkConfiguration.MANAGED_FORK_CONFIG_FILE):
      err_mesg = "Globus jobmanager-managedfork configuration not present, " \
                 "is it installed?\n"
      self.log(err_mesg,
               level = logging.ERROR)
      self.log('ManagedForkConfiguration.configure completed')
      return False

    
    # The accept_limited argument was added for Steve Timm.  We are not adding
    # it to the default config.ini template because we do not think it is
    # useful to a wider audience.
    # See VDT RT ticket 7757 for more information.
    if self.options['accept_limited'].value:
      if not self.enable_accept_limited(ManagedForkConfiguration.MANAGED_FORK_CONFIG_FILE):
        self.log('Error writing to ' + 
                 ManagedForkConfiguration.MANAGED_FORK_CONFIG_FILE, 
                 level = logging.ERROR)
        self.log('ManagedForkConfiguration.configure completed')
        return False
    else:
      if not self.disable_accept_limited(ManagedForkConfiguration.MANAGED_FORK_CONFIG_FILE):
        self.log('Error writing to ' + 
                 ManagedForkConfiguration.MANAGED_FORK_CONFIG_FILE, 
                 level = logging.ERROR)
        self.log('ManagedForkConfiguration.configure completed')
        return False      

    if not self.set_default_jobmanager('managed-fork'):
      self.log("Could not set the jobmanager-managedfork to the default jobmanager",
               level = logging.ERROR)
      self.log('ManagedForkConfiguration.configure completed')
      return False

    self.log('ManagedForkConfiguration.configure completed')
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
  
  def getAttributes(self, converter = str):
    """
    Get attributes for the osg attributes file using the dict in self.options

    Returns a dictionary of ATTRIBUTE => value mappings
    
    Need to override parent class method since OSG_MANAGEDFORK is bool and needs
    to be mapped to Y/N
    """

    self.log("%s.getAttributes started" % self.__class__)
    attributes = BaseConfiguration.getAttributes(self, converter = convert_values)
    if attributes == {}:
      attributes['OSG_MANAGEDFORK'] = 'N'
    self.log("%s.getAttributes completed" % self.__class__)
    return attributes
  
  
  def enabledServices(self):
    """Return a list of  system services needed for module to work
    """
    
    if not self.enabled or self.ignored:
      return set()

    return set(['condor-cron', 'globus-gatekeeper'])
  
