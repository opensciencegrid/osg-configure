#!/usr/bin/python

""" Base class for all configuration classes """

import ConfigParser, logging

from osg_configure.modules import configfile

__all__ = ['BaseConfiguration']


class BaseConfiguration(object):
  """Base class for inheritance by configuration"""
  # pylint: disable-msg=W0613
  def __init__(self, *args, **kwargs):
    self.logger = kwargs['logger']
    self.ignored = False
    self.enabled = False
    self.options = {}
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
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "BaseConfiguration"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return False
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return []
  
  def log(self, mesg, **kwargs):
    """
    Generate a log message if option and section are given then the file 
    that generated the error is added to log message  
    
    Arguments:
    mesg - message to add to default log message 
    
    Keyword Arguments:
    option - option that caused the log message to be created
    section - the section that the option given above is location in
    level - optional log level for message, should be a level from 
            logging, defaults to logging.DEBUG if none given
    exception - if True, adds exception information to log file
    """
    
    log_level = kwargs.get('level', logging.DEBUG)
    exception = kwargs.get('exception', False)
    message = ""
    if ('option' in kwargs and 'section' in kwargs):
      file_location = configfile.get_option_location(kwargs['option'],
                                                     kwargs['section'])
      if file_location is not None:
        message = "Using %s in section %s located in %s: " % (kwargs['option'],
                                                              kwargs['section'],
                                                              file_location)      
    message += mesg
    self.logger.log(log_level, message, exc_info = exception)
    
  def checkConfig(self, configuration):
    """
    Make sure config argument is of the correct type
    """
    
    if configuration is None or \
       (configuration.__class__.__name__ is not 'ConfigParser' and \
        configuration.__class__.__name__ is not 'SafeConfigParser'):
      err_msg = 'Invalid type for configuration, must be a ConfigParser '
      err_msg += 'or SafeConfigParser object'
      self.log(err_msg, level = logging.ERROR)
      raise TypeError('Invalid type for configuration, must be a ' + 
                      'ConfigParser or SafeConfigParser object')    
  
  def getOptions(self, configuration, **kwargs):
    """
    Populate self.options based on contents of ConfigParser object, 
    warns if unknown options are found
    
    arguments:
    configuration - a ConfigParser object
    
    keyword arguments:
    ignore_options - a list of option names that should be ignored
                     when checking for unknown options
    """
    
    self.checkConfig(configuration)
    for option in self.options.values():
      self.log("Getting value for %s" % option.name)
      try:              
        configfile.get_option(configuration,
                              self.config_section, 
                              option)
        self.log("Got %s" % option.value)
      except Exception, ex:
        self.log("Received exception when parsing option",
                 option = option.name,
                 section = self.config_section,
                 level = logging.ERROR,
                 exception = True)
        raise

    # check and warn if unknown options found
    known_options = self.options.keys()
    known_options.extend(kwargs.get('ignore_options', []))
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        known_options,
                                        configuration.defaults().keys())
    for option in temp:
      self.log("Found unknown option",
               option = option, 
               section = self.config_section,
               level = logging.WARNING)
    
  def getAttributes(self, converter = str):
    """
    Get attributes for the osg attributes file using the dict in self.options

    Arguments:
    converter -- function that converts various types to strings
    Returns a dictionary of ATTRIBUTE => value mappings
    """
    
    self.log("%s.getAttributes started" % self.__class__)
    if not self.enabled:
      self.log("Not enabled, returning {}")
      self.log("%s.getAttributes completed" % self.__class__)
      return {}
    
    if self.options == {} or self.options is None:
      self.log("self.options empty or None, returning {}")
      self.log("%s.getAttributes completed" % self.__class__)
      return {}
    
    self.log("%s.getAttributes completed" % self.__class__)
    return dict(zip([item.mapping for item in self.options.values() if item.isMappable()],
                    [converter(item.value) for item in self.options.values() if item.isMappable()]))
    
