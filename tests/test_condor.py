"""Unit tests to test condor configuration"""

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

from osg_configure.configure_modules import condor
from osg_configure.modules.utilities import get_test_config

# NullHandler is only available in Python 2.7+
try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

global_logger = logging.getLogger(__name__)
global_logger.addHandler(NullHandler())


class TestCondor(unittest.TestCase):
    """
    Unit test class to test CondorConfiguration class
    """

    def testParsing(self):
        """
        Test condor parsing
        """

        config_file = get_test_config("condor/condor1.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        options = {'OSG_JOB_MANAGER_HOME': '/opt/condor',
                   'OSG_CONDOR_LOCATION': '/opt/condor',
                   'OSG_CONDOR_CONFIG': '/etc/condor/condor_config',
                   'OSG_JOB_MANAGER': 'Condor'}
        for option in options:
            value = options[option]
            self.assertTrue(option in attributes,
                            "Attribute %s missing" % option)
            err_msg = "Wrong value obtained for %s, " \
                      "got %s instead of %s" % (option, attributes[option], value)
            self.assertEqual(attributes[option], value, err_msg)

    def testParsingDisabled(self):
        """
        Test condor parsing when disabled
        """

        config_file = get_test_config("condor/condor_disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertEqual(len(attributes), 0,
                         "Disabled configuration should have no attributes")

    def testParsingIgnored(self):
        """
        Test condor parsing when ignored
        """

        config_file = get_test_config("condor/ignored.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(len(attributes) == 0,
                        "Disabled configuration should have no attributes")

    def testParsingDefaults(self):
        """
        Test handling of defaults when parsing a configuration
        """

        config_file = get_test_config("condor/condor_defaults1.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)


        # check to see if we can get values from condor_* variables
        os.environ['CONDOR_LOCATION'] = '/my/condor'
        os.environ['CONDOR_CONFIG'] = '/my/condor/etc/condor_config'
        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue('OSG_CONDOR_LOCATION' in attributes,
                        'Attribute OSG_CONDOR_LOCATION missing')
        self.assertEqual(attributes['OSG_CONDOR_LOCATION'], '/my/condor',
                         'Wrong value obtained for OSG_CONDOR_LOCATION')

        self.assertTrue('OSG_CONDOR_CONFIG' in attributes,
                        'Attribute OSG_CONDOR_CONFIG missing')
        self.assertEqual(attributes['OSG_CONDOR_CONFIG'],
                         '/my/condor/etc/condor_config',
                         'Wrong value obtained for OSG_CONDOR_CONFIG')

        # check when condor_config is not present
        del os.environ['CONDOR_CONFIG']
        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue('OSG_CONDOR_LOCATION' in attributes,
                        'Attribute OSG_CONDOR_LOCATION missing')
        self.assertEqual(attributes['OSG_CONDOR_LOCATION'], '/my/condor',
                         'Wrong value obtained for OSG_CONDOR_LOCATION')

        self.assertTrue('OSG_CONDOR_CONFIG' in attributes,
                        'Attribute OSG_CONDOR_CONFIG missing')
        self.assertEqual(attributes['OSG_CONDOR_CONFIG'],
                         '/etc/condor/condor_config',
                         'Wrong value obtained for OSG_CONDOR_CONFIG')


        # check to make sure that config values take precedence over
        # environment variables
        config_file = get_test_config("condor/condor1.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)
        os.environ['CONDOR_LOCATION'] = '/my/condor1'
        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue('OSG_CONDOR_LOCATION' in attributes,
                        'Attribute OSG_CONDOR_LOCATION missing')
        self.assertEqual(attributes['OSG_CONDOR_LOCATION'], '/opt/condor',
                         'Wrong value obtained for OSG_CONDOR_LOCATION')

        self.assertTrue('OSG_CONDOR_CONFIG' in attributes,
                        'Attribute OSG_CONDOR_CONFIG missing')
        self.assertEqual(attributes['OSG_CONDOR_CONFIG'],
                         '/etc/condor/condor_config',
                         'Wrong value obtained for OSG_CONDOR_CONFIG')

        # check to see if jobmanager home values get used in preference to other values
        config_file = get_test_config("condor/condor_defaults2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)
        os.environ['CONDOR_LOCATION'] = '/my/condor1'
        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue('OSG_CONDOR_LOCATION' in attributes,
                        'Attribute OSG_CONDOR_LOCATION missing')
        self.assertEqual(attributes['OSG_CONDOR_LOCATION'], '/usr/local/condor',
                         'Wrong value obtained for OSG_CONDOR_LOCATION')

        self.assertTrue('OSG_CONDOR_CONFIG' in attributes,
                        'Attribute OSG_CONDOR_CONFIG missing')
        self.assertEqual(attributes['OSG_CONDOR_CONFIG'],
                         '/etc/condor/condor_config',
                         'Wrong value obtained for OSG_CONDOR_CONFIG')

    def testMissingCondorLocation(self):
        """
        Test the check_attributes function to see if it catches missing condor location
        """

        config_file = get_test_config("condor/missing_location.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice missing condor location")

    def testMissingCondorConfig(self):
        """
        Test the check_attributes function to see if it catches missing
        condor config locations
        """

        for filename in [get_test_config("condor/missing_config1.ini"),
                         get_test_config("condor/missing_config2.ini")]:
            config_file = os.path.abspath(filename)
            configuration = configparser.SafeConfigParser()
            configuration.read(config_file)

            settings = condor.CondorConfiguration(logger=global_logger)
            try:
                settings.parse_configuration(configuration)
            except Exception as e:
                self.fail("Received exception while parsing configuration: %s" % e)

            attributes = settings.get_attributes()
            self.assertFalse(settings.check_attributes(attributes),
                             "Did not notice missing condor config location: " +
                             attributes['OSG_CONDOR_CONFIG'])

    def testValidSettings(self):
        """
        Test the check_attributes function to see if it works on valid settings
        """

        config_file = get_test_config("condor/check_ok.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct settings incorrectly flagged as missing")

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it works on valid settings
        """

        config_file = get_test_config("condor/check_ok2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct settings incorrectly flagged as missing")

    def testServiceList(self):
        """
        Test to make sure right services get returned
        """

        config_file = get_test_config("condor/check_ok.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = {'condor-ce', 'globus-gridftp-server'}
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        config_file = get_test_config("condor/condor_disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = condor.CondorConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = set()
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()
