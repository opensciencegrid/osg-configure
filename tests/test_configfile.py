#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, types

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.modules import configfile
from osg_configure.utilities import get_test_config

pathname = os.path.join('../scripts', 'osg-configure')

try:
    has_configure_osg = False
    fp = open(pathname, 'r')
    configure_osg = imp.load_module('test_module', fp, pathname, ('', '', 1))
    has_configure_osg = True
except:
    raise

class TestConfigFile(unittest.TestCase):

    def test_get_option(self):
      """
      Test functionality of get_option function
      """
      # check to see if exception is raised if option is not present
      config = ConfigParser.ConfigParser()
      section = 'Test'
      config.add_section(section)
      option = configfile.Option(name = 'foo')
      
      # do missing options get flagged
      self.failUnlessRaises(exceptions.SettingError, 
                            configfile.get_option,
                            config = config,
                            section = section,
                            option = option)
      option.required = configfile.Option.OPTIONAL
      
      # do optional settings get handled correctly if they are missing
      self.failUnlessEqual(None, 
                           configfile.get_option(config, 
                                                 section, 
                                                 option), 
                           'Raised exception for missing optional setting')
      
      option.default_value = 'test'
      option.value = ''
      # make sure defaults get used 
      configfile.get_option(config, section, option)
      self.failUnlessEqual('test', 
                           option.value,
                           "Default value not obtained, got %s, expected %s" %
                           (option.value, 'test'))
      # get integer option
      config.set(section, option.name, '1')
      option.type = int
      configfile.get_option(config, section, option)
      self.failUnlessEqual(1, 
                           option.value,
                           'Should have gotten an integer equal to 1 back ' +
                           "got %s" % option.value)
      
      # get float option
      option.type = float
      config.set(section, option.name, '1.23e5')
      configfile.get_option(config, section, option)
      self.failUnlessAlmostEqual(1.23e5, 
                                 option.value,
                                 7,
                                 'Should have gotten a float equal to 1.23e5 '+
                                 "back, got %s" % option.value)

      # check errors when wrong type specified
      option.type = int
      self.failUnlessRaises(exceptions.SettingError, 
                            configfile.get_option,
                            config = config,
                            section = section,
                            option = option)

      # get boolean option 
      option.type = bool
      config.set(section, option.name, 'False')
      configfile.get_option(config, section, option)
      self.failUnlessEqual(False, 
                           option.value,
                           'Should have gotten False back, got %s' % 
                           option.value)
      # check errors when wrong type specified
      option.type = int
      self.failUnlessRaises(exceptions.SettingError, 
                            configfile.get_option,
                            config = config,
                            section = section,
                            option = option)
      
      # check errors when wrong type specified
      option.type = bool
      config.set(section, option.name, 'abc')
      self.failUnlessRaises(exceptions.SettingError, 
                            configfile.get_option,
                            config = config,
                            section = section,
                            option = option)

      # check to make sure that default gets set when setting is set to 
      # blank/UNAVAILABLE
      option.type = str
      config.set(section, option.name, 'UNAVAILABLE')
      configfile.get_option(config, section, option)
      self.failUnlessEqual('test', 
                           option.value,
                           "Should have gotten a value of test back, got %s" %
                           option.value)

    def test_get_option_location(self):
      """
      Test the get option location method in configfile module
      """
      config_directory = './configs/config-test1.d'
      location = './configs/config-test1.d/00-test.ini'
      opt_location = configfile.get_option_location('first_opt', 
                                                    'Common',
                                                    config_directory = config_directory)
      self.failUnlessEqual(location,
                           opt_location,
                           "Didn't get the correct location for first_opt:" +
                           "got %s expected %s" % (opt_location, location))
      
      location = './configs/config-test1.d/10-test.ini'
      opt_location = configfile.get_option_location('second_opt', 
                                                    'Common',
                                                    config_directory = config_directory)
      self.failUnlessEqual(location,
                           opt_location,
                           "Didn't get the correct location for second_opt:" +
                           "got %s expected %s" % (opt_location, location))

      location = None
      opt_location = configfile.get_option_location('missing_opt', 
                                                    'Common',
                                                    config_directory = config_directory)
      self.failUnlessEqual(location,
                           opt_location,
                           "Didn't get the correct location for missing_opt:" +
                           "got %s expected None" % (opt_location))

    def test_get_file_list(self):
      """
      Test the list of files that the module things it's reading and the order
      that the files are read in
      """
      config_directory = './configs/config-test1.d'
      file_order = ['./configs/config-test1.d/00-test.ini',
                    './configs/config-test1.d/10-test.ini',
                    './configs/config-test1.d/A-test.ini',
                    './configs/config-test1.d/atest.ini']
      file_list = configfile.get_file_list(config_directory = config_directory) 
      self.failUnlessEqual(file_order,
                           file_list, 
                           "Didn't get the files in the correct order: " +
                           " %s\n instead of\n %s" % (file_list, file_order))
      
      config_directory = './configs/config-test2.d'
      file_order = ['./configs/config-test2.d/00-test.ini',
                    './configs/config-test2.d/10-test.ini',
                    './configs/config-test2.d/A-test.ini',
                    './configs/config-test2.d/atest.ini']
      file_list = configfile.get_file_list(config_directory = config_directory) 
      self.failUnlessEqual(file_order,
                           file_list, 
                           "Didn't get the files in the correct order: " +
                           " %s\n instead of\n %s" % (file_list, file_order))

    def test_jobmanager_enabled(self):
      """
      Test configurations to make sure that they are properly understood as being for a CE
      """
      
      config_dirs = ['./configs/config-ce-pbs.d', 
                     './configs/config-ce-condor.d',
                     './configs/config-ce-lsf.d',
                     './configs/config-ce-sge.d']
      for dir in config_dirs:
        config = configfile.read_config_files(config_directory = dir)
        self.failUnless(configfile.jobmanager_enabled(config), 
                        "%s has an enabled jobmanager" % dir)

      config = configfile.read_config_files(config_directory = './configs/config-nonce.d')
      self.failIf(configfile.jobmanager_enabled(config), 
                  "jobmanager_enabled returned true on a config without an enabled jobmanager")
          
if __name__ == '__main__':
    unittest.main()

