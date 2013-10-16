"""Unit tests to test sge configuration"""

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

from osg_configure.modules import exceptions
from osg_configure.configure_modules import sge
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

class TestSGE(unittest.TestCase):
  """
  Unit test class to test SGEConfiguration class
  """

  def testParsing(self):
    """
    Test configuration parsing
    """
    
    config_file = get_test_config("sge/sge1.ini")
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
      self.assertTrue(attributes.has_key(option), 
                      "Attribute %s missing" % option)
      err_msg = "Wrong value obtained for %s, " \
                "got %s instead of %s" % (option, attributes[option], value)
      self.assertEqual(attributes[option], value, err_msg)




  def testParsingDisabled(self):
    """
    Test parsing disabled configuration
    """
    
    config_file = get_test_config("sge/sge_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.assertEqual(len(attributes), 0, 
                     "Disabled configuration should have no attributes")
    
  def testParsingIgnored(self):
    """
    Test parsing ignored configuration
    """
    
    config_file = get_test_config("sge/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.assertEqual(len(attributes), 0, 
                     "Ignored configuration should have no attributes")

    
  def testMissingAttribute(self):
    """
    Test the parsing when attributes are missing, should get exceptions
    """


    mandatory = ['sge_root',
                 'sge_cell',
                 'sge_bin_location',
                 'job_contact',
                 'util_contact']
    for option in mandatory:
      config_file = get_test_config("sge/sge1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('SGE', option)
      
      settings = sge.SGEConfiguration(logger=global_logger)
      self.assertRaises(exceptions.SettingError, 
                        settings.parseConfiguration,
                        configuration)
   
                            

  def testMissingSGERoot(self):
    """
    Test the checkAttributes function to see if it catches missing SGE location
    """


    config_file = get_test_config("sge/missing_root.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.assertFalse(settings.checkAttributes(attributes), 
                     "Did not notice missing SGE root")

  def testMissingSGECell(self):
    """
    Test the checkAttributes function to see if it catches missing SGE cell
    """


    config_file = get_test_config("sge/missing_cell.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.assertFalse(settings.checkAttributes(attributes), 
                     "Did not notice missing SGE root")

  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """


    config_file = get_test_config("sge/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    root = os.path.join(config_file[:-16], 'test_files')
    configuration.set('SGE', 'sge_root', root)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.assertTrue(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """


    config_file = get_test_config("sge/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    root = os.path.join(config_file[:-17], 'test_files')
    configuration.set('SGE', 'sge_root', root)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.assertTrue(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")
    
  def testLogDir(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """


    config_file = get_test_config("sge/sge_log_dir.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    root = os.path.join(config_file[:-20], 'test_files')
    configuration.set('SGE', 'sge_root', root)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    err_msg = "Got incorrect value, expected " + \
              "%s but " % get_test_config('./test_files/subscriptions.xml') + \
               "got %s instead\n" %  settings.options['log_file'].value
    self.assertEqual(settings.options['log_file'].value,
                     '/etc/hosts',
                     err_msg)
                     
    attributes = settings.getAttributes()    
    self.assertTrue(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")

  def testLogFile(self):
    """
    Test the checkAttributes function to see if it works on valid settings 
    using log_directory or log_path
    """


    config_file = get_test_config("sge/sge_log_file.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    root = os.path.join(config_file[:-20], 'test_files')
    configuration.set('SGE', 'sge_root', root)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)


    err_msg = "Got incorrect value, expected " + \
              "%s but " % get_test_config('./test_files/subscriptions.xml') + \
               "got %s instead\n" %  settings.options['log_file'].value
 
    self.assertEqual(settings.options['log_file'].value,
                     '/etc/hosts',
                     err_msg)
    
    attributes = settings.getAttributes()
    self.assertTrue(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")

    
  def testInvalidJobContact(self):
    """
    Test the checkAttributes function to see if it catches invalid job contacts
    """


    config_file = get_test_config("sge/invalid_job_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      print e
      self.fail("Received exception while parsing configuration")
 
    attributes = settings.getAttributes()
    self.assertFalse(settings.checkAttributes(attributes), 
                     "Did not notice invalid host in jobcontact option")

  def testInvalidUtilityContact(self):
    """
    Test the checkAttributes function to see if it catches invalid
    utility contacts
    """

    config_file = get_test_config("sge/invalid_utility_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.assertFalse(settings.checkAttributes(attributes), 
                     "Did not notice invalid host in utility_contact option")

  def testServiceList(self):
    """
    Test to make sure right services get returned
    """
    
    config_file = get_test_config("sge/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set(['globus-gatekeeper',
                                  'globus-gridftp-server'])
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))
    
    
    config_file = get_test_config("sge/seg_enabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set(['globus-gatekeeper', 
                                  'globus-gridftp-server',
                                  'globus-scheduler-event-generator'])
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))

    config_file = get_test_config("sge/sge_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set()
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))    

    config_file = get_test_config("sge/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = sge.SGEConfiguration(logger=global_logger)
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
