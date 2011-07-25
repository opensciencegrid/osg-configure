#!/usr/bin/python

""" Module to hold various utility functions """

import re, socket, os, types, pwd, sys, glob, ConfigParser
import tempfile, subprocess   

from configure_osg.modules import exceptions

__all__ = ['valid_domain', 
           'valid_email', 
           'valid_location', 
           'valid_file',
           'valid_user',
           'valid_user_vo_file',
           'valid_vo_name',
           'valid_boolean',
           'valid_executable',
           'valid_ini_file',
           'using_prima',
           'using_xacml_protocol',
           'get_vos',
           'duplicate_sections', 
           'run_vdt_configure',
           'enable_service',
           'disable_service',
           'configure_service',   
           'service_enabled',    
           'get_elements',
           'get_hostname',
           'get_set_membership',
           'blank',
           'get_gums_host',
           'create_map_file',
           'fetch_crl',
           'get_option',
           'ce_config']
  
CONFIG_DIRECTORY = "/etc/osg"

def valid_domain(host, resolve=False):
  """Check to see if the string passed in is a valid domain"""
  if len(host) == 0:
    return False
  match = re.match('^[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)+$', 
                   host)
  if not match:
    return False
  elif match and not resolve:
    return True
  
  try:
    socket.gethostbyname(host)
  except socket.herror:
    return False
  except socket.gaierror:
    return False
  return True

def valid_email(address):
  """Check an email address and make sure that it fits the correct format"""
  if len(address) == 0:
    return False
  match = re.match('(?:[a-zA-Z\-_+0-9.]+)@([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)+)', 
                   address)
  if not match:
    return False
  return True

def valid_location(location):
  """Returns True if location points to an existing directory or file"""
  if os.path.exists(location):
    return os.path.isdir(location) or os.path.isfile(location)
  
  return False 

def valid_file(location):
  """Returns True if location points to an existing file"""
  if os.path.exists(location):
    return os.path.isfile(location)
  
  return False 

def valid_user(username):
  """
  Returns True if the username given is a valid username on the system
  """
  try:
    if pwd.getpwnam(username):
      return True
  except KeyError:
    # getpwnam returns a key error if entry isn't present
    return False
  
  return False 
  
def using_prima():
  """
  Function to check whether prima callouts are setup
  """
  
  if (not valid_file('/etc/grid-security/gsi-authz.conf') or
      not valid_file('/etc/grid-security/prima-authz.conf')):
    return False
    
  gsi_set = False
  prima_set = False
  gsi_buffer = open('/etc/grid-security/gsi-authz.conf').read()
  prima_buffer = open('/etc/grid-security/prima-authz.conf').read()

  if re.search('^\s*globus_mapping', gsi_buffer, re.M):
    gsi_set = True

  if re.search('^\s*imsContact https://(.*?):\d+', prima_buffer, re.M):
    prima_set = True

  if gsi_set and prima_set:
    return True
  
  return False

def using_xacml_protocol():
  """
  Function to check to see whether the system is using xacml to talk to GUMS
  """
  
  if not using_prima():
    return False
  
  gsi_buffer = open('/etc/grid-security/gsi-authz.conf').read(8192)

  if re.search('^globus_mapping.*_scas_.*', gsi_buffer, re.M):
    return True
  
  return False
  
def get_gums_host():
  """
  Function to return the gums host being used on the system, returns a tuple 
  with the host name and port of the gums host or None if a gums host is not being used
  """

  if 'VDT_GUMS_HOST' in os.environ:
    return (os.environ['VDT_GUMS_HOST'], 8443)
  
  if not using_prima():
    return None
    
  prima_buffer = open('/etc/grid-security/prima-authz.conf').read(8192)

  match = re.search('^\s*imsContact https://(.*?):(\d+)?', prima_buffer, re.M)      
  if match:
    host = match.group(1)
    port = match.group(2)
    return (host, port)
  
  return None
  
def run_vdt_configure(arguments = None):
  """Run a configuration script from vdt and return exit status"""
  if arguments is None:
    return False
  return run_script(arguments)
    
def get_elements(element=None, filename=None):
  """Get values for selected element from xml file specified in filename"""
  if filename is None or element is None:
    return []
  import xml.dom.minidom
  try:
    dom = xml.dom.minidom.parse(filename)
  except IOError:
    return []
  except xml.parsers.expat.ExpatError:
    return []
  values = dom.getElementsByTagName(element)
  return values
    
