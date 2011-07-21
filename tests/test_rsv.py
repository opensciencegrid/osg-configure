#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
if "CONFIGURE_OSG_LOCATION" in os.environ:
    pathname = os.path.join(os.environ['CONFIGURE_OSG_LOCATION'], 'bin')
else:
    if "VDT_LOCATION" in os.environ:
        pathname = os.path.join(os.environ['VDT_LOCATION'], 'osg', 'bin')
        if not os.path.exists(os.path.join(pathname, 'configure-osg')):
          pathname = '../lib/python/'
    else:
      pathname = '../lib/python/'
          
sys.path.append(pathname)


from configure_osg.modules import exceptions
from configure_osg.modules import utilities

from configure_osg.configure_modules import rsv


global_logger = logging.getLogger('test_rsv configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)



class TestRSVSettings(unittest.TestCase):
  """
  Unit test class to test RsvConfiguration class
  """

  def testParsing1(self):
    """
    Test rsv parsing
    """
    
    config_file = os.path.abspath("./configs/rsv/rsv1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e) 

    attributes = settings.attributes
    variables = {'rsv_user' : 'daemon',
                 'gratia_probes' : 'pbs,metric,managedfork', 
                 'enable_ce_probes' : True,
                 'ce_hosts' : 'my.host.com',
                 'enable_gridftp_probes' : True,
                 'gridftp_hosts' : 'my.host.com',
                 'gridftp_dir' : '/tmp',
                 'enable_gums_probes' : True,
                 'gums_hosts' : 'my.host.com',
                 'enable_srm_probes' : True,
                 'srm_hosts' : 'my.host.com:60443',
                 'srm_dir' : '/srm/dir',
                 'srm_webservice_path' : 'srm/v2/server',
                 'use_service_cert' : True,
                 'rsv_cert_file' : './configs/rsv/rsv1.ini',
                 'rsv_cert_key' : './configs/rsv/rsv1.ini',
                 'rsv_proxy_out_file' : '/tmp/rsvproxy.tmp',
                 'proxy_file' : 'UNAVAILABLE',
                 'enable_gratia' : True,
                 'setup_rsv_nagios' : True,
                 'rsv_nagios_conf_file' : './configs/rsv/rsv1.ini',
                 'setup_for_apache' : True}
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
    Test rsv parsing
    """
    
    config_file = os.path.abspath("./configs/rsv/rsv2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e) 

    attributes = settings.attributes
    variables = {'rsv_user' : 'daemon',
                 'gratia_probes' : None, 
                 'enable_ce_probes' : False,
                 'ce_hosts' : 'my.host.com, my2.host.com',
                 'enable_gridftp_probes' : False,
                 'gridftp_hosts' : 'my.host.com, my2.host.com',
                 'gridftp_dir' : '/tmp',
                 'enable_gums_probes' : False,
                 'gums_hosts' : 'my.host.com, my2.host.com',
                 'enable_srm_probes' : False,
                 'srm_hosts' : 'my.host.com, my2.host.com',
                 'srm_dir' : '/srm/dir',
                 'srm_webservice_path' : 'srm/v2/server',
                 'use_service_cert' : False,
                 'rsv_cert_file' : './configs/rsv/rsv1.ini',
                 'rsv_cert_key' : './configs/rsv/rsv1.ini',
                 'rsv_proxy_out_file' : '/tmp/rsvproxy.tmp',
                 'proxy_file' : './configs/rsv/rsv2.ini',
                 'enable_gratia' : False,
                 'setup_rsv_nagios' : False,
                 'rsv_nagios_conf_file' : './configs/rsv/rsv1.ini',
                 'setup_for_apache' : False}
    for var in variables:
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))

  def testMultipleHosts(self):
    """
    Test rsv parsing
    """
    
    config_file = os.path.abspath("./configs/rsv/multiple_hosts.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e) 

    attributes = settings.attributes
    variables = {'rsv_user' : 'daemon',
                 'enable_ce_probes' : True,
                 'ce_hosts' : 'host1.site.com, host2.site.com',
                 'enable_gridftp_probes' : True,
                 'gridftp_hosts' : 'host3.site.com, host4.site.com',
                 'gridftp_dir' : '/tmp',
                 'enable_gums_probes' : True,
                 'gums_hosts' : 'host8.site.com, host9.site.com',
                 'enable_srm_probes' : True,
                 'srm_hosts' : 'host5.site.com, host6.site.com, host7.site.com:1234',
                 'srm_dir' : '/srm/dir',
                 'srm_webservice_path' : 'srm/v2/server',
                 'use_service_cert' : True,
                 'rsv_cert_file' : './configs/rsv/rsv1.ini',
                 'rsv_cert_key' : './configs/rsv/rsv1.ini',
                 'rsv_proxy_out_file' : '/tmp/rsvproxy.tmp',
                 'proxy_file' : 'UNAVAILABLE',
                 'enable_gratia' : True,
                 'setup_rsv_nagios' : True,
                 'rsv_nagios_conf_file' : './configs/rsv/rsv1.ini',
                 'setup_for_apache' : True}
    for var in variables:
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))


    
  def testParsingIgnored(self):
    """
    Test parsing when ignored
    """
    
    config_file = os.path.abspath("./configs/rsv/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    config_file = os.path.abspath("./configs/rsv/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = rsv.RsvConfiguration(logger=global_logger)
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

    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/rsv2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)        

    os.environ['VDT_LOCATION'] = os.getcwd()
    mandatory = ['use_service_cert',
                 'enable_gratia',
                 'enable_ce_probes',
                 'enable_gridftp_probes',
                 'enable_gums_probes',
                 'enable_srm_probes',
                 'setup_rsv_nagios']
    for option in mandatory:
      config_file = os.path.abspath("./configs/rsv/rsv1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('RSV', option)

      settings = rsv.RsvConfiguration(logger=global_logger)
      self.failUnlessRaises(exceptions.SettingError, 
                            settings.parseConfiguration, 
                            configuration)

  def testInvalidKey(self):
    """
    Test the checkAttributes with invalid key file
    """
    
    
    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_key.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    os.environ['VDT_LOCATION'] = '/opt/osg'    
    config_file = os.path.abspath("./configs/rsv/" \
                                  "missing_key.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    os.environ['VDT_LOCATION'] = '/opt/osg'    
    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_cert.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/" \
                                  "missing_cert.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    
    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_proxy.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
        
    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/" \
                                  "missing_proxy.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_gratia1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes),
                "Invalid gratia probe ignored")

    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_gratia2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_ce_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_gums_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_gridftp_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    
    os.environ['VDT_LOCATION'] = '/opt/osg'
    config_file = os.path.abspath("./configs/rsv/" \
                                  "invalid_srm_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)
  
    settings = rsv.RsvConfiguration(logger=global_logger)
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
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/rsv/rsv1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
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
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/rsv/rsv2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = rsv.RsvConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct configuration incorrectly flagged as missing")

if __name__ == '__main__':
    unittest.main()
