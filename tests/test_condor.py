#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.configure_modules import condor
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger('test condor configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestCondor(unittest.TestCase):
  """
  Unit test class to test CondorConfiguration class
  """


  def testParsing(self):
    """
    Test condor parsing
    """
    
    config_file = get_test_config("condor/condor1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    options = {'OSG_JOB_MANAGER_HOME' : '/opt/condor',
               'OSG_CONDOR_LOCATION' : '/opt/condor',
               'OSG_CONDOR_CONFIG' : '/etc/condor/condor_config',
               'OSG_JOB_CONTACT' : 'my.domain.com/jobmanager-condor',
               'OSG_UTIL_CONTACT' : 'my.domain.com/jobmanager',
               'OSG_JOB_MANAGER' : 'Condor'}
    for option in options:
      value = options[option]
      self.failUnless(attributes.has_key(option), 
                      "Attribute %s missing" % option)
      err_msg = "Wrong value obtained for %s, " \
                "got %s instead of %s" % (option, attributes[option], value)
      self.failUnlessEqual(attributes[option], value, err_msg)




  def testParsingDisabled(self):
    """
    Test condor parsing when disabled
    """
    
    config_file = get_test_config("condor/condor_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")
    
  def testParsingIgnored(self):
    """
    Test condor parsing when ignored
    """
    
    config_file = get_test_config("condor/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")


  def testParsingDefaults(self):
    """
    Test handling of defaults when parsing a configuration
    """
    
    config_file = get_test_config("condor/condor_defaults1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)


    # check to see if we can get values from condor_* variables
    os.environ['CONDOR_LOCATION'] = '/my/condor'
    os.environ['CONDOR_CONFIG'] = '/my/condor/etc/condor_config'
    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_CONDOR_LOCATION'), 
                    'Attribute OSG_CONDOR_LOCATION missing')
    self.failUnlessEqual(attributes['OSG_CONDOR_LOCATION'], '/my/condor', 
                         'Wrong value obtained for OSG_CONDOR_LOCATION')
  
    self.failUnless(attributes.has_key('OSG_CONDOR_CONFIG'), 
                    'Attribute OSG_CONDOR_CONFIG missing')
    self.failUnlessEqual(attributes['OSG_CONDOR_CONFIG'], 
                         '/my/condor/etc/condor_config', 
                         'Wrong value obtained for OSG_CONDOR_CONFIG')
    
    # check when condor_config is not present
    del os.environ['CONDOR_CONFIG']
    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_CONDOR_LOCATION'), 
                    'Attribute OSG_CONDOR_LOCATION missing')
    self.failUnlessEqual(attributes['OSG_CONDOR_LOCATION'], '/my/condor', 
                         'Wrong value obtained for OSG_CONDOR_LOCATION')
  
    self.failUnless(attributes.has_key('OSG_CONDOR_CONFIG'), 
                    'Attribute OSG_CONDOR_CONFIG missing')
    self.failUnlessEqual(attributes['OSG_CONDOR_CONFIG'], 
                         '/etc/condor/condor_config', 
                         'Wrong value obtained for OSG_CONDOR_CONFIG')


    # check to make sure that config values take precedence over 
    # environment variables
    config_file = get_test_config("condor/condor1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    os.environ['CONDOR_LOCATION'] = '/my/condor1'
    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_CONDOR_LOCATION'), 
                    'Attribute OSG_CONDOR_LOCATION missing')
    self.failUnlessEqual(attributes['OSG_CONDOR_LOCATION'], '/opt/condor', 
                         'Wrong value obtained for OSG_CONDOR_LOCATION')
  
    self.failUnless(attributes.has_key('OSG_CONDOR_CONFIG'), 
                    'Attribute OSG_CONDOR_CONFIG missing')
    self.failUnlessEqual(attributes['OSG_CONDOR_CONFIG'], 
                         '/etc/condor/condor_config', 
                         'Wrong value obtained for OSG_CONDOR_CONFIG')

    # check to see if jobmanager home values get used in preference to other values
    config_file = get_test_config("condor/condor_defaults2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    os.environ['CONDOR_LOCATION'] = '/my/condor1'
    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_CONDOR_LOCATION'), 
                    'Attribute OSG_CONDOR_LOCATION missing')
    self.failUnlessEqual(attributes['OSG_CONDOR_LOCATION'], '/usr/local/condor', 
                         'Wrong value obtained for OSG_CONDOR_LOCATION')
  
    self.failUnless(attributes.has_key('OSG_CONDOR_CONFIG'), 
                    'Attribute OSG_CONDOR_CONFIG missing')
    self.failUnlessEqual(attributes['OSG_CONDOR_CONFIG'], 
                         '/etc/condor/condor_config', 
                         'Wrong value obtained for OSG_CONDOR_CONFIG')

                           
  def testMissingCondorLocation(self):
    """
    Test the checkAttributes function to see if it catches missing condor location
    """
    

    config_file = get_test_config("condor/missing_location.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing condor location")

  def testMissingCondorConfig(self):
    """
    Test the checkAttributes function to see if it catches missing
    condor config locations
    """
    

    for filename in ["./configs/condor/missing_config1.ini", 
                     "./configs/condor/missing_config2.ini"]:
      config_file = os.path.abspath(filename)
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
  
      settings = condor.CondorConfiguration(logger=global_logger)
      try:
        settings.parseConfiguration(configuration)
      except Exception, e:
        self.fail("Received exception while parsing configuration: %s" % e)
   
      attributes = settings.getAttributes()      
      self.failIf(settings.checkAttributes(attributes), 
                  "Did not notice missing condor config location: " + 
                  attributes['OSG_CONDOR_CONFIG'] )

  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """
    

    config_file = get_test_config("condor/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as missing")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """
    

    config_file = get_test_config("condor/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as missing")

    
  def testInvalidJobContact(self):
    """
    Test the checkAttributes function to see if it catches invalid job contacts
    """
    

    config_file = get_test_config("condor/invalid_job_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid host in jobcontact option")

  def testInvalidUtilityContact(self):
    """
    Test the checkAttributes function to see if it catches invalid
    utility contacts
    """
    

    config_file = get_test_config("condor/invalid_utility_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = condor.CondorConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid host in utility_contact option")
    
if __name__ == '__main__':
    unittest.main()
