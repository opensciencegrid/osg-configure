"""Unit tests to test managed fork configuration"""

#pylint: disable=W0703
#pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.configure_modules import managedfork
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger(__name__)
if sys.version_info[0] >= 2 and sys.version_info[1] > 6:
  global_logger.addHandler(logging.NullHandler())
else:
  # NullHandler is only in python 2.7 and above
  class NullHandler(logging.Handler):
    def emit(self, record):
      pass
            
  global_logger.addHandler(NullHandler())
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
    self.assertTrue(attributes.has_key('OSG_MANAGEDFORK'), 
                    'Attribute OSG_MANAGEDFORK missing')
    self.assertEqual(attributes['OSG_MANAGEDFORK'], 
                     'Y', 
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
    self.assertTrue(attributes.has_key('OSG_MANAGEDFORK'), 
                    'Attribute OSG_MANAGEDFORK missing')
    self.assertEqual(attributes['OSG_MANAGEDFORK'], 
                     'N', 
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
    self.assertTrue(attributes.has_key('OSG_MANAGEDFORK'), 
                    'Attribute OSG_MANAGEDFORK missing')
    self.assertEqual(attributes['OSG_MANAGEDFORK'], 
                     'N', 
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
    self.assertTrue(settings.checkAttributes(attributes), 
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
    self.assertTrue(settings.checkAttributes(attributes), 
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
    self.assertTrue(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")

  def testServiceList(self):
    """
    Test to make sure right services get returned
    """
    
    config_file = get_test_config("managedfork/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set(['globus-gatekeeper', 'condor'])
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))
    
    
    config_file = get_test_config("managedfork/managedfork_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set()
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))    

    config_file = get_test_config("managedfork/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = managedfork.ManagedForkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set()
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))    
    
if __name__ == '__main__':
  console = logging.StreamHandler()
  console.setLevel(logging.ERROR)
  global_logger.addHandler(console)
  unittest.main()
