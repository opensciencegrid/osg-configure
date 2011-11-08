#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging


# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.configure_modules import bestman

global_logger = logging.getLogger('test bestman configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestBestman(unittest.TestCase):
  """
  Unit test class to test BestmanConfiguration class
  """

  def testParsing1(self):
    """
    Test bestman parsing
    """
    
    config_file = os.path.abspath("./configs/bestman/bestman1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'certificate_file' : './configs/bestman/bestman1.ini',
                 'key_file' : './configs/bestman/bestman1.ini',
                 'http_port' : 8080,
                 'https_port' : 8443,
                 'mode' : 'xrootd',
                 'token_list' : 
                   'ATLASDATADISK[desc:ATLASDATADISK][40000];ATLASPRODDISK[desc:ATLASPRODDISK][30000];',                 
                 'transfer_servers' : 'gsiftp://host1.example.com,gsiftp://host2.example.com:2312'}
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
    Test bestman parsing with negative values
    """
    
    config_file = os.path.abspath("./configs/bestman/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 1, 
                         "Disabled configuration should have no attributes")
    

  def testParsingDefaults(self):
    """
    Test bestman defaults
    """
    
    config_file = os.path.abspath("./configs/bestman/defaults.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    attributes = settings.attributes
    variables = {'http_port' : '8080',
                 'https_port' : '8443'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))

    
  def testInvalidTokens1(self):
    """
    Test the checkAttributes function to see if it catches invalid
    space tokens
    """
        

    config_file = os.path.abspath("./configs/bestman/invalid_tokens1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid tokens")
    
  def testInvalidTokens2(self):
    """
    Test the checkAttributes function to see if it catches invalid
    space tokens
    """
        

    config_file = os.path.abspath("./configs/bestman/invalid_tokens2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid tokens")

  def testInvalidServers1(self):
    """
    Test the checkAttributes function to see if it catches invalid
    transfer servers
    """
        

    config_file = os.path.abspath("./configs/bestman/invalid_transfer1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid transfer servers")

  def testInvalidMode(self):
    """
    Test the checkAttributes function to see if it catches invalid
    bestman modes
    """
        

    config_file = os.path.abspath("./configs/bestman/invalid_mode.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid mode")

  def testKeyCheck(self):
    """
    Test the checkAttributes function to see if it catches problems with
    the key file
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_key.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid key file")

    config_file = os.path.abspath("./configs/bestman/missing_key.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing key file")

  def testCertificateCheck(self):
    """
    Test the checkAttributes function to see if it catches problems with
    the certificate file
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_cert.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid cert file")

    config_file = os.path.abspath("./configs/bestman/missing_cert.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing cert file")

  def testInvalidHttpPort1(self):
    """
    Test the checkAttributes function to see if it catches invalid
    http ports
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_http_port1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid http port")
                            
  def testInvalidHttpPort2(self):
    """
    Test the checkAttributes function to see if it catches invalid
    http ports
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_http_port2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    self.failUnlessRaises(exceptions.SettingError, 
                          settings.parseConfiguration, 
                          configuration = configuration) 
 
 
  def testInvalidHttpsPort1(self):
    """
    Test the checkAttributes function to see if it catches invalid
    http ports
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_https_port1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    self.failUnlessRaises(exceptions.SettingError, 
                          settings.parseConfiguration, 
                          configuration = configuration) 
                            
  def testInvalidHttpsPort2(self):
    """
    Test the checkAttributes function to see if it catches invalid
    http ports
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_https_port2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid https port")

  def testInvalidAllowedPaths(self):
    """
    Test the checkAttributes function to see if it catches invalid
    allowed paths
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_allowed_paths.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid allowed paths specifications")
    
  def testInvalidCacheSize(self):
    """
    Test the checkAttributes function to see if it catches invalid
    cache size
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_cache_size1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    self.failUnlessRaises(exceptions.SettingError, 
                          settings.parseConfiguration, 
                          configuration = configuration) 
 
    config_file = os.path.abspath("./configs/bestman/invalid_cache_size2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid cache size")

  def testInvalidVolatileLifetime(self):
    """
    Test the checkAttributes function to see if it catches invalid
    volatile lifetimes
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_volatile_lifetime1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    self.failUnlessRaises(exceptions.SettingError, 
                          settings.parseConfiguration, 
                          configuration = configuration) 
 
    config_file = os.path.abspath("./configs/bestman/invalid_volatile_lifetime2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid volatile lifetime")

  def testInvalidCustodialSize(self):
    """
    Test the checkAttributes function to see if it catches invalid
    custodial size
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_custodial_size1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    self.failUnlessRaises(exceptions.SettingError, 
                          settings.parseConfiguration, 
                          configuration = configuration) 
 
    config_file = os.path.abspath("./configs/bestman/invalid_custodial_size2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid custodial size")
    
  def testInvalidCustodialPath(self):
    """
    Test the checkAttributes function to see if it catches invalid
    custodial path
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_custodial_path1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid custodial size")

  def testInvalidBlockedPaths(self):
    """
    Test the checkAttributes function to see if it catches invalid
    blocked paths
    """
        
    config_file = os.path.abspath("./configs/bestman/invalid_blocked_paths.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid blocked paths specifications")
    

  def testValidSettings1(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = os.path.abspath("./configs/bestman/check_ok1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings considered to be invalid")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = os.path.abspath("./configs/bestman/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings considered to be invalid")

  def testDiabledValid(self):
    """
    Test the checkAttributes function to see if it oks a disabled section
    """
        
    config_file = os.path.abspath("./configs/bestman/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Disabled section considerd to be invalid")
    
  def testValidSettings3(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = os.path.abspath("./configs/bestman/check_ok3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings considered to be invalid")

  def testValidSettings4(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    config_file = os.path.abspath("./configs/bestman/check_ok4.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = bestman.BestmanConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings considered to be invalid")

    
if __name__ == '__main__':
    unittest.main()
