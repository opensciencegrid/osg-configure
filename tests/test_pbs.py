#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path if it's not there at present
try:
  from configure_osg.modules import utilities
except ImportError:
  pathname = '../'
  sys.path.append(pathname)
  from configure_osg.modules import utilities

from configure_osg.modules import exceptions


from configure_osg.configure_modules import pbs

global_logger = logging.getLogger('test pbs configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestPBS(unittest.TestCase):
  """
  Unit test class to test PBSConfiguration class
  """

  def testParsing(self):
    """
    Test configuration parsing
    """
    
    config_file = os.path.abspath("./configs/pbs/pbs1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = pbs.PBSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    options = {'OSG_JOB_MANAGER_HOME' : '/opt/pbs',
               'OSG_PBS_LOCATION' : '/opt/pbs',
               'OSG_JOB_CONTACT' : 'my.domain.com/jobmanager-pbs',
               'OSG_UTIL_CONTACT' : 'my.domain.com/jobmanager',
               'OSG_WS_GRAM' : 'Y',
               'OSG_JOB_MANAGER' : 'PBS'}
    for option in options:
      value = options[option]
      self.failUnless(attributes.has_key(option), 
                      "Attribute %s missing" % option)
      err_msg = "Wrong value obtained for %s, " \
                "got %s instead of %s" % (option, attributes[option], value)
      self.failUnlessEqual(attributes[option], value, err_msg)




  def testParsingDisabled(self):
    """
    Test PBS section parsing when set to disabled
    """
    
    config_file = os.path.abspath("./configs/pbs/pbs_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = pbs.PBSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")
    
  def testParsingIgnored(self):
    """
    Test PBS section parsing when set to Ignore
    """
    
    config_file = os.path.abspath("./configs/pbs/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = pbs.PBSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Ignored configuration should have no attributes")


  def testAttributeGeneration1(self):
    """
    Test the creation of a config file given attributes
    """
    
    config_file = os.path.abspath("./configs/pbs/pbs1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = pbs.PBSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()    
    new_config = ConfigParser.SafeConfigParser()
    settings.generateConfigFile(attributes.items(), new_config)
    section_name = 'PBS'
    self.failUnless(new_config.has_section(section_name), 
                    "%s section not created in config file" % section_name)
    
    options = {'enabled' : 'True',
               'job_contact' : 'my.domain.com/jobmanager-pbs',
               'util_contact' : 'my.domain.com/jobmanager',
               'wsgram' : 'True',               
               'pbs_location' : '/opt/pbs'}
    for option in options:      
      self.failUnless(new_config.has_option(section_name, option), 
                      "Option %s missing" % option)
      self.failUnlessEqual(new_config.get(section_name, option), 
                           options[option], 
                           "Wrong value obtained for %s, expected %s, got %s" %
                           (option,
                            options[option],
                            new_config.get(section_name, option)))
                            
    
  def testAttributeGeneration2(self):
    """
    Test the creation of a config file given attributes
    """
    
    config_file = os.path.abspath("./configs/pbs/pbs_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = pbs.PBSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()    
    new_config = ConfigParser.SafeConfigParser()
    settings.generateConfigFile(attributes.items(), new_config)
    section_name = 'PBS'
    self.failIf(new_config.has_section(section_name), 
                "%s section created in config file" % section_name)
    
                            
  def testMissingPBSLocation(self):
    """
    Test the checkAttributes function to see if it catches missing pbs location
    """
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/pbs/missing_location.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = pbs.PBSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing pbs location")


  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/pbs/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = pbs.PBSConfiguration(logger=global_logger)
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
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/pbs/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = pbs.PBSConfiguration(logger=global_logger)
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
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/pbs/invalid_job_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = pbs.PBSConfiguration(logger=global_logger)
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
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/pbs/invalid_utility_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = pbs.PBSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid host in utility_contact option")
    
if __name__ == '__main__':
    unittest.main()
