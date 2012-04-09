#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import managedfork
from osg_configure.utilities import get_test_config

global_logger = logging.getLogger('test managedfork configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestManagedFork(unittest.TestCase):
  """
  Unit test class to test ManagedForkConfiguration class
  """

  def testParsing1(self):
    """
    Test managedfork parsing
    """
    
    config_file = get_test_config("managedfork/managedfork1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_MANAGEDFORK'), 
                    'Attribute OSG_MANAGEDFORK missing')
    self.failUnlessEqual(attributes['OSG_MANAGEDFORK'], 'Y', 
                         'Wrong value obtained for OSG_MANAGEDFORK')
    


  def testParsingDisabled(self):
    """
    Test managedfork parsing when disabled
    """
    
    config_file = get_test_config("managedfork/managedfork_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_MANAGEDFORK'), 
                    'Attribute OSG_MANAGEDFORK missing')
    self.failUnlessEqual(attributes['OSG_MANAGEDFORK'], 'N', 
                         'Wrong value obtained for OSG_MANAGEDFORK')
    
  def testParsingIgnored(self):
    """
    Test managedfork parsing when ignored
    """
    
    config_file = get_test_config("managedfork/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_MANAGEDFORK'), 
                    'Attribute OSG_MANAGEDFORK missing')
    self.failUnlessEqual(attributes['OSG_MANAGEDFORK'], 'N', 
                         'Wrong value obtained for OSG_MANAGEDFORK')
                                                        
  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = get_test_config("managedfork/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")


  def testAcceptLimitedTrue(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = get_test_config("managedfork/check_accept_limited_true.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")


  def testAcceptLimitedFalse(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = get_test_config("managedfork/check_accept_limited_false.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")

    
    
if __name__ == '__main__':
    unittest.main()