def write_attribute_file(filename=None, attributes=None):
  """
  Write attributes to osg attributes file in an atomic fashion
  """
  
  if attributes is None or filename is None:
    attributes = {}
  base_dir = os.path.dirname(filename)
  (fd, tmp_name) = tempfile.mkstemp(text=True, dir=base_dir)
  file_handle = os.fdopen(fd, 'w')
  variable_string = ""
  export_string = ""
  # keep a list of array variables 
  array_vars = {}
  keys = attributes.keys()
  keys.sort()
  for key in keys:
    if type(attributes[key]) is types.ListType:
      for item in attributes[key]:
        variable_string += "%s=\"%s\"\n" % (key, item)
    else:  
      variable_string += "%s=\"%s\"\n" % (key, attributes[key])
    if len(key.split('[')) > 1:
      real_key = key.split('[')[0]
      if real_key not in array_vars:
        export_string += "export %s\n" % key.split('[')[0]
        array_vars[real_key] = ""
    else:
      export_string += "export %s\n" % key
       
  file_handle.write("#!/bin/sh\n")
  file_handle.write("#---------- This file automatically generated by " \
                    "configure-osg \n")
  file_handle.write("#---------- This is periodically overwritten.  " \
                    "DO NOT HAND EDIT\n")
  file_handle.write("#---------- Instead, write any environment variable " \
                    "customizations into\n")
  file_handle.write("#---------- the config.ini [Local Settings] section, " \
                    "as documented here:\n")
  file_handle.write("#---------- https://twiki.grid.iu.edu/bin/view/Release"\
                    "Documentation/ConfigurationFileLocalSettings")
  file_handle.write("#---  variables -----\n")
  file_handle.write(variable_string)
  file_handle.write("#--- export variables -----\n")
  file_handle.write(export_string)
  file_handle.close()
  os.rename(tmp_name, filename)
  os.chmod(filename, 0644)
  return True

def get_set_membership(test_set, reference_set, defaults = None):
  """
  See if test_set has any elements that aren't keys of the reference_set 
  or optionally defaults.  Takes lists as arguments
  """
  missing_members = []
  
  if defaults is None:
    defaults = []
  for member in test_set:
    if member not in reference_set and member not in defaults:
      missing_members.append(member)
  return missing_members

def get_hostname():
  """Returns the hostname of the current system"""
  try:
    return socket.gethostbyaddr(socket.gethostname())[0]
  # pylint: disable-msg=W0703
  except Exception:
    return None
  return None

def blank(value):
  """Check the value to check to see if it is 'UNAVAILABLE' or blank, return True 
  if that's the case
  """
  if type(value) != types.StringType:
    if value is None:
      return True
    return False
  
  if (value.upper().startswith('UNAVAILABLE') or
      value == "" or
      value is None):
    return True
  return False

def get_vos(user_vo_file):
  """
  Returns a list of valid VO names.
  """

  if (user_vo_file is None or 
      not os.path.isfile(user_vo_file)):
    user_vo_file = os.path.join(os.path.join(CONFIG_DIRECTORY, 
                                             'osg-user-vo-map.txt'))
  if not os.path.isfile(user_vo_file):
    return []
  file_buffer = open(os.path.expandvars(user_vo_file), 'r')
  vo_list = []
  for line in file_buffer:
    try:
      line = line.strip()
      if line.startswith("#"):
        continue
      vo = line.split()[1]
      if vo.startswith('us'):
        vo = vo[2:]
      if vo not in vo_list:
        vo_list.append(vo)
    except (KeyboardInterrupt, SystemExit):
      raise
    except:
      pass
  return vo_list


def duplicate_sections_exist(config_file):
  """
  Check a config file to make sure that it does not have any duplicate 
  sections.
  """
  if config_file == "" or config_file is None:
    return False
  
  file_contents = open(config_file, 'r').read()
  sections = {}
  for line in file_contents.splitlines():
    temp = line.strip()
    match = re.search('^\s*\[(.*)\]', temp)
    if match:
      section = match.group(1).lower()      
      if section in sections:
        sys.stderr.write("Section %s duplicated" % section)
        return True
      else:
        sections[section] = True
  return False



