#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import sge

global_logger = logging.getLogger('test sge configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestSGE(unittest.TestCase):
  """
  Unit test class to test SGEConfiguration class
  """

  def testParsing(self):
    """
    Test configuration parsing
    """
    
    config_file = os.path.abspath("./configs/sge/sge1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    options = {'OSG_JOB_MANAGER_HOME' : './test_files',
               'OSG_SGE_LOCATION' : './test_files',
               'OSG_SGE_ROOT' : './test_files',
               'OSG_JOB_CONTACT' : 'my.domain.com/jobmanager-sge',
               'OSG_UTIL_CONTACT' : 'my.domain.com/jobmanager',
               'OSG_SGE_CELL' : 'sge',
               'OSG_JOB_MANAGER' : 'SGE'}
    for option in options:
      value = options[option]
      self.failUnless(attributes.has_key(option), 
                      "Attribute %s missing" % option)
      err_msg = "Wrong value obtained for %s, " \
                "got %s instead of %s" % (option, attributes[option], value)
      self.failUnlessEqual(attributes[option], value, err_msg)




  def testParsingDisabled(self):
    """
    Test parsing disabled configuration
    """
    
    config_file = os.path.abspath("./configs/sge/sge_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")
    
  def testParsingIgnored(self):
    """
    Test parsing ignored configuration
    """
    
    config_file = os.path.abspath("./configs/sge/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Ignored configuration should have no attributes")

    
  def testMissingAttribute(self):
    """
    Test the parsing when attributes are missing, should get exceptions
    """


    mandatory = ['sge_root',
                 'sge_cell',
                 'job_contact',
                 'util_contact']
    for option in mandatory:
      config_file = os.path.abspath("./configs/sge/sge1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('SGE', option)
      
      settings = sge.SGEConfiguration(logger=global_logger)
      self.failUnlessRaises(exceptions.SettingError, 
                            settings.parseConfiguration,
                            configuration)
   
                            

  def testMissingSGERoot(self):
    """
    Test the checkAttributes function to see if it catches missing SGE location
    """


    config_file = os.path.abspath("./configs/sge/missing_root.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing SGE root")

  def testMissingSGECell(self):
    """
    Test the checkAttributes function to see if it catches missing SGE cell
    """


    config_file = os.path.abspath("./configs/sge/missing_cell.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing SGE root")

  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """


    config_file = os.path.abspath("./configs/sge/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
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


    config_file = os.path.abspath("./configs/sge/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
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


    config_file = os.path.abspath("./configs/sge/invalid_job_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
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

    config_file = os.path.abspath("./configs/sge/invalid_utility_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid host in utility_contact option")
    
if __name__ == '__main__':
    unittest.main()
