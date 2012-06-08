#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path 
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import rsv
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger('test_rsv configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

if os.path.exists('./configs/rsv/meta'):
  RSV_META_DIR = './configs/rsv/meta'
elif os.path.exists('/usr/share/osg-configure/tests/configs/rsv/meta'):
  RSV_META_DIR = '/usr/share/osg-configure/tests/configs/rsv/meta'
  
class TestRSV(unittest.TestCase):
  """
  Unit test class to test RsvConfiguration class
  """

  def testParsing1(self):
    """
    Test rsv parsing
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/rsv1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e) 

    options = settings.options
    variables = {'gratia_probes' : 'pbs,metric,condor', 
                 'ce_hosts' : 'my.host.com',
                 'gridftp_hosts' : 'my.host.com',
                 'gridftp_dir' : '/tmp',
                 'gums_hosts' : 'my.host.com',
                 'srm_hosts' : 'test.com:60443',
                 'srm_dir' : '/srm/dir',
                 'srm_webservice_path' : 'srm/v2/server',
                 'service_cert' : '/etc/redhat-release',
                 'service_key' : '/etc/redhat-release',
                 'service_proxy' : '/tmp/rsvproxy',
                 'enable_gratia' : True,
                 'enable_nagios' : True}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Option %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))
        
  def testParsing2(self):
    """
    Test rsv parsing
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/rsv2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e) 

    options = settings.options
    variables = {'gratia_probes' : '', 
                 'ce_hosts' : 'my.host.com, my2.host.com',
                 'gridftp_hosts' : 'my.host.com, my2.host.com',
                 'gridftp_dir' : '/tmp',
                 'gums_hosts' : 'my.host.com, my2.host.com',
                 'srm_hosts' : 'my.host.com, my2.host.com',
                 'srm_dir' : '/srm/dir, /srm/dir2',
                 'srm_webservice_path' : 'srm/v2/server,',
                 'service_cert' : '/etc/redhat-release',
                 'service_key' : '/etc/redhat-release',
                 'service_proxy' : '/tmp/rsvproxy',
                 'enable_gratia' : False,
                 'enable_nagios' : False}
    for var in variables:
      self.failUnless(options.has_key(var), 
                      "Option %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))

  def testMultipleHosts(self):
    """
    Test rsv parsing
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/multiple_hosts.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e) 

    options = settings.options
    variables = {'ce_hosts' : 'host1.site.com, host2.site.com',
                 'gridftp_hosts' : 'host3.site.com, host4.site.com',
                 'gridftp_dir' : '/tmp',
                 'gums_hosts' : 'host8.site.com, host9.site.com',
                 'srm_hosts' : 'host5.site.com, host6.site.com, host7.site.com:1234',
                 'srm_dir' : '/srm/dir',
                 'srm_webservice_path' : 'srm/v2/server',
                 'service_cert' : './configs/rsv/rsv1.ini',
                 'service_key' : './configs/rsv/rsv1.ini',
                 'service_proxy' : '/tmp/rsvproxy',
                 'enable_gratia' : True,
                 'enable_nagios' : True}
    for var in variables:
      self.failUnless(options.has_key(var), 
                      "Option %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))


    
  def testParsingIgnored(self):
    """
    Test parsing when ignored
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e) 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Ignored configuration should have no attributes")
    
  def testParsingDisabled(self):
    """
    Test parsing when disabled
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e) 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")
                                                            

  def testMissingAttribute(self):
    """
    Test the parsing when attributes are missing, should get exceptions
    """

    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/rsv2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)        

    mandatory = ['enable_gratia',
                 'enable_nagios']
    for option in mandatory:
      config_file = get_test_config("rsv/rsv1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('RSV', option)

      settings = rsv.RsvConfiguration(logger=global_logger)
      settings.rsv_meta_dir = RSV_META_DIR 
      self.failUnlessRaises(exceptions.SettingError, 
                            settings.parseConfiguration, 
                            configuration)

  def testInvalidKey(self):
    """
    Test the checkAttributes with invalid key file
    """
    
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "invalid_key.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)    

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid rsv key file ignored")
    
  def testMissingKey(self):
    """
    Test the checkAttributes with a missing rsv key file
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "missing_key.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)    

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Missing rsv key file ignored")
  
  def testInvalidCert(self):
    """
    Test the checkAttributes with invalid cert file
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "invalid_cert.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
          
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid rsv cert file ignored")

  def testMissingCert(self):
    """
    Test the checkAttributes with a missing rsv cert file
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "missing_cert.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
          
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Missing rsv cert file ignored")

  def testInvalidProxy(self):
    """
    Test the checkAttributes with invalid proxy file
    """
    
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "invalid_proxy.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
          
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid rsv proxy file ignored")

  def testMissingProxy(self):
    """
    Test the checkAttributes with a missing proxy cert file
    """
        
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "missing_proxy.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
          
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Missing rsv proxy file ignored")

  def testInvalidGratiaProbes(self):
    """
    Test the checkAttributes with invalid gratia probes
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "invalid_gratia1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid gratia probe ignored")

    config_file = get_test_config("rsv/" \
                                  "invalid_gratia2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid gratia probe list ignored")

  def testInvalidCEHost(self):
    """
    Test the checkAttributes with invalid ce host
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "invalid_ce_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid ce  ignored")
      
  def testInvalidGumsHost(self):
    """
    Test the checkAttributes with invalid gums host
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "invalid_gums_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid gums host ignored")

  def testInvalidGridftpHost(self):
    """
    Test the checkAttributes with invalid gridftp host
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "invalid_gridftp_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid gridftp ignored")

  def testInvalidSRMHost(self):
    """
    Test the checkAttributes with invalid srm host
    """
    
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/" \
                                  "invalid_srm_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid srm ignored")

  def testValidSettings1(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """

    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/rsv1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR 
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct configuration incorrectly flagged as incorrect")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """
    # need to have rsv installed to get rsv tests working
    if not utilities.rpm_installed('rsv-core'):
      return
    config_file = get_test_config("rsv/rsv2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    settings.rsv_meta_dir = RSV_META_DIR     
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct configuration incorrectly flagged as incorrect")

if __name__ == '__main__':
    unittest.main()
