"""Unit tests to test validation module"""

#pylint: disable=W0703
#pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import imp

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import validation
from osg_configure.modules.utilities import get_test_config

pathname = os.path.join('../scripts', 'osg-configure')
if not os.path.exists(pathname):
  pathname = os.path.join('/', 'usr', 'sbin', 'osg-configure')
  if not os.path.exists(pathname):
    raise Exception("Can't find osg-configure script")
  
try:
  has_configure_osg = False
  fp = open(pathname, 'r')
  configure_osg = imp.load_module('test_module', fp, pathname, ('', '', 1))
  has_configure_osg = True
except:
  raise Exception("Can't import osg-configure script")


class TestValidation(unittest.TestCase):
  """Unit test class for testing validation module"""
  
  def test_valid_domain(self):
    """
    Check the valid_domain functionality
    """
    test_domain = "testing"
    self.assertFalse(validation.valid_domain(test_domain),
                     "testing marked as a valid domain address")
    
    test_domain = "34c93F.39f@~#"
    self.assertFalse(validation.valid_domain(test_domain),
                     "testing marked as a valid domain address")

    test_domain = "t-ea.34.org"
    self.assertTrue(validation.valid_domain(test_domain), 
                    "t-ea.34.org marked as an invalid domain address")
      
    test_domain = "uchicago.edu"
    self.assertTrue(validation.valid_domain(test_domain, resolve = True),
                    "uchicago.edu marked as an invalid domain address")

    
    test_domain = "invalid.invalid"
    self.assertFalse(validation.valid_domain(test_domain, resolve = True),
                     "invalid.invalid marked as an valid domain address")

  def test_valid_email(self):
    """
    Check the valid email functionality
    """
    test_email = "fake@email@testing"
    self.assertFalse(validation.valid_email(test_email),
                     "fake@email@testing marked as a valid email address")
    
    test_email = "a.3a-3bc@t-ea.34.org"
    self.assertTrue(validation.valid_email(test_email),
                    "a.3a-3bc@t-ea.34.org marked as an invalid email " \
                    "address")
    

  def test_valid_location(self):
    """
    Check the valid_location functionality
    """

    test_location = get_test_config("cemon/ignore_bdii.ini")
    self.assertTrue(validation.valid_location(test_location), 
                    "%s not marked as a valid location" % test_location)

    
    test_location = "configs/invalid_foo.config"
    self.assertFalse(validation.valid_location(test_location), 
                     "%s marked as a valid location" % test_location)      

  def test_valid_file_location(self):
    """
    Check the valid_file functionality
    """
    test_file = get_test_config("utilities/valid_boolean.ini")
    message = "%s not marked as a valid file location" % test_file
    self.assertTrue(validation.valid_location(test_file), message)
    
    test_file = "configs/invalid_foo.config"
    message = "%s marked as a valid file location" % test_file
    self.assertFalse(validation.valid_location(test_file),
                     message)
    

  def test_valid_user(self):
    """
    Check the valid_user functionality
    """

    self.assertTrue(validation.valid_user('root'),
                    "root not marked as a valid user")
    
    self.assertFalse(validation.valid_user('hacked'), 
                     "'hacked' is considered a valid user")
   
  def test_valid_user_vo_file(self):
    """
    Test functionality of valid_user_vo_file function
    """
    
    test_file = get_test_config("./test_files/valid-user-vo-map.txt")
    self.assertTrue(validation.valid_user_vo_file(test_file, False), 
                    "Valid file flagged as invalid")
    
    test_file = get_test_config("./test_files/invalid-user-vo-map.txt")
    self.assertFalse(validation.valid_user_vo_file(test_file, False), 
                     "Invalid file flagged as valid")
    bad_lines = validation.valid_user_vo_file(test_file, True)[1]
    standard_lines =  ['fdjkf394f023', 'sam= 34f3']
    self.assertEqual(bad_lines, standard_lines, 
                     "Wrong lines from the vo map obtained, " +
                     "got:\n%s\n" % (bad_lines) +
                     "expected:\n%s" % (standard_lines))
    
  def test_valid_boolean(self):
    """
    Test functionality of valid_boolean function
    """
    config_file = get_test_config('utilities/valid_boolean.ini')
    config = ConfigParser.SafeConfigParser()
    config.read(config_file)
    self.assertFalse(validation.valid_boolean(config, 'Test', 'invalid_bool'),
                     'invalid_bool flagged as valid')
    self.assertFalse(validation.valid_boolean(config, 'Test', 'invalid_bool2'),
                     'invalid_bool2 flagged as valid')
    self.assertFalse(validation.valid_boolean(config, 'Test', 'missing'),
                     'invalid_bool2 flagged as valid')
    self.assertTrue(validation.valid_boolean(config, 'Test', 'valid_bool'),
                    'valid_bool flagged as invalid')
    self.assertTrue(validation.valid_boolean(config, 'Test', 'valid_bool2'),
                    'valid_bool2 flagged as invalid')

  def test_valid_executable(self):
    """
    Test functionality of valid_executable function
    """
    
    binary = "/bin/ls"
    text = get_test_config("test_files/subscriptions.xml")
    missing = "./test_files/foo"
    
    self.assertFalse(validation.valid_executable(missing), 
                     "Non-existent file is not a valid executable")
    self.assertFalse(validation.valid_executable(text), 
                     "Text file is not a valid executable")
    self.assertTrue(validation.valid_executable(binary), 
                    "/bin/ls should be a valid binary")
    

  def test_valid_file(self):
    """
    Test functionality of valid_file function
    """

    filename = get_test_config('utilities/newline.ini')
    _stderr = sys.stderr
    sys.stderr = file(os.devnull, 'wb')
    # need to do this instead of putting this in assert so that stderr can 
    # be restored after call
    result = validation.valid_ini_file(filename)
    self.assertFalse(result,
                     "Didn't detect newline in %s"  % filename)
    # test whether we catch sections that has a space before the first setting
    filename = get_test_config('utilities/section_space.ini')
    self.assertFalse(result,
                     "Didn't detect space in %s"  % filename)
    sys.stderr = _stderr

    filename = get_test_config('utilities/valid_boolean.ini')    
    self.assertTrue(validation.valid_ini_file(filename),
                    "Got error on valid file %s" % filename)
    
    filename = get_test_config('utilities/valid_variable.ini')
    self.assertTrue(validation.valid_ini_file(filename),
                    "Got error on valid file %s" % filename)
    
    
    
