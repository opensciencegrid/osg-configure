""" Module to hold various validation functions """

import re
import socket
import os
import pwd
import ConfigParser
import sys

__all__ = ['valid_domain', 
           'valid_email', 
           'valid_location', 
           'valid_file',
           'valid_directory',           
           'valid_user',
           'valid_user_vo_file',
           'valid_vo_name',
           'valid_boolean',
           'valid_executable',
           'valid_ini_file',
           'valid_contact']


def valid_domain(host, resolve=False):
  """Check to see if the string passed in is a valid domain"""
  if len(host) == 0:
    return False
  match = re.match(r'^[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)+$', 
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
  match = re.match(r'(?:[a-zA-Z\-_+0-9.]+)@([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)+)', 
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

def valid_directory(location):
  """Returns True if location points to an existing file"""
  if os.path.exists(location):
    return os.path.isdir(location)
  
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
  comment = re.compile(r'^\s*#')
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

def valid_ini_file(filename):
  """
  Check an ini file to make sure that it's conforms to our requirements
  E.g. no repeated sections, no newlines in options
  
  returns True/False
  """  
  if filename == "" or filename is None:
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
          # pylint: disable-msg=E1103
          error_line = value.split('\n')[1]
          sys.stderr.write("INI syntax error in section %s: \n" % section)
          sys.stderr.write("The following line starts with a space: %s\n" % error_line)
          sys.stderr.write("Please removing the leading space\n")
          return False
  except ValueError:
    sys.stderr.write("syntax error in section %s with option %s\n" % (section, option))
    return False
        
  return True


def valid_contact(contact, jobmanager):
  """
  Check a contact string to make sure that it's valid, e.g. host[:port]/jobmanager
  returns True or False  
  """
  
  if len(contact.split('/')) != 2:
    return False
  (host_part, jobmanager_part) = contact.split('/')
  
  if '-' in jobmanager_part and jobmanager_part.split('-')[1] != jobmanager:
    # invalid jobmanager
    return False
  
  if ':' in host_part:
    (host, port) = host_part.split(':')
    try:
      # test to make sure port is an integer
      int(port)
      return valid_domain(host)
    except ValueError:
      return False
  else:
    return valid_domain(host_part)

  return True