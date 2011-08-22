#!/usr/bin/python

""" Module to hold various utility functions """

import glob, ConfigParser, types, os

from configure_osg.modules import exceptions
from configure_osg.modules import utilities
from configure_osg.modules import validation

__all__ = ['get_option_location',
           'get_file_list',
           'read_config_files', 
           'get_option',
           'ce_config']

CONFIG_DIRECTORY = '/etc/osg/config.d'

def read_config_files(**kwargs):
  """
  Read config files located in /etc/osg/config.d and return a config parser 
  object for it
  
  Keyword arguments:
  config_directory -- indicates which directory holds the config files
  case_sensitive -- indicates whether the ConfigParser should be case 
    sensitive when parsing the config file, this is needed for Local Options 
    section
    
  Raises:
  IOError -- error when parsing files
  """

  config_dir = kwargs.get('config_directory', CONFIG_DIRECTORY)
  case_sensitive = kwargs.get('case_sensitive', False)
  if not validation.valid_directory(config_dir):
    raise IOError("%s does not exist" % config_dir)
  file_list = get_file_list(config_directory = config_dir)
  try:
    config = ConfigParser.SafeConfigParser()
    if case_sensitive:
      config.optionxform = str
  except ConfigParser.Error, e:
    raise IOError("Can't read and parse config files:\n%s" % e)
  read_files = config.read(file_list)
  read_files.sort()
  if file_list != read_files:
    unread_files = set(file_list).difference(read_files)
    msg = "Can't read following config files:\n %s" % ("\n".join(unread_files)) 
    raise IOError(msg)
  return config
    
  
def get_option_location(option, section, **kwargs):
  """
  Check for and returns the filename that sets the value of the given option
  Returns None if option or section is not defined.  NOTE: does not handle
  variable interpolation

  Formal arguments:
  option -- option name to look for
  section -- section that the option is located in 

  Keyword arguments:
  config_directory -- indicates which directory holds the config files

  Raises:
  IOError -- Can't read a given file
  Exception -- Can't parse a config file in the config directory    
  """
  config_dir = kwargs.get('config_directory', CONFIG_DIRECTORY)
  file_list = get_file_list(config_directory = config_dir)
  file_list.reverse()
  for fn in file_list:
    try:
      config = ConfigParser.SafeConfigParser()
      config.readfp(open(fn, 'r'))
      if config.has_option(section, option):
        return fn
    except ConfigPaser.Error, e:
      raise Exception("Can't parse %s:\n%s" % (fn, e))
      
  return None

def get_file_list(**kwargs):
  """
  Get the list of files in the sequence that the config parser object will read them

  Keyword arguments:
  config_directory -- indicates which directory holds the config files
  """
  config_dir = kwargs.get('config_directory', CONFIG_DIRECTORY)
  file_list = glob.glob(os.path.join(config_dir, '[!.]*.ini'))
  file_list.sort()
  return file_list

def get_option(config,
               section,
               option,
               optional_settings = None, 
               defaults = None,
               option_type = types.StringType):
  """
  Get an option from a config file with optional defaults and mandatory 
  options.

  Keyword arguments:
  config  -- a ConfigParser object to query
  section --  the ini section the option is located in
  option  --  option name to check
  option_type --  an optional variable indicating the type of the option
  optional_settings -- a list of options that don't have to be given
  defaults -- a dictionary of option : value pairs giving default values for 
    options
  """
  
  if optional_settings is None:
    optional_settings = []
    
  if defaults is None:
    defaults = {}
  
  if option == None or option == "":
    raise exceptions.SettingError('No option passed to get_option')

  if config.has_option(section, option):
    try:
      # if option is blank and there's a default for the option
      # return the default
      if utilities.blank(config.get(section, option)):
        if option in defaults:
          return defaults[option] 
      if (option_type is None or
          option_type is types.StringType):
        return config.get(section, option).strip()
      elif option_type is types.BooleanType:
        return config.getboolean(section, option)
      elif option_type is types.IntType:
        return config.getint(section, option)
      elif option_type is types.FloatType:
        return config.getfloat(section, option)      
    except ValueError:
      error_mesg = "%s  in %s section is of the wrong type" % (option, section)
      raise exceptions.SettingError(error_mesg)
  
  if option in defaults:
    return defaults[option]
  elif option in optional_settings:
    return None
  else:
    err_mesg = "Can't get value for %s in %s section" % (option, section)
    raise exceptions.SettingError(err_mesg)


def ce_config(configuration):
  """
  Check the configuration file and enable this module if the configuration
  is for a ce. A configuration is for a ce if it enables one of the job manager 
  sections
  
  Keyword arguments:
  configuration -- ConfigParser object to check
  """
  
  jobmanagers = ['PBS', 'Condor', 'SGE', 'LSF']  
  for jobmanager in jobmanagers:
    if (configuration.has_section(jobmanager) and
        configuration.has_option(jobmanager, 'enabled') and 
        configuration.getboolean(jobmanager, 'enabled')):
      return True
  
  return False
  