# Functionality has been broken for several versions and not going to be added in 
# 1.0.40 will be fixed for 1.0.41    
#   def test_valid_references(self):
#     """
#     Test functionality of invalid_references_exist and make sure 
#     it catches invalid references correctly and lets valid references
#     go
#     """
#     filename = get_test_config('utilities/invalid_ref1.ini')
#     _stderr = sys.stderr
#     sys.stderr = file(os.devnull, 'wb')
#     # need to do this instead of putting this in assert so that stderr can 
#     # be restored after call
#     result = validation.valid_ini_references(filename)
#     sys.stderr = _stderr
#     self.assertFalse(result,
#                      "Didn't detect invalid reference in %s" % filename)
# 
#     filename = get_test_config('utilities/invalid_ref2.ini')
#     _stderr = sys.stderr
#     sys.stderr = file(os.devnull, 'wb')
#     # need to do this instead of putting this in assert so that stderr can 
#     # be restored after call
#     result = validation.valid_ini_references(filename)
#     sys.stderr = _stderr
#     self.assertFalse(result,
#                      "Didn't detect invalid reference in %s" % filename)
# 
#     filename = get_test_config('utilities/valid_ref1.ini')
#     self.assertTrue(validation.valid_ini_references(filename),
#                     "Got error on valid file %s" % filename)


  def test_valid_contact(self):
    """
    Test functionality of valid_contact to make sure that it rejects incorrect
    contact strings and accepts correct ones
    """
    
    jobmanagers = ['pbs', 'lsf', 'sge', 'condor']
    domain = 'test.com'
    port = 8888
    
    for jobmanager in jobmanagers:
      for test_manager in jobmanagers:
        contact = "%s:%s/jobmanager-%s" % (domain, port, test_manager)
        if test_manager == jobmanager:
          self.assertTrue(validation.valid_contact(contact, 
                                                   jobmanager), 
                          "%s labeled as invalid contact" % contact)
        else:
          self.assertFalse(validation.valid_contact(contact, 
                                                    jobmanager), 
                           "%s labeled as valid contact" % contact)
    port = '234a'
    for jobmanager in jobmanagers:
      contact = "%s:%s/jobmanager-%s" % (domain, port, jobmanager)
      self.assertFalse(validation.valid_contact(contact, jobmanager), 
                       "%s labeled as valid contact" % contact)
    port = 8888
    domain = 'fdf^34@!'
    for jobmanager in jobmanagers:
      contact = "%s:%s/jobmanager-%s" % (domain, port, jobmanager)
      self.assertFalse(validation.valid_contact(contact, jobmanager), 
                       "%s labeled as valid contact" % contact)
          
if __name__ == '__main__':
  unittest.main()

