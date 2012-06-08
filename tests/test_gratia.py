#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path 
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import gratia
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger('test gratia configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestGratia(unittest.TestCase):
  """
  Unit test class to test GratiaConfiguration class
  """

  def testParsing1(self):
    """
    Test gratia parsing
    """
    
    config_file = get_test_config("gratia/gratia.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'probes' : 'jobmanager:gratia-osg-prod.opensciencegrid.org:80, '\
                            'metric:rsv.grid.iu.edu:8880, ' \
                            'gridftp:gratia-osg-transfer.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))

  def testParsingITBDefault(self):
    """
    Make sure gratia picks up the itb defaults 
    """
    
    # need to be on a CE to get CE defaults
    if not utilities.ce_installed():
      return

    config_file = get_test_config("gratia/itb_default.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'probes' : 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))

    
  def testParsingProductionDefault(self):
    """
    Make sure gratia picks up the itb defaults 
    """
    
    # need to be on a CE to get CE defaults
    if not utilities.ce_installed():
      return

    config_file = get_test_config("gratia/prod_default.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'probes' : 'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))

  def testParsingMissingITBDefault(self):
    """
    Make sure gratia picks up the itb defaults when the gratia
    section is missing 
    """
    
    # need to be on a CE to get CE defaults
    if not utilities.ce_installed():
      return
    config_file = get_test_config("gratia/itb_default2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'probes' : 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))

    config_file = get_test_config("gratia/itb_default3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'probes' : 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))
    
  def testParsingMissingProductionDefault(self):
    """
    Make sure gratia picks up the production defaults when the gratia 
    section is missing 
    """
    
    # need to be on a CE to get CE defaults
    if not utilities.ce_installed():
      return
    config_file = get_test_config("gratia/prod_default2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'probes' : 'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))

  def testParsingDisabled(self):
    """
    Test gratia parsing with negative values
    """
    
    config_file = get_test_config("gratia/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.failUnlessEqual(len(settings.options['probes'].value), 0, 
                         "Disabled configuration should have no attributes")

  def testParsingIgnored(self):
    """
    Test gratia parsing when section is ignored
    """
    
    config_file = get_test_config("gratia/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.failUnlessEqual(len(settings.options['probes'].value), 0, 
                         "Disabled configuration should have no attributes")

  def testInvalidProbes1(self):
    """
    Test the checkAttributes function to see if it catches invalid
    probes
    """
        
    config_file = get_test_config("gratia/invalid_probe1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid probe specification")

  def testInvalidProbes2(self):
    """
    Test the checkAttributes function to see if it catches invalid
    probes
    """
        
    config_file = get_test_config("gratia/invalid_probe2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid probe specification")

  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = get_test_config("gratia/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")
    
  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it oks a disabled section
    """
        
    config_file = get_test_config("gratia/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Disabled section incorrectly flagged as invalid")
    
  def testValidITBDefaults(self):
    """
    Test the ITB defaults and make sure that they are valid
    """
    config_file = get_test_config("gratia/itb_default.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "ITB defaults flagged as invalid")

  def testValidProductionDefaults(self):
    """
    Test the production defaults and make sure that they are valid
    """
    config_file = get_test_config("gratia/prod_default.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Production defaults flagged as invalid")
    
  def testMissingITBDefaults(self):
    """
    Test the ITB defaults and make sure that they are valid when the
    gratia section is missing
    """
    config_file = get_test_config("gratia/itb_default2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "ITB defaults flagged as invalid")

  def testMissingProductionDefaults(self):
    """
    Test the production defaults and make sure that they are valid when the 
    gratia section is missing
    """
    config_file = get_test_config("gratia/prod_default2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Production defaults flagged as invalid")

if __name__ == '__main__':
    unittest.main()
