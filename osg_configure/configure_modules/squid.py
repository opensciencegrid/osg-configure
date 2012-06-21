#!/usr/bin/python

""" Module to handle squid configuration and setup """

import ConfigParser, os, logging

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['SquidConfiguration']


class SquidConfiguration(BaseConfiguration):
  """Class to handle attributes related to squid configuration and setup"""
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(SquidConfiguration, self).__init__(*args, **kwargs)
    self.log('SquidConfiguration.__init__ started')
    self.options = {'location' : 
                      configfile.Option(name = 'location',
                                        mapping = 'OSG_SQUID_LOCATION'),
                    'policy' : 
                      configfile.Option(name = 'policy',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_SQUID_POLICY'),
                    'cache_size' : 
                      configfile.Option(name = 'cache_size',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = 0,
                                        type = int,
                                        mapping = 'OSG_SQUID_CACHE_SIZE'),
                    'memory_size' : 
                      configfile.Option(name = 'memory_size',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = 0,
                                        type = int,
                                        mapping = 'OSG_SQUID_MEM_CACHE')}
    self.config_section = 'Squid'
    self.log('SquidConfiguration.__init__ completed')
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.log('SquidConfiguration.parseConfiguration started')
    
    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)
      self.log('SquidConfiguration.parseConfiguration completed')
      return
    
    if not self.setStatus(configuration):
      self.log('SquidConfiguration.parseConfiguration completed')
      if not self.ignored and not self.enabled:
        return True

    self.getOptions(configuration, ignore_options = ['enabled'])
    
    if not utilities.blank(self.options['location'].value):
      if ":" not in self.options['location'].value:        
        self.options['location'].value += ":3128"        
        
    self.log('SquidConfiguration.parseConfiguration completed')

  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('SquidConfiguration.checkAttributes started')
    attributes_ok = True
    if not self.enabled:
      self.log('squid not enabled')
      self.log('SquidConfiguration.checkAttributes completed')
      return attributes_ok

    if self.ignored:
      self.log('Ignored, returning True')
      self.log('SquidConfiguration.checkAttributes completed')
      return attributes_ok

    if len(self.options['location'].value.split(':')) != 2:
      self.log("Bad host specification, got %s expected hostname:port " \
               "(e.g. localhost:3128" % self.options['location'].value,
               section = self.config_section,
               option = 'location',
               level = logging.ERROR)
      attributes_ok = False
    (hostname, port) = self.options['location'].value.split(':')
    if not validation.valid_domain(hostname, True):
      self.log("Invalid hostname for squid location: %s" % \
               self.options['location'].value,
               section = self.config_section,
               option = 'location',
               level = logging.ERROR)
      attributes_ok = False
    try:
      int(port)
    except ValueError:
      self.log("The port must be a number(e.g. host:3128) for squid " \
               "location: %s" % self.options['location'].value,
               section = self.config_section,
               option = 'location',
               level = logging.ERROR,
               exception = True)      
      attributes_ok = False
            
    self.log('SquidConfiguration.checkAttributes completed')
    return attributes_ok 
  
# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('SquidConfiguration.configure started')

    if not self.enabled:
      self.log('squid not enabled')
      self.log('SquidConfiguration.configure completed')
      return True

    if self.ignored:
      self.log('Ignored, returning True')
      self.log('SquidConfiguration.configure completed')
      return True

    self.log('SquidConfiguration.configure completed')
    return True     

  def moduleName(self):
    """Return a string with the name of the module"""
    return "Squid"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]

  def getAttributes(self):
    """
    Get attributes for the osg attributes file using the dict in self.options

    Returns a dictionary of ATTRIBUTE => value mappings
    
    Need to override parent class method since two options may map to OSG_SITE_NAME
    """

    self.log("%s.getAttributes started" % self.__class__)

    attributes = BaseConfiguration.getAttributes(self)
    if self.ignored:
      self.log("%s.getAttributes completed" % self.__class__)
      return dict(zip([item.mapping for item in self.options.values() if item.isMappable()],
                      [str(item.value) for item in self.options.values() if item.isMappable()]))
    elif not self.enabled:
      attributes['OSG_SQUID_LOCATION'] = 'UNAVAILABLE'
      self.log("%s.getAttributes completed" % self.__class__)
      return attributes              
    
    self.log("%s.getAttributes completed" % self.__class__)
    return attributes