def valid_user_vo_file(map_file = None, return_invalid_lines = False):
  """
  Check an osg-user-vo-file and make sure that it's valid.
  """
  if map_file is None or map_file == "":
    if return_invalid_lines:
      return (False, [])
    else:
      return False
  
  if not valid_file(map_file):
    if return_invalid_lines:
      return (False, [])
    else:
      return False

  if os.path.getsize(map_file) == 0:
    if return_invalid_lines:
      return (False, [])
    else:
      return False
  
  valid = True
  comment = re.compile('^\s*#')
  java = re.compile('(java|exception)', re.I)
  account_regex = re.compile('^[a-z0-9-._]+$', re.IGNORECASE) 
  invalid_lines = []
  for line in [x.strip() for x in open(map_file)]:
    if line == "":
      # skip blank lines
      continue
    
    if java.search(line):
      # found java exception
      invalid_lines.append(line)
      valid = False
      continue

    if not comment.match(line):
      if len(line.strip().split(' ')) != 2:
        invalid_lines.append(line)
        valid = False
        continue
        
      (account, vo) = line.strip().split(' ')
      if not (account_regex.match(account) and valid_vo_name(vo)):
        # not a comment or entry
        invalid_lines.append(line)
        valid = False
        continue
      
  if return_invalid_lines:    
    return (valid, invalid_lines)
  else:
    return valid

def enable_service(service_name):
  """
  Run vdt-control to enable specified service.
  """
  
  if service_name == None or service_name == "":
    return False
  return run_script(['/sbin/service', '--on', service_name])


def disable_service(service_name):
  """
  Run vdt-control to enable specified service.
  """
  
  if service_name == None or service_name == "":
    return False
  return run_script(['/sbin/service', '--disable', service_name])

def service_enabled(service_name):
  """
  Check to see if a service is enabled
  """
  if service_name == None or service_name == "":
    return False
  process = subprocess.Popen(['/sbin/service', '--list', service_name], 
                             stdout=subprocess.PIPE)
  output = process.communicate()[0]
  if process.returncode != 0:
    return False  

  match = re.search(service_name + '\s*\|.*\|\s*([a-z ]*)$', output)
  if match:
    # The regex above captures trailing whitespace, so remove it
    # before we make the comparison. -Scot Kronenfeld 2010-10-08
    if match.group(1).strip() == 'enable':
      return True
    else:
      return False
  else:
    return False 
  
def configure_service(script = "", arguments = None):
  """
  Run vdt configuration scripts with the given arguments
  """
  if arguments == None or script == "":
    return False
  
  vdt_script_path = os.path.join('usr',
                                 'bin',
                                 script)
  return run_script([vdt_script_path] + arguments)

def create_map_file(using_gums = False):
  """
  Check and create a mapfile if needed
  """

  map_file = os.path.join(CONFIG_DIRECTORY,
                          'osg-user-vo-map.txt')
  result = True
  try:
    if valid_user_vo_file(map_file):
      return result
    if using_gums:
      gums_script = os.path.join('usr',
                                 'bin',
                                 'gums-host-cron')
    else:
      gums_script = os.path.join('usr'
                                 'bin',
                                 'edg-mkgridmap')
      
    sys.stdout.write("Running %s, this process may take some time " % gums_script +
                     "to query vo and gums servers\n")
    sys.stdout.flush()
    if not run_script([gums_script]):
      return False    
  except IOError:
    result = False
  return result

def fetch_crl():
  """
  Run fetch_crl script and return a boolean indicating whether it was successful
  """

  try:
    if 'X509_CADIR' not in os.environ:
      sys.stdout.write("Can't find CA directory, assuming crl files not present\n")
    else:
      crl_files = glob.glob(os.path.join(os.environ['X509_CADIR'], '*.r0'))
      if len(crl_files) > 0:
        sys.stdout.write("CRLs exist, skipping fetch-crl invocation\n")
        sys.stdout.flush()
        return True
      
    crl_path = os.path.join('usr',
                            'bin',
                            'fetch-crl.cron')
                 
    if len(glob.glob(crl_path)) > 0:
      crl_script = glob.glob(crl_path)[0]
    
    sys.stdout.write("Running %s, this process make take " % crl_script +
                     "some time to fetch all the crl updates\n")
    sys.stdout.flush()
    if not run_script([crl_script]):
      return False
  except IOError:
    return False
  return True

def run_script(script):
  """
  Run a script and return True if it executes successfully (exit code 0)
  return False otherwise
  """
  
  if not valid_executable(script[0]):
    return False

  process = subprocess.Popen(script)
  process.communicate()
  if process.returncode != 0:
    return False
    
  return True          

def valid_boolean(config, section, option):
  """
  Check an option to make sure that it's a valid boolean option
  """
  try:
    if not config.has_option(section, option):
      return False
    config.getboolean(section, option)
    return True
  except ValueError:
    return False
    
  
