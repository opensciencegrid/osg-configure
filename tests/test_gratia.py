"""Unit tests to test gratia configuration class"""

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

from osg_configure.modules import utilities

from osg_configure.configure_modules import gratia
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


class TestGratia(unittest.TestCase):
    """
    Unit test class to test GratiaConfiguration class
    """

    def testParsing1(self):
        """
        Test gratia parsing
        """

        config_file = get_test_config("gratia/gratia.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'probes': 'jobmanager:gratia-osg-prod.opensciencegrid.org:80, ' \
                               'gridftp:gratia-osg-transfer.opensciencegrid.org:80'}
        for var in variables:
            self.assertTrue(var in options,
                            "Attribute %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

    def testParsingITBDefault(self):
        """
        Make sure gratia picks up the itb defaults
        """

        # need to be on a CE to get CE defaults
        if not gratia.requirements_are_installed():
            return

        config_file = get_test_config("gratia/itb_default.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'probes': 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
        for var in variables:
            self.assertTrue(var in options,
                            "Attribute %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

    def testParsingProductionDefault(self):
        """
        Make sure gratia picks up the itb defaults
        """

        # need to be on a CE to get CE defaults
        if not gratia.requirements_are_installed():
            return

        config_file = get_test_config("gratia/prod_default.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'probes': 'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}
        for var in variables:
            self.assertTrue(var in options,
                            "Attribute %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

    def testParsingMissingITBDefault(self):
        """
        Make sure gratia picks up the itb defaults when the gratia
        section is missing
        """

        # need to be on a CE to get CE defaults
        if not gratia.requirements_are_installed():
            return
        config_file = get_test_config("gratia/itb_default2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'probes': 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
        for var in variables:
            self.assertTrue(var in options,
                            "Attribute %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

        config_file = get_test_config("gratia/itb_default3.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'probes': 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
        for var in variables:
            self.assertTrue(var in options,
                            "Attribute %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

    def testParsingMissingProductionDefault(self):
        """
        Make sure gratia picks up the production defaults when the gratia
        section is missing
        """

        # need to be on a CE to get CE defaults
        if not gratia.requirements_are_installed():
            return
        config_file = get_test_config("gratia/prod_default2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'probes': 'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}
        for var in variables:
            self.assertTrue(var in options,
                            "Attribute %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

    def testParsingDisabled(self):
        """
        Test gratia parsing with negative values
        """

        config_file = get_test_config("gratia/disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertEqual(len(settings.options['probes'].value),
                         0,
                         "Disabled configuration should have no attributes")

    def testParsingIgnored(self):
        """
        Test gratia parsing when section is ignored
        """

        config_file = get_test_config("gratia/ignored.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertEqual(len(settings.options['probes'].value),
                         0,
                         "Disabled configuration should have no attributes")

    def testInvalidProbes2(self):
        """
        Test the check_attributes function to see if it catches invalid
        probes
        """

        config_file = get_test_config("gratia/invalid_probe2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice invalid probe specification")

    def testValidSettings(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("gratia/check_ok.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        # new checks require an installed and working copy of HTCondor
        # disable for now
        # self.assertTrue(settings.check_attributes(attributes),
        #                "Correct settings incorrectly flagged as invalid")

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it oks a disabled section
        """

        config_file = get_test_config("gratia/disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Disabled section incorrectly flagged as invalid")

    def testValidITBDefaults(self):
        """
        Test the ITB defaults and make sure that they are valid
        """
        config_file = get_test_config("gratia/itb_default.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except OSError:
            # Need to rewrite or remove this test due to new checks with condor
            pass
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        # new checks require an installed and working copy of HTCondor
        # disable for now
        # self.assertTrue(settings.check_attributes(attributes),
        #                "ITB defaults flagged as invalid")

    def testValidProductionDefaults(self):
        """
        Test the production defaults and make sure that they are valid
        """
        config_file = get_test_config("gratia/prod_default.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        # new checks require an installed and working copy of HTCondor
        # disable for now
        # self.assertTrue(settings.check_attributes(attributes),
        #                "Production defaults flagged as invalid")

    def testMissingITBDefaults(self):
        """
        Test the ITB defaults and make sure that they are valid when the
        gratia section is missing
        """
        config_file = get_test_config("gratia/itb_default2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "ITB defaults flagged as invalid")

    def testMissingProductionDefaults(self):
        """
        Test the production defaults and make sure that they are valid when the
        gratia section is missing
        """
        config_file = get_test_config("gratia/prod_default2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Production defaults flagged as invalid")

    def testServiceList(self):
        """
        Test to make sure right services get returned
        """

        config_file = get_test_config("gratia/check_ok.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = set(['gratia-probes-cron'])
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        config_file = get_test_config("gratia/disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = gratia.GratiaConfiguration(logger=global_logger)
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
