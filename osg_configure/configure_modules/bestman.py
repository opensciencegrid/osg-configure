#!/usr/bin/python

"""
Module to handle attributes related to the bestman configuration 
"""

import re, ConfigParser, types

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules import exceptions
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['BestmanConfiguration']

class BestmanConfiguration(BaseConfiguration):
  """
  Class to handle attributes related to bestman configuration
  """
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(BestmanConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('BestmanConfiguration.__init__ started')    
    self.__enabled = False
    self.__settings = ['certificate_file',
                       'key_file',
                       'http_port',
                       'https_port',
                       'globus_tcp_port_range',
                       'volatile_file_lifetime',
                       'cache_size',
                       'custodial_storage_path',
                       'custodial_storage_size',
                       'mode',
                       'token_list',
                       'transfer_servers',
                       'user',
                       'allowed_paths',
                       'blocked_paths']
    self.option_types = {'http_port' : types.IntType, 
                         'https_port' : types.IntType,
                         'volatile_file_lifetime' : types.IntType,
                         'cache_size' : types.IntType,
                         'custodial_storage_size' :  types.IntType }
    self.__optional = ['token_list',
                       'globus_tcp_port_range',
                       'volatile_file_lifetime',
                       'cache_size',
                       'custodial_storage_path',
                       'custodial_storage_size',                       
                       'allowed_paths',
                       'blocked_paths']
    # the http and https port defaults need to be set to 8080 and 8443 because the defaults
    # are 10080 and 10443 in the configure_bestman script
    self.__defaults = {'http_port' : '8080',
                       'https_port' : '8443',
                       'user' : 'UNAVAILABLE',
                       'volatile_file_lifetime' : None,
                       'cache_size' : None,
                       'custodial_storage_size' : None }    
    self.__using_gums = False
    self.__gums_host = None
    self.__using_xrootdfs = False
    self.config_section = "Bestman"
    self.logger.debug('BestmanConfiguration.__init__ completed')    
    
  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('BestmanConfiguration.parseConfiguration started')
    
    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.__enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('Bestman.parseConfiguration completed')
      return
    
    try:      
      if (not configuration.has_option(self.config_section, 'enabled') or 
          not configuration.getboolean(self.config_section, 'enabled')):
        self.logger.debug('Bestman not enabled')
        self.attributes['enabled'] = 'N'
        self.__enabled = False
        self.logger.debug('BestmanConfiguration.parseConfiguration completed')    
        return True
      else:
        self.__enabled = True
    except ConfigParser.NoOptionError:
      raise exceptions.SettingError("Can't get value for enable option in Bestman section") 
       
    for setting in self.__settings:
      self.logger.debug("Getting value for %s" % setting)
      if setting in self.option_types:
        option_type = self.option_types[setting]
      else:
        option_type = types.StringType
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting, 
                                   self.__optional, 
                                   self.__defaults,
                                   option_type)
      self.attributes[setting] = temp
      self.logger.debug("Got %s" % temp)  

    # get authorization information from the Misc Services section
    if (configuration.has_section('Misc Services') and
        configuration.has_option('Misc Services', 'authorization_method') and
        configuration.get('Misc Services', 'authorization_method') in ['xacml', 'prima']):
      self.__using_gums = True
      if configuration.has_option('Misc Services', 'gums_host'):
        self.__gums_host = configuration.get('Misc Services', 'gums_host')
        

    # Check to see if xrootdfs is enabled
    if (configuration.has_section('XrootdFS') and
        configuration.has_option('XrootdFS', 'enabled') and
        validation.valid_boolean(configuration, 'XrootdFS', 'enabled')):
      self.__using_xrootdfs = configuration.getboolean('XrootdFS', 'enabled')
      
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__settings,
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
    self.logger.debug('BestmanConfiguration.parseConfiguration completed')    

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('BestmanConfiguration.checkAttributes started')    
    if not self.__enabled:
      return True
    
    attributes_ok = True

    # make sure locations exist
    if not validation.valid_file(self.attributes['certificate_file']):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      self.logger.error("%s points to non-existent location: %s" % 
                        ('key_file',
                         self.attributes['certificate_file']))

    if not validation.valid_file(self.attributes['key_file']):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      self.logger.error("%s points to non-existent location: %s" % 
                        ('key_file',
                         self.attributes['key_file']))

    if self.__using_gums:
      if not validation.valid_domain(self.__gums_host, True):
        attributes_ok = False
        self.logger.error("In Misc Services section:")
        self.logger.error("%s points to host that is not resolvable: %s" % 
                          ('gums_host',
                           self.__gums_host))
        
    
    if not utilities.blank(self.attributes['http_port']):
      port = int(self.attributes['http_port'])
      if port < 0:
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        self.logger.error("%s is less than 0: %s" % 
                          ('http_port',
                           self.attributes['http_port']))

          
    if not utilities.blank(self.attributes['https_port']):
      port = int(self.attributes['https_port'])
      if port < 0:
        attributes_ok = False
        self.logger.error("In %s section:" % self.config_section)
        self.logger.error("%s is less than 0: %s" % 
                          ('https_port',
                           self.attributes['https_port']))
        
    if self.attributes['mode'] not in ('xrootd', 'standalone'):
      attributes_ok = False
      self.logger.error("In %s section:" % self.config_section)
      err_msg = "%s should be set to either xrootd or standalone " % ('mode')
      err_msg += "got %s instead" % (self.attributes['mode'])
      self.logger.error(err_msg)
    
              
    if self.attributes['mode'] == 'xrootd':
      attributes_ok &= self.__check_xrootd_attributes()
    elif self.attributes['mode'] == 'standalone':
      # this calls __check_non_xrootd_attributes
      attributes_ok &= self.__check_standalone_attributes() 
    else:
      attributes_ok &= self.__check_non_xrootd_attributes() 
      

    attributes_ok &= self.__check_servers()      
    
    self.logger.debug('BestmanConfiguration.checkAttributes completed')    
    return attributes_ok 

# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('BestmanConfiguration.configure started')    
    
    # disable configure for now
    self.logger.debug('Bestman not enabled')    
    return True
    
    if not self.__enabled:
      self.logger.debug('Bestman not enabled')    
      return True

    arguments = ['--server', 
                 'y',
                 '--cert',
                 self.attributes['certificate_file'],
                 '--key',
                 self.attributes['key_file']]
    if self.__using_gums:
      arguments.append('--gums-host')
      arguments.append(self.__gums_host)
      arguments.append('--gums-port')
      arguments.append('8443')
      
      
    
    arguments.extend(self.__get_connection_options())
    
    if self.attributes['mode'] == 'xrootd':
      arguments.append('--use-xrootd')
    else:
      arguments.extend(self.__get_non_xrootd_options())
      
    if not utilities.blank(self.attributes['user']):
      arguments.append('--user')
      arguments.append(self.attributes['user'])

    if not utilities.configure_service('configure_bestman', 
                                       arguments):
      self.logger.error("Error configuring bestman")
      raise exceptions.ConfigureError("Error configuring Bestman")    

    self.logger.debug('BestmanConfiguration.configure completed')    
    return True
  
  def moduleName(self):
    """
    Return a string with the name of the module
    """
    return "Bestman"
  
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
  
  def __check_servers(self):
    """
    Returns True or False depending whether the server_list is a valid list 
    of gsiftp urls. 
    A valid list consists of gsiftp urls separated by commas, 
    e.g. gsiftp://server1.example.com,gsiftp://server2.example.com:2188
    """
    
    valid = True
    server_regex = re.compile('gsiftp://[a-zA-Z0-9-]+(?:.[a-zA-Z0-9-]+)+(:\d+)?')
    for server in [server.strip() for server \
                   in self.attributes['transfer_servers'].split(',')]:
      if server == "":
        continue
      match = server_regex.match(server)
      if match is None:
        valid = False
        self.logger.error("In %s section:" % self.config_section)
        error = "%s is a malformed gsiftp url in "  % server 
        error += "transfer_servers setting"
        self.logger.error(error)
        valid = False
        
      host = server[9:].split(':')[0]      
      if not validation.valid_domain(host, False):
        self.logger.error("In %s section:" % self.config_section)
        error = "-%s- is not a valid domain in "  % host 
        error += "transfer_servers setting"
        self.logger.error(error)
        valid = False
        continue
      
      # if no port setting, skip checking the port  
      if len(server[9:].split(':')) == 1:
        continue
      
      try:
        port = int(server[9:].split(':')[1])
        if port < 0:
          raise ValueError()
      except ValueError:
        self.logger.error("In %s section:" % self.config_section)
        error = "%s does not have a valid port in "  % server 
        error += "transfer_servers setting"
        self.logger.error(error)
        valid = False
        
        
    return valid
  
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
  
  def __check_standalone_attributes(self):
    """
    Check options that apply to bestman when it's in gateway mode
    """
    
    status = True
    status &= self.__check_paths(self.attributes['allowed_paths'])
    status &= self.__check_paths(self.attributes['blocked_paths'])
    status &= self.__check_non_xrootd_attributes()
    return status
      
  def __check_non_xrootd_attributes(self):
    """
    Check options that apply to bestman when it's in gateway mode
    """
    
    status = True
    if not utilities.blank(self.attributes['custodial_storage_path']):
      status &= self.__check_paths(self.attributes['custodial_storage_path'])

    if not utilities.blank(self.attributes['cache_size']):
      if self.attributes['cache_size'] < 0:
        status = False

    if not utilities.blank(self.attributes['cache_size']):
      if self.attributes['cache_size'] < 0:
        status = False

    if not utilities.blank(self.attributes['volatile_file_lifetime']):
      if self.attributes['volatile_file_lifetime'] < 0:
        status = False

    if not utilities.blank(self.attributes['custodial_storage_size']):
      if self.attributes['custodial_storage_size'] < 0:
        status = False

    return status

  def __check_xrootd_attributes(self):
    """
    Check options that apply to bestman when it's in xrootd mode
    """
    
    if not self.__using_xrootdfs:
      self.logger.error('XrootdFS must be enabled and configured when using ' \
                        'Bestman in xrootd mode')
      return False
    
    if not utilities.blank(self.attributes['volatile_file_lifetime']):
      self.logger.warning("In section %s, volatile_file_lifetime " \
                          "is not valid when using xrootd.  Setting " \
                          "will be ignored." % self.config_section)
      
    if not utilities.blank(self.attributes['cache_size']):
      self.logger.warning("In section %s, cache_size " \
                          "is not valid when using xrootd.  Setting " \
                          "will be ignored." % self.config_section)
    status = True
    status &= self.__check_paths(self.attributes['allowed_paths'])
    status &= self.__check_paths(self.attributes['blocked_paths'])
    status &= self.__check_tokens()
    
    return status
  
  def __check_paths(self, paths):
    """
    Check paths to make sure that the paths are in the proper format:
    directories seperated by semicolons
    
    Returns True, if the paths are in proper format
    """
    
    if paths is None:
      return True
    
    dir_regex = re.compile('(\./|/)?[\w-]+(?:/[\w-]+)*' )
    for path in paths.split(';'):
      if dir_regex.match(path) is None:
        return False
    return True
  
  def __get_non_xrootd_options(self):
    """
    Generate non xrootd options for configure_bestman call
    """
    arguments = []
    if self.attributes['mode'] == 'gateway':
      arguments.append('--enable-gateway')
    
    if (self.attributes['volatile_file_lifetime'] is not None and 
        not utilities.blank(self.attributes['volatile_file_lifetime'])):
      arguments.append('--volatile-file-lifetime')
      arguments.append(self.attributes['volatile_file_lifetime'])
    
    if (self.attributes['cache_size'] is not None and 
        not utilities.blank(self.attributes['cache_size'])):
      arguments.append('--cache-size')
      arguments.append(self.attributes['cache_size'])
      
    if self.attributes['custodial_storage_path'] is not None:
      arguments.append('--custodial-storage-path')
      arguments.append(self.attributes['custodial_storage_path'])

    if self.attributes['custodial_storage_size'] is not None:
      arguments.append('--custodial-storage-size')
      arguments.append(self.attributes['custodial_storage_size'])

    return arguments
  
  def __get_connection_options(self):
    """
    Generate options pertaining to connections for configure_bestman call
    """
    arguments = []

    if not utilities.blank(self.attributes['http_port']):
      arguments.append('--http-port')
      arguments.append(self.attributes['http_port'])
      
    if not utilities.blank(self.attributes['https_port']):
      arguments.append('--https-port')
      arguments.append(self.attributes['https_port'])

    if not utilities.blank(self.attributes['globus_tcp_port_range']):
      arguments.append('--globus-tcp-port-range')
      arguments.append(self.attributes['globus_tcp_port_range'])

    if not utilities.blank(self.attributes['https_port']):
      arguments.append('--https-port')
      arguments.append(self.attributes['https_port'])

    if not utilities.blank(self.attributes['transfer_servers']):
      arguments.append('--with-transfer-servers')
      arguments.append(self.attributes['transfer_servers'])
    
    return arguments
