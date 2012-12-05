#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser

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

  def test_valid_domain(self):
    """
    Check the valid_domain functionality
    """
    test_domain = "testing"
    self.failIf(validation.valid_domain(test_domain),
                "testing marked as a valid domain address")
    
    test_domain = "34c93F.39f@~#"
    self.failIf(validation.valid_domain(test_domain),
                "testing marked as a valid domain address")

    test_domain = "t-ea.34.org"
    self.failUnless(validation.valid_domain(test_domain), 
                    "t-ea.34.org marked as an invalid domain address")
      
    test_domain = "uchicago.edu"
    self.failUnless(validation.valid_domain(test_domain, resolve = True),
                    "uchicago.edu marked as an invalid domain address")

    
    test_domain = "invalid.invalid"
    self.failIf(validation.valid_domain(test_domain, resolve = True),
                "invalid.invalid marked as an valid domain address")

  def test_valid_email(self):
    """
    Check the valid email functionality
    """
    failed = False
    test_email = "fake@email@testing"
    self.failIf(validation.valid_email(test_email),
                "fake@email@testing marked as a valid email address")
    
    test_email = "a.3a-3bc@t-ea.34.org"
    self.failUnless(validation.valid_email(test_email),
                    "a.3a-3bc@t-ea.34.org marked as an invalid email " \
                    "address")
    

  def test_valid_location(self):
    """
    Check the valid_location functionality
    """

    test_location = get_test_config("cemon/ignore_bdii.ini")
    self.failUnless(validation.valid_location(test_location), 
                    "%s not marked as a valid location" % test_location)

    
    test_location = "configs/invalid_foo.config"
    self.failIf(validation.valid_location(test_location), 
                "%s marked as a valid location" % test_location)      

  def test_valid_file_location(self):
    """
    Check the valid_file functionality
    """
    test_file = get_test_config("utilities/valid_boolean.ini")
    message = "%s not marked as a valid file location" % test_file
    self.failUnless(validation.valid_location(test_file), message)
    
    test_file = "configs/invalid_foo.config"
    message = "%s marked as a valid file location" % test_file
    self.failIf(validation.valid_location(test_file),
                message)
    

  def test_valid_user(self):
    """
    Check the valid_user functionality
    """

    self.failUnless(validation.valid_user('root'),
                    "root not marked as a valid user")
    
    self.failIf(validation.valid_user('hacked'), 
                "'hacked' is considered a valid user")
   
  def test_valid_user_vo_file(self):
    """
    Test functionality of valid_user_vo_file function
    """
    
    test_file = get_test_config("./test_files/valid-user-vo-map.txt")
    self.failUnless(validation.valid_user_vo_file(test_file, False), 
                    "Valid file flagged as invalid")
    
    test_file = get_test_config("./test_files/invalid-user-vo-map.txt")
    self.failIf(validation.valid_user_vo_file(test_file, False), 
                "Invalid file flagged as valid")
    bad_lines = validation.valid_user_vo_file(test_file, True)[1]
    standard_lines =  ['fdjkf394f023', 'sam= 34f3']
    self.failUnlessEqual(bad_lines, standard_lines, 
                         "Wrong lines from the vo map obtained, " +
                         "got\n%s" % (bad_lines) +
                         "\nexpected\n%s" % (standard_lines))
    
  def test_valid_boolean(self):
    """
    Test functionality of valid_boolean function
    """
    config_file = get_test_config('utilities/valid_boolean.ini')
    config = ConfigParser.SafeConfigParser()
    config.read(config_file)
    self.failIf(validation.valid_boolean(config, 'Test', 'invalid_bool'),
                'invalid_bool flagged as valid')
    self.failIf(validation.valid_boolean(config, 'Test', 'invalid_bool2'),
                'invalid_bool2 flagged as valid')
    self.failIf(validation.valid_boolean(config, 'Test', 'missing'),
                'invalid_bool2 flagged as valid')
    self.failUnless(validation.valid_boolean(config, 'Test', 'valid_bool'),
                    'valid_bool flagged as invalid')
    self.failUnless(validation.valid_boolean(config, 'Test', 'valid_bool2'),
                    'valid_bool2 flagged as invalid')

  def test_valid_executable(self):
    """
    Test functionality of valid_executable function
    """
    
    binary = "/bin/ls"
    text = get_test_config("test_files/subscriptions.xml")
    missing = "./test_files/foo"
    
    self.failIf(validation.valid_executable(missing), 
                "Non-existent file is not a valid executable")
    self.failIf(validation.valid_executable(text), 
                "Text file is not a valid executable")
    self.failUnless(validation.valid_executable(binary), 
                    "/bin/ls should be a valid binary")
    

  def test_valid_file2(self):
    """
    Test functionality of valid_file function
    """

    filename = get_test_config('utilities/newline.ini')
    self.failIf(validation.valid_ini_file(filename),
                "Didn't detect newline in %s"  % filename)

    filename = get_test_config('utilities/valid_boolean.ini')
    self.failUnless(validation.valid_ini_file(filename),
                    "Got error on valid file %s" % filename)
    
  def test_valid_references(self):
    """
    Test functionality of invalid_references_exist and make sure 
    it catches invalid references correctly and lets valid references
    go
    """

    filename = get_test_config('utilities/invalid_ref1.ini')
    self.failIf(validation.valid_ini_file(filename),
                "Didn't detect invalid reference in %s" % filename)

    filename = get_test_config('utilities/invalid_ref2.ini')
    self.failIf(validation.valid_ini_file(filename),
                "Didn't detect invalid reference in %s" % filename)

    filename = get_test_config('utilities/valid_ref1.ini')
    self.failUnless(validation.valid_ini_file(filename),
                    "Got error on valid file %s" % filename)


if __name__ == '__main__':
  unittest.main()

