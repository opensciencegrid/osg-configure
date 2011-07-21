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

from configure_osg.configure_modules import monalisa

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

  def testAttributeGeneration1(self):
    """
    Test the creation of a config file given attributes
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
    new_config = ConfigParser.SafeConfigParser()
    settings.generateConfigFile(attributes.items(), new_config)
    section_name = 'MonaLisa'
    self.failUnless(new_config.has_section(section_name), 
                    "%s section not created in config file" % section_name)
    
    options = {'enabled' : 'True',
               'use_vo_modules' : 'True',
               'ganglia_support' : 'True',
               'ganglia_host' : 'ganglia.host.org',
               'ganglia_port' : '1234',
               'monitor_group' : 'monalisa_group',
               'auto_update' : 'True',
               'user' : 'monalisa_user' }
    for option in options:      
      self.failUnless(new_config.has_option(section_name, option), 
                      "Option %s missing" % option)
      self.failUnlessEqual(new_config.get(section_name, option), 
                           options[option], 
                           "Wrong value obtained for %s, expected %s, got %s" %
                           (option,
                            options[option],
                            new_config.get(section_name, option)))
                            
    
  def testAttributeGeneration2(self):
    """
    Test the creation of a config file given attributes
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
    new_config = ConfigParser.SafeConfigParser()
    settings.generateConfigFile(attributes.items(), new_config)
    section_name = 'MonaLisa'
    self.failUnless(new_config.has_section(section_name), 
                    "%s section not created in config file" % section_name)
    
    options = {'enabled' : 'True',
               'use_vo_modules' : 'False',
               'ganglia_support' : 'False',
               'ganglia_host' : 'ganglia.host.org',
               'ganglia_port' : '1234',
               'monitor_group' : 'monalisa_group',
               'auto_update' : 'False',
               'user' : 'monalisa_user' }
    for option in options:      
      self.failUnless(new_config.has_option(section_name, option), 
                      "Option %s missing" % option)
      self.failUnlessEqual(new_config.get(section_name, option), 
                           options[option], 
                           "Wrong value obtained for %s, expected %s, got %s" %
                           (option,
                            options[option],
                            new_config.get(section_name, option)))
                            
  def testAttributeGeneration3(self):
    """
    Test the creation of a config file given attributes
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
    new_config = ConfigParser.SafeConfigParser()
    settings.generateConfigFile(attributes.items(), new_config)
    section_name = 'MonaLisa'
    self.failUnless(new_config.has_section(section_name), 
                    "%s section not created in config file" % section_name)
    
    options = {'enabled' : 'False'}
    for option in options:      
      self.failUnless(new_config.has_option(section_name, option), 
                      "Option %s missing" % option)
      self.failUnlessEqual(new_config.get(section_name, option), 
                           options[option], 
                           "Wrong value obtained for %s, expected %s, got %s" %
                           (option,
                            options[option],
                            new_config.get(section_name, option)))
                            

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