def valid_executable(file_name):
  """
  Check to make sure that a file is present and a valid executable
  """
  
  
  try:
    if (not valid_file(file_name) or 
        not os.access(file_name, os.X_OK)):
      return False    
  except IOError:
    return False    
  return True

def get_condor_location(default_location = None):
  """
  Check environment variables to try to get condor location preferring 
  VDTSET_CONDOR_LOCATION over CONDOR_LOCATION
  """

  if not blank(default_location):
    return default_location
  if 'VDTSETUP_CONDOR_LOCATION' in os.environ:
    return os.path.normpath(os.environ['VDTSETUP_CONDOR_LOCATION'])
  elif 'CONDOR_LOCATION' in os.environ:
    return os.path.normpath(os.environ['CONDOR_LOCATION'])  
  else:
    return ""

def get_condor_config(default_config = None):
  """
  Check environment variables to try to get condor config preferring 
  VDTSET_CONDOR_CONFIG over CONDOR_CONFIG
  """
  
  if not blank(default_config):
    return default_config
  if 'VDTSETUP_CONDOR_CONFIG' in os.environ:
    return os.path.normpath(os.environ['VDTSETUP_CONDOR_CONFIG'])
  elif 'CONDOR_CONFIG' in os.environ:
    return os.path.normpath(os.environ['CONDOR_CONFIG'])
  elif (get_condor_location() == ''):
    return ''  
  else:
    return os.path.join(get_condor_location(),
                        'etc',
                        'condor_config')

def get_option(config,
               section,
               option,
               optional_settings = None, 
               defaults = None,
               option_type = types.StringType):
  """
  Get an option from a config file with optional defaults and mandatory 
  options.
  
  config should be a ConfigParser object
  section should be the ini section the option is located in
  option should be the option name
  option_type should be an optional variable indicating the type of the option
  optional_settings should be a list of options that don't have to be given
  defaults is  a dictionary of option : value pairs giving default values for 
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
      if blank(config.get(section, option)):
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

def valid_ini_file(filename):
  """
  Check an ini file to make sure that it's conforms to our requirements
  E.g. no repeated sections, no newlines in options
  
  returns True/False
  """
  
  if filename == "" or filename is None:
    return False
  
  if duplicate_sections_exist(filename):
    return False
  
  config_file = os.path.abspath(filename)
  configuration = ConfigParser.ConfigParser()
  configuration.read(config_file)
  
  sections = configuration.sections()
  try:
    for section in sections:
      for option in configuration.options(section):
        value = configuration.get(section, option)
        if "\n" in value:
          error_line = value.split('\n')[1]
          sys.stderr.write("INI syntax error in section %s: " % section)
          sys.stderr.write("The following line starts with a space: %s" % error_line)
          sys.stderr.write("Please removing the leading space")
          return False
  except ValueError:
    sys.stderr.write("syntax error in section %s with option %s" % (section, option))
    return False
        
  return True

def ce_config(configuration):
  """
  Check the configuration file and enable this module if the configuration
  is for a ce.
  
  A configuration is for a ce if it enables one of the jobmanager 
  sections
  """
  
  jobmanagers = ['PBS', 'Condor', 'SGE', 'LSF']
  for jobmanager in jobmanagers:
    if (configuration.has_section(jobmanager) and
        configuration.has_option(jobmanager, 'enabled') and 
        configuration.getboolean(jobmanager, 'enabled')):
      return True
  
  return False
  
def valid_vo_name(vo_name):
  """
  Check to see if a vo_name is valid 
  VO names should follow the guidelines as outlined at
  https://forge.ggf.org/sf/wiki/do/viewPage/projects.gin/wiki/GINVONaming
  basically RFC 1034 section 3.5 dictates the formatting (e.g. vo name
  should be a valid dns name)
  
  returns True / False
  """
  
  if vo_name is None:
    return False

  if valid_domain(vo_name):
    return True
  
  name_re = re.compile('[a-z0-9-]+', re.IGNORECASE)
  if name_re.match(vo_name):
    return True
  
  return False

def config_template(config_file):
  """
  Check to see if the config file specified in config_ini is the template file.
  config_file should be a ConfigParser instance
  
  returns True / False
  """
  
  if not config_file.has_section('Site Information'):
    return False
  
  if (not config_file.has_option('Site Information', 'email') or
      config_file.get('Site Information', 'email') == 'foo@my.domain'):
    return True

  return False
