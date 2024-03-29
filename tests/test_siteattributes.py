"""Unit tests to test site attribute configuration"""

# pylint: disable=W0703
# pylint: disable=R0904

import os
import sys
import unittest
import configparser
import logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.configure_modules import siteinformation
from osg_configure.modules.utilities import get_test_config, ce_installed

# NullHandler is only available in Python 2.7+
try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

global_logger = logging.getLogger(__name__)
global_logger.addHandler(NullHandler())


class TestSiteAttributes(unittest.TestCase):
    """
    Unit test class to test SiteAttributes class
    """

    def testParsing1(self):
        """
        Test siteattributes parsing
        """

        config_file = get_test_config("siteattributes/siteattributes1.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = siteinformation.SiteInformation(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        variables = {'OSG_GROUP': 'OSG-ITB',
                     'OSG_HOSTNAME': 'example.com',
                     'OSG_SITE_NAME': 'MY_SITE',
                    }
        for var in variables:
            self.assertTrue(var in attributes,
                            "Attribute %s missing" % var)
            self.assertEqual(attributes[var],
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, attributes[var], variables[var]))

    def testParsing2(self):
        """
        Test siteattributes parsing
        """

        config_file = get_test_config("siteattributes/siteattributes2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = siteinformation.SiteInformation(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        variables = {'OSG_GROUP': 'OSG',
                     'OSG_HOSTNAME': 'example.com',
                     'OSG_SITE_NAME': 'MY_SITE',
                    }
        for var in variables:
            self.assertTrue(var in attributes,
                            "Attribute %s missing" % var)
            self.assertEqual(attributes[var],
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, attributes[var], variables[var]))

    def testParsing3(self):
        """
        Test siteattributes parsing
        """

        config_file = get_test_config("siteattributes/siteattributes3.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = siteinformation.SiteInformation(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        variables = {'OSG_GROUP': 'OSG',
                     'OSG_HOSTNAME': 'example.com',
                     'OSG_SITE_NAME': 'MY_SITE',
                    }
        for var in variables:
            self.assertTrue(var in attributes,
                            "Attribute %s missing" % var)
            self.assertEqual(attributes[var],
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, attributes[var], variables[var]))
        if ('resource_group' not in settings.options or
                    settings.options['resource_group'].value != 'RESOURCE_GROUP'):
            self.fail('resource_group not present or not set to RESOURCE_GROUP')

    def testMissingAttribute(self):
        """
        Test the parsing when attributes are missing, should get exceptions
        """
        config_file = get_test_config("siteattributes/siteattributes2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = siteinformation.SiteInformation(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        mandatory_on_all = ['group']
        # ^ TODO OSG 3.5: add "resource" to this list
        mandatory_on_ce = ['host_name']
        mandatory = list(mandatory_on_all)
        if ce_installed():
            mandatory += mandatory_on_ce
        for option in mandatory:
            config_file = get_test_config("siteattributes/siteattributes1.ini")
            configuration = configparser.SafeConfigParser()
            configuration.read(config_file)
            configuration.remove_option('Site Information', option)

            settings = siteinformation.SiteInformation(logger=global_logger)
            self.assertRaises(exceptions.SettingError,
                              settings.parse_configuration,
                              configuration)

    def testInvalidHostname(self):
        """
        Test the check_attributes with invalid hostname
        """

        config_file = get_test_config("siteattributes/" \
                                      "invalid_hostname.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = siteinformation.SiteInformation(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid hostname ignored")

    def testValidSettings(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("siteattributes/valid_settings.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = siteinformation.SiteInformation(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct locations incorrectly flagged as missing")

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("siteattributes/siteattributes3.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = siteinformation.SiteInformation(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct locations incorrectly flagged as missing")


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()
