#!/usr/bin/env python

import os, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.configure_modules import monalisa
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

class TestMonalisa(unittest.TestCase):
  """
  Unit test class to test MonalisaConfiguration class
  """

  def testParsing1(self):
    """
    Test monalisa parsing
    """
    
    config_file = get_test_config("monalisa/monalisa1.ini")
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

    self.failUnless(settings.options.has_key('monitor_group'), 
                    'Attribute monitor_group missing')
    self.failUnlessEqual(settings.options['monitor_group'].value, 
                         'monalisa_group', 
                         'Wrong value obtained for monitor_group')

    self.failUnless(settings.options.has_key('user'), 
                    'Attribute user missing')
    self.failUnlessEqual(settings.options['user'].value, 'monalisa_user', 
                         'Wrong value obtained for user')

    self.failUnless(settings.options.has_key('auto_update'), 
                    'Attribute auto_update missing')
    self.failUnlessEqual(settings.options['auto_update'].value, True, 
                         'Wrong value obtained for auto_update')


  def testParsing2(self):
    """
    Test monalisa parsing with negative values
    """
    
    config_file = get_test_config("monalisa/monalisa2.ini")
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
    
    self.failUnless(settings.options.has_key('auto_update'), 
                    'Attribute auto_update missing')
    self.failUnlessEqual(settings.options['auto_update'].value, False, 
                         'Wrong value obtained for auto_update')

  def testParsingDisabled(self):
    """
    Test monalisa parsing when disabled
    """
    
    config_file = get_test_config("monalisa/monalisa_disabled.ini")
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
    
    config_file = get_test_config("monalisa/ignored.ini")
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
    
    config_file = get_test_config("monalisa/monalisa_defaults.ini")
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
    
    self.failUnless(settings.options.has_key('monitor_group'), 
                    'Attribute monitor_group missing')
    self.failUnlessEqual(settings.options['monitor_group'].value, '', 
                         'Wrong value obtained for monitor_group')

    self.failUnless(settings.options.has_key('user'), 
                    'Attribute user missing')
    self.failUnlessEqual(settings.options['user'].value, 'daemon', 
                         'Wrong value obtained for user')

    self.failUnless(settings.options.has_key('auto_update'), 
                    'Attribute auto_update missing')
    self.failUnlessEqual(settings.options['auto_update'].value, False, 
                         'Wrong value obtained for auto_update')

  def testAttributeCheck(self):
    """
    Test the checkAttributes function
    """
        
    
    config_file = get_test_config("monalisa/bad_port.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = monalisa.MonalisaConfiguration(logger=global_logger)
    self.assertRaises(exceptions.SettingError,
                      settings.parseConfiguration,
                      configuration)
                            
    config_file = get_test_config("monalisa/bad_host.ini")
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

    config_file = get_test_config("monalisa/monalisa1.ini")
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
        
    config_file = get_test_config("monalisa/valid_settings.ini")
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
  console = logging.StreamHandler()
  console.setLevel(logging.ERROR)
  global_logger.addHandler(console)
  unittest.main()
