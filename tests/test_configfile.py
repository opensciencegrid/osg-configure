#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, types

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.modules import configfile

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
      option = 'foo'
      
      # do missing options get flagged
      self.failUnlessRaises(exceptions.SettingError, 
                            configfile.get_option,
                            config = config,
                            section = section,
                            option = 'missing')
      optional_settings = [option]
      
      # do optional settings get handled correctly if they are missing
      self.failUnlessEqual(None, 
                           configfile.get_option(config, 
                                                 section, 
                                                 option, 
                                                 optional_settings), 
                           'Raised exception for missing optional setting')
      defaults = { option : 'test'}
      # make sure defaults get used 
      self.failUnlessEqual('test', 
                           configfile.get_option(config, 
                                                 section, 
                                                 option, 
                                                 optional_settings,
                                                 defaults), 
                           'Raised exception for missing optional setting')
      # get integer option
      config.set(section, option, '1')
      self.failUnlessEqual(1, 
                           configfile.get_option(config, 
                                                 section, 
                                                 option, 
                                                 optional_settings,
                                                 defaults,
                                                 types.IntType), 
                           'Should have gotten an integer equal to 1 back')
      
      # get float option
      config.set(section, option, '1.23e5')
      self.failUnlessAlmostEqual(1.23e5, 
                                 configfile.get_option(config, 
                                                       section, 
                                                       option, 
                                                       optional_settings,
                                                       defaults,
                                                       types.FloatType),
                                 7,
                                 'Should have gotten a float equal to 1.23e5 back')

      # check errors when wrong type specified
      self.failUnlessRaises(exceptions.SettingError, 
                            configfile.get_option,
                            config = config,
                            section = section,
                            option = option,
                            defaults = defaults,
                            option_type = types.IntType)

      # get boolean option 
      config.set(section, option, 'False')
      self.failUnlessEqual(False, 
                           configfile.get_option(config, 
                                                 section, 
                                                 option, 
                                                 optional_settings,
                                                 defaults,
                                                 types.BooleanType), 
                           'Should have gotten False back')
      # check errors when wrong type specified
      self.failUnlessRaises(exceptions.SettingError, 
                            configfile.get_option,
                            config = config,
                            section = section,
                            option = option,
                            defaults = defaults,
                            option_type = types.IntType)
      
      # check errors when wrong type specified
      config.set(section, option, 'abc')
      self.failUnlessRaises(exceptions.SettingError, 
                            configfile.get_option,
                            config = config,
                            section = section,
                            option = option,
                            defaults = defaults,
                            option_type = types.BooleanType)

      # check to make sure that default gets set when setting is set to 
      # blank/UNAVAILABLE
      config.set(section, option, 'UNAVAILABLE')
      self.failUnlessEqual('test', 
                           configfile.get_option(config, 
                                                 section, 
                                                 option, 
                                                 optional_settings,
                                                 defaults), 
                           'Should have gotten a value of test back')

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

