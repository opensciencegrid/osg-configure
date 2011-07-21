#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, types

# setup system library path
if "CONFIGURE_OSG_LOCATION" in os.environ:
    pathname = os.path.join(os.environ['CONFIGURE_OSG_LOCATION'], 'bin')
else:
    if "VDT_LOCATION" in os.environ:
        pathname = os.path.join(os.environ['VDT_LOCATION'], 'osg', 'bin')
        if not os.path.exists(os.path.join(pathname, 'configure-osg')):
          pathname = '../lib/python'
    else:
      pathname = '../lib/python'
          
sys.path.append(pathname)

pathname = os.path.join('../bin', 'configure-osg')

try:
    has_configure_osg = False
    fp = open(pathname, 'r')
    configure_osg = imp.load_module('test_module', fp, pathname, ('', '', 1))
    has_configure_osg = True
except:
    raise

from configure_osg.modules import exceptions
from configure_osg.modules import utilities

class TestUtilities(unittest.TestCase):

    def test_valid_domain(self):
      """
      Check the valid_domain functionality
      """
      test_domain = "testing"
      self.failIf(utilities.valid_domain(test_domain),
                  "testing marked as a valid domain address")
      
      test_domain = "34c93F.39f@~#"
      self.failIf(utilities.valid_domain(test_domain),
                  "testing marked as a valid domain address")

      test_domain = "t-ea.34.org"
      self.failUnless(utilities.valid_domain(test_domain), 
                      "t-ea.34.org marked as an invalid domain address")
        
      test_domain = "uchicago.edu"
      self.failUnless(utilities.valid_domain(test_domain, resolve = True),
                      "uchicago.edu marked as an invalid domain address")

      
      test_domain = "invalid.invalid"
      self.failIf(utilities.valid_domain(test_domain, resolve = True),
                  "invalid.invalid marked as an valid domain address")

    def test_valid_email(self):
      """
      Check the valid email functionality
      """
      failed = False
      test_email = "fake@email@testing"
      self.failIf(utilities.valid_email(test_email),
                  "fake@email@testing marked as a valid email address")
      
      test_email = "a.3a-3bc@t-ea.34.org"
      self.failUnless(utilities.valid_email(test_email),
                      "a.3a-3bc@t-ea.34.org marked as an invalid email " \
                      "address")
      

    def test_valid_location(self):
      """
      Check the valid_location functionality
      """

      test_location = os.path.abspath("./configs")
      self.failUnless(utilities.valid_location(test_location), 
                      "%s not marked as a valid location" % test_location)

      
      test_location = "configs/invalid_foo.config"
      self.failIf(utilities.valid_location(test_location), 
                  "%s marked as a valid location" % test_location)      

    def test_valid_file_location(self):
      """
      Check the valid_file functionality
      """
      test_file = "configs/utilities/valid_boolean.ini"
      message = "%s not marked as a valid file location" % test_file
      self.failUnless(utilities.valid_location(test_file), message)
      
      test_file = "configs/invalid_foo.config"
      message = "%s marked as a valid file location" % test_file
      self.failIf(utilities.valid_location(test_file),
                  message)
      

    def test_valid_user(self):
      """
      Check the valid_user functionality
      """

      self.failUnless(utilities.valid_user('root'),
                      "root not marked as a valid user")
      
      self.failIf(utilities.valid_user('hacked'), 
                  "'hacked' is considered a valid user")
      

    def test_get_gums_host(self):
      """
      Check the functionality of get_gums_host
      """
      
      failed = False
      message = None
      gums_host = 'gums-host.test.com'

      os.environ['VDT_GUMS_HOST'] = gums_host
      self.failUnlessEqual(utilities.get_gums_host(), 
                           (gums_host, 8443), 
                           "Gums host not found from environment")
      del os.environ['VDT_GUMS_HOST']
        

    def test_vdt_location(self):
      """
      Check to see if get_vdt_location works
      """

      vdt_location = os.path.abspath('.')

      os.environ['VDT_LOCATION'] = vdt_location
      self.failUnlessEqual(utilities.get_vdt_location(), 
                           vdt_location, 
                           "VDT_LOCATION not found from environment")        
      del os.environ['VDT_LOCATION']

      self.failUnlessRaises(exceptions.ApplicationError, utilities.get_vdt_location)

      
    def test_get_elements(self):
      """
      Check to make sure that get_elements properly gets information 
      from xml files
      """
      
      xml_file = 'test_files/subscriptions.xml'
      self.failUnlessEqual(utilities.get_elements('foo', xml_file), 
                           [], 
                           'Got invalid elements')
      subscriptions = utilities.get_elements('subscription', xml_file)
      self.failUnlessEqual(len(subscriptions), 
                           2, 
                           'Got wrong number of elements')
      tag_names = [x.tagName for x in subscriptions]
      self.failUnlessEqual(['subscription', 'subscription'], 
                           tag_names, 
                           'Got wrong elements')
      
    def test_write_attribute_file(self):
      """
      Check to make sure that write_attribute_file writes out files properly
      """
      attribute_file = os.path.abspath("./test_files/temp_attributes.conf")
      attribute_standard = os.path.abspath("./test_files/attributes_output.conf")
      try:
        attributes = {'Foo' : 123,
                      'test_attr' : 'abc-234#$',
                      'my-Attribute' : 'test_attribute'}
        utilities.write_attribute_file(attribute_file, attributes)
        self.failUnlessEqual(open(attribute_file).read(), 
                             open(attribute_standard).read(), 
                             'Attribute files are not equal')
        if os.path.exists(attribute_file):
          os.unlink(attribute_file)
      except Exception, ex:
        print ex
        self.fail('Got exception while testing wite_attribute_file' \
                  "functionality:\n%s" % ex)
        if os.path.exists(attribute_file):
          os.unlink(attribute_file)
      
    def test_get_set_membership(self):
      """
      Test get_set_membership functionality
      """
      
      test_set1 = [1, 2, 3, 4, 5, 6, 7]
      reference_set1 = [1, 2, 3, 4, 5]
      default_set1 = [5, 6, 7]
      
      self.failUnlessEqual(utilities.get_set_membership(test_set1, 
                                                        reference_set1), 
                            [6, 7],
                            'Did not get [6, 7] as missing set members')

      self.failUnlessEqual(utilities.get_set_membership(test_set1, 
                                                        reference_set1,
                                                        default_set1), 
                            [],
                            'Did not get [] as missing set members')

      self.failUnlessEqual(utilities.get_set_membership(reference_set1, 
                                                        reference_set1), 
                            [],
                            'Did not get [] as missing set members')

      test_set2 = ['a', 'b', 'c', 'd', 'e']
      reference_set2 = ['a', 'b', 'c']
      default_set2 = ['d', 'e']
      self.failUnlessEqual(utilities.get_set_membership(test_set2, 
                                                        reference_set2), 
                            ['d', 'e'],
                            'Did not get [d, e] as missing set members')

      self.failUnlessEqual(utilities.get_set_membership(test_set2, 
                                                        reference_set2,
                                                        default_set2), 
                            [],
                            'Did not get [] as missing set members')

      self.failUnlessEqual(utilities.get_set_membership(reference_set2, 
                                                        reference_set2), 
                            [],
                            'Did not get [] as missing set members')

    def test_blank(self):
      """
      Test functionality of blank function
      """
      
      self.failIf(utilities.blank(1), 
                  'blank indicated 1 was a blank value')
      self.failIf(utilities.blank('a'), 
                  'blank indicated a was a blank value')
      self.failUnless(utilities.blank('unavailable'), 
                      'blank did not indicate unavailable was a blank value')
      self.failUnless(utilities.blank(None), 
                      'blank did not indicate None was a blank value')
      self.failUnless(utilities.blank('unavAilablE'), 
                      'blank did not indicate unavAilablE was a blank value')

    def test_get_vos(self):
      """
      Test get_vos function
      """  
      
      vo_file = os.path.abspath('./test_files/sample-vos.txt')
      self.failUnlessEqual(utilities.get_vos(vo_file), 
                           ['osg', 'LIGO', 'cdf'], 
                           "Correct vos not found")
      
    def test_duplicate_sections(self):
      did_fail = False
      

      self.failUnlessRaises(SystemExit, 
                            configure_osg.read_config_file, 
                            configuration_file = "configs/utilities/duplicate_sections.ini")

      self.failUnlessRaises(SystemExit, 
                            configure_osg.read_config_file, 
                            configuration_file = "configs/utilities/duplicate_sections2.ini")
      
      try:
        configure_osg.read_config_file("configs/utilities/duplicate_sections3.ini")
      except SystemExit:
        self.fail("Non-duplicate section flagged as duplicated.")

      try:
        configure_osg.read_config_file("configs/utilities/duplicate_sections4.ini")
      except SystemExit:
        self.fail("Commented out sections flagged as duplicated sections.")

    def test_valid_user_vo_file(self):
      """
      Test functionality of valid_user_vo_file function
      """
      
      test_file = os.path.abspath("./test_files/valid-user-vo-map.txt")
      self.failUnless(utilities.valid_user_vo_file(test_file, False), 
                      "Valid file flagged as invalid")
      
      test_file = os.path.abspath("./test_files/invalid-user-vo-map.txt")
      self.failIf(utilities.valid_user_vo_file(test_file, False), 
                  "Invalid file flagged as valid")
      bad_lines = utilities.valid_user_vo_file(test_file, True)[1]
      standard_lines =  ['fdjkf394f023', 'sam= 34f3']
      self.failUnlessEqual(bad_lines, standard_lines, 
                           "Wrong lines from the vo map obtained, " +
                           "got\n%s" % (bad_lines) +
                           "\nexpected\n%s" % (standard_lines))
      
    def test_valid_bookean(self):
      """
      Test functionality of valid_boolean function
      """
      config_file = os.path.abspath('./configs/utilities/valid_boolean.ini')
      config = ConfigParser.SafeConfigParser()
      config.read(config_file)
      self.failIf(utilities.valid_boolean(config, 'Test', 'invalid_bool'),
                  'invalid_bool flagged as valid')
      self.failIf(utilities.valid_boolean(config, 'Test', 'invalid_bool2'),
                  'invalid_bool2 flagged as valid')
      self.failIf(utilities.valid_boolean(config, 'Test', 'missing'),
                  'invalid_bool2 flagged as valid')
      self.failUnless(utilities.valid_boolean(config, 'Test', 'valid_bool'),
                      'valid_bool flagged as invalid')
      self.failUnless(utilities.valid_boolean(config, 'Test', 'valid_bool2'),
                      'valid_bool2 flagged as invalid')

    def test_valid_executable(self):
      """
      Test functionality of valid_executable function
      """
      
      binary = "/bin/ls"
      text = os.path.abspath("./test_files/subscriptions.xml")
      missing = os.path.abspath("./test_files/foo")
      
      self.failIf(utilities.valid_executable(missing), 
                  "Non-existent file is not a valid executable")
      self.failIf(utilities.valid_executable(text), 
                  "Text file is not a valid executable")
      self.failUnless(utilities.valid_executable(binary), 
                      "/bin/ls should be a valid binary")
      
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
                            utilities.get_option,
                            config = config,
                            section = section,
                            option = 'missing')
      optional_settings = [option]
      
      # do optional settings get handled correctly if they are missing
      self.failUnlessEqual(None, 
                           utilities.get_option(config, 
                                                section, 
                                                option, 
                                                optional_settings), 
                           'Raised exception for missing optional setting')
      defaults = { option : 'test'}
      # make sure defaults get used 
      self.failUnlessEqual('test', 
                           utilities.get_option(config, 
                                                section, 
                                                option, 
                                                optional_settings,
                                                defaults), 
                           'Raised exception for missing optional setting')
      # get integer option
      config.set(section, option, '1')
      self.failUnlessEqual(1, 
                           utilities.get_option(config, 
                                                section, 
                                                option, 
                                                optional_settings,
                                                defaults,
                                                types.IntType), 
                           'Should have gotten an integer equal to 1 back')
      
      # get float option
      config.set(section, option, '1.23e5')
      self.failUnlessAlmostEqual(1.23e5, 
                                 utilities.get_option(config, 
                                                      section, 
                                                      option, 
                                                      optional_settings,
                                                      defaults,
                                                      types.FloatType),
                                 7,
                                 'Should have gotten a float equal to 1.23e5 back')

      # check errors when wrong type specified
      self.failUnlessRaises(exceptions.SettingError, 
                            utilities.get_option,
                            config = config,
                            section = section,
                            option = option,
                            defaults = defaults,
                            option_type = types.IntType)

      # get boolean option 
      config.set(section, option, 'False')
      self.failUnlessEqual(False, 
                           utilities.get_option(config, 
                                                section, 
                                                option, 
                                                optional_settings,
                                                defaults,
                                                types.BooleanType), 
                           'Should have gotten False back')
      # check errors when wrong type specified
      self.failUnlessRaises(exceptions.SettingError, 
                            utilities.get_option,
                            config = config,
                            section = section,
                            option = option,
                            defaults = defaults,
                            option_type = types.IntType)
      
      # check errors when wrong type specified
      config.set(section, option, 'abc')
      self.failUnlessRaises(exceptions.SettingError, 
                            utilities.get_option,
                            config = config,
                            section = section,
                            option = option,
                            defaults = defaults,
                            option_type = types.BooleanType)

      # check to make sure that default gets set when setting is set to 
      # blank/UNAVAILABLE
      config.set(section, option, 'UNAVAILABLE')
      self.failUnlessEqual('test', 
                           utilities.get_option(config, 
                                                section, 
                                                option, 
                                                optional_settings,
                                                defaults), 
                           'Should have gotten a value of test back')

    def test_valid_file2(self):
      """
      Test functionality of valid_file function
      """

      filename = './configs/utilities/duplicate_sections.ini'
      self.failIf(utilities.valid_ini_file(filename),
                  "Didn't detect duplicated section in %s" % filename)

      filename = './configs/utilities/duplicate_sections2.ini'
      self.failIf(utilities.valid_ini_file(filename),
                  "Didn't detect duplicated section in %s" % filename)

      filename = './configs/utilities/duplicate_sections3.ini'
      self.failUnless(utilities.valid_ini_file(filename),
                      "Got error on valid file %s" % filename)

      filename = './configs/utilities/duplicate_sections4.ini'
      self.failUnless(utilities.valid_ini_file(filename),
                      "Got error on valid file %s" % filename)

      filename = './configs/utilities/newline.ini'
      self.failIf(utilities.valid_ini_file(filename),
                  "Didn't detect newline in %s"  % filename)

      filename = './configs/utilities/valid_boolean.ini'
      self.failUnless(utilities.valid_ini_file(filename),
                      "Got error on valid file %s" % filename)
      
    def test_valid_references(self):
      """
      Test functionality of invalid_references_exist and make sure 
      it catches invalid references correctly and lets valid references
      go
      """

      filename = './configs/utilities/invalid_ref1.ini'
      self.failIf(utilities.valid_ini_file(filename),
                  "Didn't detect invalid reference in %s" % filename)

      filename = './configs/utilities/invalid_ref2.ini'
      self.failIf(utilities.valid_ini_file(filename),
                  "Didn't detect invalid reference in %s" % filename)

      filename = './configs/utilities/valid_ref1.ini'
      self.failUnless(utilities.valid_ini_file(filename),
                      "Got error on valid file %s" % filename)

    def test_template(self):
      """
      Test functionality of config_template and make sure 
      it catches a config template
      """

      filename = './configs/utilities/template.ini'
      config = ConfigParser.SafeConfigParser()
      config.read(filename)
      self.failUnless(utilities.config_template(config),
                      "Didn't detect template in %s" % filename)



if __name__ == '__main__':
    unittest.main()

