#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path if it's not there at present
try:
  from osg_configure.modules import utilities
except ImportError:
  pathname = '../'
  sys.path.append(pathname)
  from osg_configure.modules import utilities

from osg_configure.modules import exceptions


from osg_configure.configure_modules import gratia

global_logger = logging.getLogger('test gratia configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestLocalSettings(unittest.TestCase):
  """
  Unit test class to test GratiaConfiguration class
  """

  def testParsing1(self):
    """
    Test gratia parsing
    """
    
    config_file = os.path.abspath("./configs/gratia/gratia.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'probes' : 'jobmanager:gratia-osg-prod.opensciencegrid.org:80, '\
                            'metric:rsv.grid.iu.edu:8880, ' \
                            'gridftp:gratia-osg-transfer.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))

  def testParsingITBDefault(self):
    """
    Make sure gratia picks up the itb defaults 
    """
    
    config_file = os.path.abspath("./configs/gratia/itb_default.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'probes' : 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))
    
  def testParsingProductionDefault(self):
    """
    Make sure gratia picks up the itb defaults 
    """
    
    config_file = os.path.abspath("./configs/gratia/prod_default.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'probes' : 'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))

  def testParsingMissingITBDefault(self):
    """
    Make sure gratia picks up the itb defaults when the gratia
    section is missing 
    """
    
    config_file = os.path.abspath("./configs/gratia/itb_default2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'probes' : 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))
    
  def testParsingMissingProductionDefault(self):
    """
    Make sure gratia picks up the production defaults when the gratia 
    section is missing 
    """
    
    config_file = os.path.abspath("./configs/gratia/prod_default2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'probes' : 'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))

  def testParsingDisabled(self):
    """
    Test gratia parsing with negative values
    """
    
    config_file = os.path.abspath("./configs/gratia/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")

  def testParsingIgnored(self):
    """
    Test gratia parsing when section is ignored
    """
    
    config_file = os.path.abspath("./configs/gratia/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = gratia.GratiaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")

  def testInvalidProbes1(self):
    """
    Test the checkAttributes function to see if it catches invalid
    probes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/gratia/invalid_probe1.ini")
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
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/gratia/invalid_probe2.ini")
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
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gratia/check_ok.ini")
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
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gratia/disabled.ini")
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
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gratia/itb_default.ini")
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
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gratia/production_default.ini")
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
    
  def testMissingITBDefaults(self):
    """
    Test the ITB defaults and make sure that they are valid when the
    gratia section is missing
    """
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gratia/itb_default2.ini")
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
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gratia/production_default2.ini")
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

if __name__ == '__main__':
    unittest.main()
