#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path 
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import lsf
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

class TestLSF(unittest.TestCase):
  """
  Unit test class to test LSFConfiguration class
  """

  def testParsing(self):
    """
    Test configuration parsing
    """
    
    config_file = get_test_config("lsf/lsf1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = lsf.LSFConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    options = {'OSG_JOB_MANAGER_HOME' : '/opt/lsf',
               'OSG_LSF_LOCATION' : '/opt/lsf',
               'OSG_JOB_CONTACT' : 'my.domain.com/jobmanager-lsf',
               'OSG_UTIL_CONTACT' : 'my.domain.com/jobmanager',
               'OSG_JOB_MANAGER' : 'LSF'}
    for option in options:
      value = options[option]
      self.failUnless(attributes.has_key(option), 
                      "Attribute %s missing" % option)
      err_msg = "Wrong value obtained for %s, " \
                "got %s instead of %s" % (option, attributes[option], value)
      self.failUnlessEqual(attributes[option], value, err_msg)




  def testParsingDisabled(self):
    """
    Test parsing when disabled
    """
    
    config_file = get_test_config("lsf/lsf_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = lsf.LSFConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")
    
  def testParsingIgnored(self):
    """
    Test parsing when ignored
    """
    
    config_file = get_test_config("lsf/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = lsf.LSFConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Ignored configuration should have no attributes")

                           
  def testMissingLSFLocation(self):
    """
    Test the checkAttributes function to see if it catches missing LSF location
    """
    config_file = get_test_config("lsf/missing_location.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = lsf.LSFConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing LSF location")


  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """
    config_file = get_test_config("lsf/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = lsf.LSFConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """
    config_file = get_test_config("lsf/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = lsf.LSFConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")
    
  def testInvalidJobContact(self):
    """
    Test the checkAttributes function to see if it catches invalid job contacts
    """
    config_file = get_test_config("lsf/invalid_job_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = lsf.LSFConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      print e
      self.fail("Received exception while parsing configuration")
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid host in jobcontact option")

  def testInvalidUtilityContact(self):
    """
    Test the checkAttributes function to see if it catches invalid
    utility contacts
    """
    config_file = get_test_config("lsf/invalid_utility_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = lsf.LSFConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid host in utility_contact option")
    
if __name__ == '__main__':
  console = logging.StreamHandler()
  console.setLevel(logging.ERROR)
  global_logger.addHandler(console)
  unittest.main()
