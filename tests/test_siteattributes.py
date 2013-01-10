"""Unit tests to test site attribute configuration"""

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
from osg_configure.configure_modules import siteattributes
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

class TestSiteAttributes(unittest.TestCase):
  """
  Unit test class to test SiteAttributes class
  """


  def testParsing1(self):
    """
    Test siteattributes parsing
    """
    
    config_file = get_test_config("siteattributes/siteattributes1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    variables = {'OSG_GROUP' : 'OSG-ITB',
                 'OSG_HOSTNAME' : 'example.com',
                 'OSG_SITE_NAME': 'MY_SITE',
                 'OSG_SPONSOR' : 'osg:100',
                 'OSG_SITE_INFO' : 'http://example/com/policy.html',
                 'OSG_CONTACT_NAME' : 'Admin Name',
                 'OSG_CONTACT_EMAIL' : 'myemail@example.com',
                 'OSG_SITE_CITY' : 'Chicago',
                 'OSG_SITE_COUNTRY' : 'US',
                 'OSG_SITE_LONGITUDE' : '84.23',
                 'OSG_SITE_LATITUDE' : '23.32'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))
        
  def testParsing2(self):
    """
    Test siteattributes parsing
    """
    
    config_file = get_test_config("siteattributes/siteattributes2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    variables = {'OSG_GROUP' : 'OSG',
                 'OSG_HOSTNAME' : 'example.com',
                 'OSG_SITE_NAME': 'MY_SITE',
                 'OSG_SPONSOR' : 'osg:50 atlas:50',
                 'OSG_SITE_INFO' : 'http://example/com/policy.html',
                 'OSG_CONTACT_NAME' : 'Admin Name',
                 'OSG_CONTACT_EMAIL' : 'myemail@example.com',
                 'OSG_SITE_CITY' : 'Chicago',
                 'OSG_SITE_COUNTRY' : 'US',
                 'OSG_SITE_LONGITUDE' : '-84.23',
                 'OSG_SITE_LATITUDE' : '-23.32'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))


  def testParsing3(self):
    """
    Test siteattributes parsing
    """
    
    config_file = get_test_config("siteattributes/siteattributes3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    variables = {'OSG_GROUP' : 'OSG',
                 'OSG_HOSTNAME' : 'example.com',
                 'OSG_SITE_NAME': 'MY_SITE',
                 'OSG_SPONSOR' : 'osg:50 atlas:50',
                 'OSG_SITE_INFO' : 'http://example/com/policy.html',
                 'OSG_CONTACT_NAME' : 'Admin Name',
                 'OSG_CONTACT_EMAIL' : 'myemail@example.com',
                 'OSG_SITE_CITY' : 'Chicago',
                 'OSG_SITE_COUNTRY' : 'US',
                 'OSG_SITE_LONGITUDE' : '-84.23',
                 'OSG_SITE_LATITUDE' : '-23.32'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))
    if ('resource_group' not in settings.options or
        settings.options['resource_group'].value != 'RESOURCE_GROUP'):
      self.fail('resource_group not present or not set to RESOURCE_GROUP')

  def testMissingAttribute(self):
    """
    Test the parsing when attributes are missing, should get exceptions
    """
    config_file = get_test_config("siteattributes/siteattributes2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
        

    mandatory = ['host_name',
                 'sponsor',
                 'contact',
                 'email',
                 'city',
                 'country',
                 'longitude',
                 'latitude']
    for option in mandatory:
      config_file = get_test_config("siteattributes/siteattributes1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('Site Information', option)

      settings = siteattributes.SiteAttributes(logger=global_logger)
      self.failUnlessRaises(exceptions.SettingError, 
                            settings.parseConfiguration, 
                            configuration)

  def testInvalidLatitude(self):
    """
    Test the checkAttributes with invalid latitude values
    """
    
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_latitude1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid latitude ignored")
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_latitude2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid latitude ignored")
  
  def testInvalidLongitude(self):
    """
    Test the checkAttributes with invalid longitude values
    """
    
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_longitude1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid latitude ignored")
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_longitude2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid latitude ignored")

  def testInvalidHostname(self):
    """
    Test the checkAttributes with invalid hostname
    """
    
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_hostname.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid hostname ignored")
    
  def testInvalidEmail(self):
    """
    Test the checkAttributes with invalid email
    """
    
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_email.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid email ignored")

  def testInvalidSponsor1(self):
    """
    Test the checkAttributes where the sponsor percentages 
    add up to more than 100
    """
    
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_sponsor1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid email ignored")

  def testInvalidSponsor2(self):
    """
    Test the checkAttributes where the sponsor percentages 
    add up to less than 100
    """
    
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_sponsor2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid email ignored")

  def testInvalidSponsor3(self):
    """
    Test the checkAttributes where the sponsor isn't on list 
    of allow VOs
    """
    
    
    config_file = get_test_config("siteattributes/" \
                                  "invalid_sponsor2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid email ignored")

  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = get_test_config("siteattributes/valid_settings.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = get_test_config("siteattributes/siteattributes3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = siteattributes.SiteAttributes(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")
if __name__ == '__main__':
  console = logging.StreamHandler()
  console.setLevel(logging.ERROR)
  global_logger.addHandler(console)
  unittest.main()
