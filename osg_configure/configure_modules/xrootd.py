#!/usr/bin/python

"""
Module to handle attributes related to the bestman configuration 
"""


import re, ConfigParser

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules import exceptions
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['XrootdConfiguration']

class XrootdConfiguration(BaseConfiguration):
  """
  Class to handle attributes related to XRootd configuration
  """
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(XrootdConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('XrootdConfiguration.__init__ started')    
    self.__mappings = {'user' : 'user',
                       'mode' : 'mode',
                       'redirector_host' : 'redirector_host',
                       'redirector_storage_path' : 'redirector_storage_path',
                       'redirector_storage_cache' : 'redirector_storage_cache',
                       'token_list' : 'token_list',
                       'public_cache_size' : 'public_cache_size'}
    self.__optional = ['token_list']
    self.config_section = "Xrootd"
    self.logger.debug('XrootdConfiguration.__init__ completed')    
    
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('XrootdConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('Xrootd.parseConfiguration completed')
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('Xrootd.parseConfiguration completed')
      return True
       
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting, 
                                   self.__optional)
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
    self.logger.debug('XrootdConfiguration.parseConfiguration completed')    

  def getAttributes(self):
    """Return settings"""
    self.logger.debug('XrootdConfiguration.getAttributes started')    
    self.logger.debug('XrootdConfiguration.getAttributes completed')    
    return {}

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('XrootdConfiguration.checkAttributes started')    
    attributes_ok = True

    if not self.enabled:
      self.logger.debug('Not enabled, return True')
      self.logger.debug('XrootdConfiguration.checkAttributes completed')
      return attributes_ok
    
    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('XrootdConfiguration.checkAttributes completed')
      return attributes_ok
    # Make sure all settings are present
    for setting in self.__mappings:
      if (self.__mappings[setting] not in self.attributes and
          setting not in self.__optional):
        raise exceptions.SettingError("Missing setting for %s in % section" %
                                      (setting, self.config_section))

    if not validation.valid_user(self.attributes['user']):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      self.logger.error("user does not give a valid user: %s" % 
                        (self.attributes['user']))
      
    
    if self.attributes['mode'] not in ('data', 'redirector'):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      err_msg = "%s should be set to either data or redirector " % ('mode')
      err_msg += "got %s instead" % (self.attributes['mode'])
      self.logger.error(err_msg)

    if self.attributes['mode'] == 'data':
      if not validation.valid_domain(self.attributes['redirector_host'], True):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        err_msg = "redirector_host should point to a valid domain "
        err_msg += "got %s instead" % (self.attributes['redirector_host'])
        self.logger.error(err_msg)
        
      if utilities.blank(self.attributes['redirector_storage_path']):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        self.logger.error("redirector_storage_path must be specified")
      
      if utilities.blank(self.attributes['redirector_storage_cache']):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        self.logger.error("redirector_storage_cache must be specified")

    else:
      if not validation.valid_location(self.attributes['redirector_storage_path']):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        err_msg = "redirector_storage_path should point to a valid location "
        err_msg += "got %s instead" % (self.attributes['redirector_storage_path'])
        self.logger.error(err_msg)
        
      if not validation.valid_location(self.attributes['redirector_storage_cache']):
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        err_msg = "redirector_storage_cache should point to a valid location "
        err_msg += "got %s instead" % (self.attributes['redirector_storage_cache'])
        self.logger.error(err_msg)
      
    try:
      cache_size = int(self.attributes['public_cache_size'])
      if cache_size < 0:
        raise ValueError()
    except ValueError:
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      err_msg = "public_cache_size should be a positive integer "
      err_msg += "got %s instead" % (self.attributes['public_cache_size'])
      self.logger.error(err_msg)

    attributes_ok &= self.__check_tokens()      
    
    self.logger.debug('XrootdConfiguration.checkAttributes completed')
    return attributes_ok 

# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('XrootdConfiguration.configure started')    
    # disable configuration for now
    self.logger.debug('Xrootd not enabled')
    self.logger.debug('XrootdConfiguration.configure completed')
    return True
    
    if not self.enabled:
      self.logger.debug('Xrootd not enabled')
      self.logger.debug('XrootdConfiguration.configure completed')
      return True

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('XrootdConfiguration.configure completed')
      return True

    arguments = ['--server', 
                 'y',
                 '--user',
                 self.attributes['user'],
                 '--xrdr-storage-path',
                 self.attributes['redirector_storage_path'],
                 '--xrdr-storage-cache',
                 self.attributes['redirector_storage_cache'],
                 '--public-cache-size',
                 self.attributes['public_cache_size']]
      
    
    if not utilities.blank(self.attributes['token_list']):
      arguments.append('--with-tokens-list')
      arguments.append(self.attributes['token_list'])
      
    if self.attributes['mode'] == 'redirector':
      arguments.append('--this-is-xrdr')
    elif self.attributes['mode'] == 'data':
      arguments.append('--xrdr-host')
      arguments.append(self.attributes['redirector_host'])
          
    if not utilities.configure_service('configure_xrootd', 
                                       arguments):
      self.logger.error("Error configuring xrootd")
      raise exceptions.ConfigureError("Error configuring Xrootd")    

    self.logger.debug('Enabling Xrootd')
    if not utilities.enable_service('xrootd'):
      self.logger.error("Error while enabling xrootd")
      raise exceptions.ConfigureError("Error configuring Xrootd")    
    self.logger.debug('XrootdConfiguration.configure completed')    
    return True
  
  def moduleName(self):
    """
    Return a string with the name of the module
    """
    return "Xrootd"
  
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
  
  
  def __check_tokens(self):
    """
    Returns True or False depending whether the token_list is a valid list
    of space tokens. 
    A valid list consists of gsiftp urls separated by commas, 
    e.g. gsiftp://server1.example.com,gsiftp://server2.example.com:2188
    """
    
    if ('token_list' not in self.attributes or
        self.attributes['token_list'] is None or
        utilities.blank(self.attributes['token_list'])):
      return True
    
    tokens = self.attributes['token_list'].split(';')
    valid = True
    token_regex = re.compile('[a-zA-Z0-9]+\[desc:[A-Za-z0-9]+\]\[\d+\]')
    for token in [token.strip() for token in tokens]:
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
