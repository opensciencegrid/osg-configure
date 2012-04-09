#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import misc
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger('test misc configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestLocalSettings(unittest.TestCase):
  """
  Unit test class to test MiscConfiguration class
  """

  def testParsing1(self):
    """
    Test misc parsing
    """
    
    config_file = get_test_config("misc/misc1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'glexec_location' : './configs/misc',
                 'gums_host' : 'my.gums.org',
                 'authorization_method' : 'xacml'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Option %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))
    attributes = settings.getAttributes()
    variables = {'OSG_GLEXEC_LOCATION' : './configs/misc'}
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
    Test misc parsing with negative values
    """
    
    config_file = get_test_config("misc/misc2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'glexec_location' : './configs/misc',
                 'gums_host' : 'my.gums.org',
                 'authorization_method' : 'xacml'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Option %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))
    attributes = settings.getAttributes()
    variables = {'OSG_GLEXEC_LOCATION' : './configs/misc'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var,                                             
                                            attributes[var],
                                            variables[var]))
    

  def testParsingAuthentication(self):
    """
    Test misc parsing with negative values
    """
    
    config_file = get_test_config("misc/misc_xacml.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.failUnless(settings.options.has_key('authorization_method'), 
                    "Attribute authorization_method missing")
    self.failUnlessEqual(settings.options['authorization_method'].value, 
                         'xacml', 
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',                                             
                                          settings.options['authorization_method'].value,
                                          'xacml'))

    config_file = get_test_config("misc/misc_gridmap.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.failUnless(settings.options.has_key('authorization_method'), 
                    "Attribute authorization_method missing")
    self.failUnlessEqual(settings.options['authorization_method'].value, 
                         'gridmap', 
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',                                             
                                          settings.options['authorization_method'].value,
                                          'gridmap'))

    config_file = get_test_config("misc/misc_local_gridmap.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.failUnless(settings.options.has_key('authorization_method'), 
                    "Attribute authorization_method missing")
    self.failUnlessEqual(settings.options['authorization_method'].value, 
                         'local-gridmap', 
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',                                             
                                          settings.options['authorization_method'].value,
                                          'local-gridmap'))

  def testMissingAttribute(self):
    """
    Test the parsing when attributes are missing, should get exceptions
    """
        
    mandatory = ['gums_host']
    for option in mandatory:
      config_file = get_test_config("misc/misc1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('Misc Services', option)

      settings = misc.MiscConfiguration(logger=global_logger)
      settings.parseConfiguration(configuration)
      self.failUnless(not settings.checkAttributes({})) 

  def testXacmlMissingGums(self):
    """
    Test the checkAttributes function when xacml is specified but the
    gums host isn't 
    """
        

    config_file = get_test_config("misc/misc_xacml_missing_gums.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    settings.parseConfiguration(configuration)
    self.failUnless(exceptions.ConfigureError,
                    settings.checkAttributes({}))
    
  def testXacmlBadGums(self):
    """
    Test the checkAttributes function when xacml is specified but the
    gums host isn't valid
    """
        

    config_file = get_test_config("misc/misc_xacml_bad_gums.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice bad gums host")

  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = get_test_config("misc/valid_settings.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
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
        
    config_file = get_test_config("misc/valid_settings2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as invalid")

  def testInvalidSettings(self):
    """
    Test the checkAttributes function to see if it flags bad attributes
    """
        
    config_file = get_test_config("misc/invalid_settings1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = misc.MiscConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Bad config incorrectly flagged as okay")    
if __name__ == '__main__':
    unittest.main()
