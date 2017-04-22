"""Unit tests to test misc configuration"""

# pylint: disable=W0703
# pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import logging
import tempfile
import subprocess

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import misc
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


class TestMisc(unittest.TestCase):
    """
    Unit test class to test MiscConfiguration class
    """

    def testParsing1(self):
        """
        Test misc parsing
        """

        config_file = get_test_config("misc/misc1.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'glexec_location': './configs/misc',
                     'gums_host': 'my.gums.org',
                     'authorization_method': 'xacml'}
        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))
        attributes = settings.get_attributes()
        variables = {'OSG_GLEXEC_LOCATION': './configs/misc'}
        for var in variables:
            self.assertTrue(attributes.has_key(var),
                            "Attribute %s missing" % var)
            self.assertEqual(attributes[var],
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, attributes[var], variables[var]))

    def testParsing2(self):
        """
        Test misc parsing with negative values
        """

        config_file = get_test_config("misc/misc2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'glexec_location': './configs/misc',
                     'gums_host': 'my.gums.org',
                     'authorization_method': 'xacml'}
        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))
        attributes = settings.get_attributes()
        variables = {'OSG_GLEXEC_LOCATION': './configs/misc'}
        for var in variables:
            self.assertTrue(attributes.has_key(var),
                            "Attribute %s missing" % var)
            self.assertEqual(attributes[var],
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, attributes[var], variables[var]))

    def testParsingAuthentication(self):
        """
        Test misc parsing with negative values
        """

        config_file = get_test_config("misc/misc_xacml.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue(settings.options.has_key('authorization_method'),
                        "Attribute authorization_method missing")
        self.assertEqual(settings.options['authorization_method'].value,
                         'xacml',
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',
                                          settings.options['authorization_method'].value,
                                          'xacml'))

        config_file = get_test_config("misc/misc_gridmap.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue(settings.options.has_key('authorization_method'),
                        "Attribute authorization_method missing")
        self.assertEqual(settings.options['authorization_method'].value,
                         'gridmap',
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',
                                          settings.options['authorization_method'].value,
                                          'gridmap'))

        config_file = get_test_config("misc/misc_local_gridmap.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue(settings.options.has_key('authorization_method'),
                        "Attribute authorization_method missing")
        self.assertEqual(settings.options['authorization_method'].value,
                         'local-gridmap',
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',
                                          settings.options['authorization_method'].value,
                                          'local-gridmap'))

    def testMissingAttribute(self):
        """
        Test the parsing when attributes are missing, should get exceptions
        """

        mandatory = ['gums_host']
        for option in mandatory:
            config_file = get_test_config("misc/misc1.ini")
            configuration = ConfigParser.SafeConfigParser()
            configuration.read(config_file)
            configuration.remove_option('Misc Services', option)

            settings = misc.MiscConfiguration(logger=global_logger)
            settings.parse_configuration(configuration)
            self.assertTrue(not settings.check_attributes({}))

    def testXacmlMissingGums(self):
        """
        Test the check_attributes function when xacml is specified but the
        gums host isn't
        """

        config_file = get_test_config("misc/misc_xacml_missing_gums.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        settings.parse_configuration(configuration)
        self.assertTrue(exceptions.ConfigureError,
                        settings.check_attributes({}))

    def testXacmlBadGums(self):
        """
        Test the check_attributes function when xacml is specified but the
        gums host isn't valid
        """

        config_file = get_test_config("misc/misc_xacml_bad_gums.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice bad gums host")

    def testValidSettings(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("misc/valid_settings.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct locations incorrectly flagged as missing")

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("misc/valid_settings2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct locations incorrectly flagged as invalid")

    def testInvalidSettings(self):
        """
        Test the check_attributes function to see if it flags bad attributes
        """

        config_file = get_test_config("misc/invalid_settings1.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Bad config incorrectly flagged as okay")

    def testServiceList(self):
        """
        Test to make sure right services get returned
        """

        config_file = get_test_config("misc/misc_xacml.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        if utilities.rpm_installed('fetch-crl'):
            expected_services = set(['fetch-crl-cron',
                                     'fetch-crl-boot',
                                     'gums-client-cron'])
        else:
            expected_services = set(['gums-client-cron'])

        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        config_file = get_test_config("misc/misc_gridmap.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        if utilities.rpm_installed('fetch-crl'):
            expected_services = set(['fetch-crl-cron',
                                     'fetch-crl-boot',
                                     'edg-mkgridmap'])
        else:
            expected_services = set(['edg-mkgridmap'])

        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()
