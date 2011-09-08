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


from osg_configure.configure_modules import monalisa

global_logger = logging.getLogger('test monalisa configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestLocalSettings(unittest.TestCase):
  """
  Unit test class to test MonalisaConfiguration class
  """

  def testParsing1(self):
    """
    Test monalisa parsing
    """
    
    config_file = os.path.abspath("./configs/monalisa/monalisa1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_MONALISA_SERVICE'), 
                    'Attribute OSG_MONALISA_SERVICE missing')
    self.failUnlessEqual(attributes['OSG_MONALISA_SERVICE'], 'Y', 
                         'Wrong value obtained for OSG_MONALISA_SERVICE')
    
    self.failUnless(attributes.has_key('OSG_VO_MODULES'), 
                    'Attribute OSG_VO_MODULES missing')
    self.failUnlessEqual(attributes['OSG_VO_MODULES'], 'Y', 
                         'Wrong value obtained for OSG_VO_MODULES')
  
    self.failUnless(attributes.has_key('OSG_GANGLIA_SUPPORT'), 
                    'Attribute OSG_GANGLIA_SUPPORT missing')
    self.failUnlessEqual(attributes['OSG_GANGLIA_SUPPORT'], 'Y', 
                         'Wrong value obtained for OSG_GANGLIA_SUPPORT')
    
    self.failUnless(attributes.has_key('OSG_GANGLIA_HOST'), 
                    'Attribute  missing')
    self.failUnlessEqual(attributes['OSG_GANGLIA_HOST'], 'ganglia.host.org', 
                         'Wrong value obtained for OSG_GANGLIA_HOST')

    self.failUnless(attributes.has_key('OSG_GANGLIA_PORT'), 
                    'Attribute OSG_GANGLIA_PORT missing')
    self.failUnlessEqual(attributes['OSG_GANGLIA_PORT'], '1234', 
                         'Wrong value obtained for OSG_GANGLIA_PORT')

    self.failUnless(attributes.has_key('monitor_group'), 
                    'Attribute monitor_group missing')
    self.failUnlessEqual(attributes['monitor_group'], 'monalisa_group', 
                         'Wrong value obtained for monitor_group')

    self.failUnless(attributes.has_key('user'), 
                    'Attribute user missing')
    self.failUnlessEqual(attributes['user'], 'monalisa_user', 
                         'Wrong value obtained for monitor_group')

    self.failUnless(attributes.has_key('auto_update'), 
                    'Attribute auto_update missing')
    self.failUnlessEqual(attributes['auto_update'], 'Y', 
                         'Wrong value obtained for auto_update')

  def testParsing2(self):
    """
    Test monalisa parsing with negative values
    """
    
    config_file = os.path.abspath("./configs/monalisa/monalisa2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_MONALISA_SERVICE'), 
                    'Attribute OSG_MONALISA_SERVICE missing')
    self.failUnlessEqual(attributes['OSG_MONALISA_SERVICE'], 'Y', 
                         'Wrong value obtained for OSG_MONALISA_SERVICE')
    
    self.failUnless(attributes.has_key('OSG_VO_MODULES'), 
                    'Attribute OSG_VO_MODULES missing')
    self.failUnlessEqual(attributes['OSG_VO_MODULES'], 'N', 
                         'Wrong value obtained for OSG_VO_MODULES')
  
    self.failUnless(attributes.has_key('OSG_GANGLIA_SUPPORT'), 
                    'Attribute OSG_GANGLIA_SUPPORT missing')
    self.failUnlessEqual(attributes['OSG_GANGLIA_SUPPORT'], 'N', 
                         'Wrong value obtained for OSG_GANGLIA_SUPPORT')
    
    self.failUnless(attributes.has_key('auto_update'), 
                    'Attribute auto_update missing')
    self.failUnlessEqual(attributes['auto_update'], 'N', 
                         'Wrong value obtained for auto_update')

  def testParsingDisabled(self):
    """
    Test monalisa parsing when disabled
    """
    
    config_file = os.path.abspath("./configs/monalisa/monalisa_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_MONALISA_SERVICE'), 
                    'Attribute OSG_MONALISA_SERVICE missing')
    self.failUnlessEqual(attributes['OSG_MONALISA_SERVICE'], 'N', 
                         'Wrong value obtained for OSG_MONALISA_SERVICE')
    
  def testParsingIgnored(self):
    """
    Test monalisa parsing when set to ignore
    """
    
    config_file = os.path.abspath("./configs/monalisa/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_MONALISA_SERVICE'), 
                    'Attribute OSG_MONALISA_SERVICE missing')
    self.failUnlessEqual(attributes['OSG_MONALISA_SERVICE'], 'N', 
                         'Wrong value obtained for OSG_MONALISA_SERVICE')


  def testParsingDefaults(self):
    """
    Test monalisa parsing
    """
    
    config_file = os.path.abspath("./configs/monalisa/monalisa_defaults.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('OSG_MONALISA_SERVICE'), 
                    'Attribute OSG_MONALISA_SERVICE missing')
    self.failUnlessEqual(attributes['OSG_MONALISA_SERVICE'], 'Y', 
                         'Wrong value obtained for OSG_MONALISA_SERVICE')
    
    self.failUnless(attributes.has_key('OSG_VO_MODULES'), 
                    'Attribute OSG_VO_MODULES missing')
    self.failUnlessEqual(attributes['OSG_VO_MODULES'], 'Y', 
                         'Wrong value obtained for OSG_VO_MODULES')
  
    self.failUnless(attributes.has_key('OSG_GANGLIA_PORT'), 
                    'Attribute OSG_GANGLIA_PORT missing')
    self.failUnlessEqual(attributes['OSG_GANGLIA_PORT'], '8649', 
                         'Wrong value obtained for OSG_GANGLIA_PORT')

    self.failUnless(attributes.has_key('monitor_group'), 
                    'Attribute monitor_group missing')
    self.failUnlessEqual(attributes['monitor_group'], None, 
                         'Wrong value obtained for monitor_group')

    self.failUnless(attributes.has_key('user'), 
                    'Attribute user missing')
    self.failUnlessEqual(attributes['user'], 'daemon', 
                         'Wrong value obtained for monitor_group')

    self.failUnless(attributes.has_key('auto_update'), 
                    'Attribute auto_update missing')
    self.failUnlessEqual(attributes['auto_update'], 'N', 
                         'Wrong value obtained for auto_update')

  def testAttributeCheck(self):
    """
    Test the checkAttributes function
    """
        
    
    config_file = os.path.abspath("./configs/monalisa/bad_port.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Non-numeric ganglia port not flagged")    
                            
    config_file = os.path.abspath("./configs/monalisa/bad_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Invalid ganglia host not flagged")    

    config_file = os.path.abspath("./configs/monalisa/monalisa1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")

  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/monalisa/valid_settings.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")
    
    
if __name__ == '__main__':
    unittest.main()
