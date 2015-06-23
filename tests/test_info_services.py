"""Unit tests to test infoservices configuration class"""
# This has been copied from test_cemon.py and has had the names changed.
# Further changes will be needed to reduce duplication between the two
# sets of tests; changes will need to be made to the configure modules
# to reduce duplication there as well.

# pylint: disable=W0703
# pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.configure_modules import infoservices
from  osg_configure.modules import utilities
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger(__name__)
if sys.version_info[0] >= 2 and sys.version_info[1] > 6:
    global_logger.addHandler(logging.NullHandler())
else:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

    global_logger.addHandler(NullHandler())


class TestInfoServices(unittest.TestCase):
    """
    Unit test class to test InfoServicesConfiguration class
    """

    def testParsing1(self):
        """
        Test infoservices parsing
        """

        config_file = get_test_config("infoservices/infoservices.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'ress_servers': 'https://osg-ress-1.fnal.gov:8443/ig/services/CEInfoCollector[OLD_CLASSAD]',
                     'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW], http://is2.grid.iu.edu:14001[RAW]'}

        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var,
                                              options[var].value,
                                              variables[var]))

    def testParsingITBDefaults(self):
        """
        Test infoservices parsing to make sure it picks up ITB defaults
        """

        # need to be on a CE to get CE defaults
        if not utilities.ce_installed():
            return
        config_file = get_test_config("infoservices/itb_defaults.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'ress_servers': 'https://osg-ress-4.fnal.gov:8443/ig/'
                                     'services/CEInfoCollector[OLD_CLASSAD]',
                     'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW],'
                                     'http://is2.grid.iu.edu:14001[RAW]'}

        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var,
                                              options[var].value,
                                              variables[var]))

    def testParsingProductionDefaults(self):
        """
        Test infoservices parsing to make sure it picks up production defaults
        """

        # need to be on a CE to get CE defaults
        if not utilities.ce_installed():
            return
        config_file = get_test_config("infoservices/prod_defaults.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'ress_servers': 'https://osg-ress-1.fnal.gov:8443/ig/'
                                     'services/CEInfoCollector[OLD_CLASSAD]',
                     'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW],'
                                     'http://is2.grid.iu.edu:14001[RAW]'}

        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var,
                                              options[var].value,
                                              variables[var]))

    def testParsingMissingITBDefaults(self):
        """
        Test infoservices parsing to make sure it picks up ITB defaults
        when the infoservices section is missing
        """

        # need to be on a CE to get CE defaults
        if not utilities.ce_installed():
            return
        config_file = get_test_config("infoservices/itb_defaults2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'ress_servers': 'https://osg-ress-4.fnal.gov:8443/ig/'
                                     'services/CEInfoCollector[OLD_CLASSAD]',
                     'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW],'
                                     'http://is2.grid.iu.edu:14001[RAW]'}

        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var,
                                              options[var].value,
                                              variables[var]))

    def testParsingMissingProductionDefaults(self):
        """
        Test infoservices parsing to make sure it picks up production defaults
        when the infoservices section is missing
        """

        # need to be on a CE to get CE defaults
        if not utilities.ce_installed():
            return
        config_file = get_test_config("infoservices/prod_defaults2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'ress_servers': 'https://osg-ress-1.fnal.gov:8443/ig/'
                                     'services/CEInfoCollector[OLD_CLASSAD]',
                     'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW],'
                                     'http://is2.grid.iu.edu:14001[RAW]'}

        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var,
                                              options[var].value,
                                              variables[var]))

    def testParsingDisabled(self):
        """
        Test infoservices parsing when set to disabled
        """

        config_file = get_test_config("infoservices/disabled.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertEqual(settings.options['ress_servers'].value, '',
                         "Disabled configuration should have no attributes")
        self.assertEqual(settings.options['bdii_servers'].value, '',
                         "Disabled configuration should have no attributes")

    def testParsingIgnored(self):
        """
        Test infoservices parsing when set to ignored
        """

        config_file = get_test_config("infoservices/ignored.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertEqual(settings.options['ress_servers'].value, '',
                         "Disabled configuration should have no attributes")
        self.assertEqual(settings.options['bdii_servers'].value, '',
                         "Disabled configuration should have no attributes")

    def testIgnoredServices(self):
        """
        Test infoservices parsing when ignoring just bdii or ress
        """

        config_file = get_test_config("infoservices/ignore_ress.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertEqual(settings.ress_servers, {},
                         "Should not have ress subscriptions when being ignored")

        config_file = get_test_config("infoservices/ignore_bdii.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertEqual(settings.bdii_servers, {},
                         "Should not have BDII subscriptions when being ignored")

    def testInvalidRess1(self):
        """
        Test the check_attributes function to see if it catches invalid
        ress servers
        """

        config_file = get_test_config("infoservices/invalid_ress1.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        self.assertRaises(exceptions.SettingError,
                          settings.parse_configuration,
                          configuration=configuration)

    def testInvalidRess2(self):
        """
        Test the check_attributes function to see if it catches invalid
        ress servers
        """

        config_file = get_test_config("infoservices/invalid_ress2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice invalid ress server")

    def testInvalidRess3(self):
        """
        Test the check_attributes function to see if it catches invalid
        ress servers
        """

        config_file = get_test_config("infoservices/invalid_ress3.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice invalid ress server")

    def testInvalidBDII1(self):
        """
        Test the check_attributes function to see if it catches invalid
        bdii servers
        """

        config_file = get_test_config("infoservices/invalid_bdii1.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        self.assertRaises(exceptions.SettingError,
                          settings.parse_configuration,
                          configuration=configuration)

    def testInvalidBDII2(self):
        """
        Test the check_attributes function to see if it catches invalid
        bdii servers
        """

        config_file = get_test_config("infoservices/invalid_bdii2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice invalid bdii server")

    def testInvalidBDII3(self):
        """
        Test the check_attributes function to see if it catches invalid
        bdii servers
        """

        config_file = get_test_config("infoservices/invalid_bdii3.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice invalid bdii server")

    def testValidSettings(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("infoservices/check_ok.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct settings incorrectly flagged as invalid")

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it oks a disabled section
        """

        config_file = get_test_config("infoservices/disabled.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Disabled section incorrectly flagged as invalid")

    def testValidITBDefaults(self):
        """
        Test the check_attributes function to see if it oks the itb defaults
        """

        # need to be on a CE to get CE defaults
        if not utilities.ce_installed():
            return

        config_file = get_test_config("infoservices/itb_defaults.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "ITB defaults incorrectly flagged as invalid")

    def testValidProductionDefaults(self):
        """
        Test the check_attributes function to see if it oks the production defaults
        """

        # need to be on a CE to get CE defaults
        if not utilities.ce_installed():
            return
        config_file = get_test_config("infoservices/prod_defaults.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "production defaults incorrectly flagged as invalid")

    def testMissingCEITBDefaults(self):
        """
        Test the check_attributes function to see if it oks the itb defaults
        set when the infoservices section is missing
        """

        config_file = get_test_config("infoservices/itb_defaults2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "ITB defaults incorrectly flagged as invalid")

    def testMissingProductionDefaults(self):
        """
        Test the check_attributes function to see if it oks the production defaults
        set when the infoservices section is missing
        """

        config_file = get_test_config("infoservices/prod_defaults2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "production defaults incorrectly flagged as invalid")

    def testMultipleRessServers(self):
        """
        Test the check_attributes function to see if it oks the production defaults
        set when the infoservices section is missing
        """

        config_file = get_test_config("infoservices/multiple_ress.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue(len(settings.ress_servers) == 3,
                        "Did not parse ress servers correctly")

    def testMultipleBDIIServers(self):
        """
        Test the check_attributes function to see if it oks the production defaults
        set when the infoservices section is missing
        """

        config_file = get_test_config("infoservices/multiple_bdii.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue(len(settings.bdii_servers) == 3,
                        "Did not parse bdii servers correctly")

    def testServiceList(self):
        """
        Test to make sure right services get returned
        """

        config_file = get_test_config("infoservices/infoservices.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = set()
        if settings.ois_required_rpms_installed:
            expected_services.add('osg-info-services')
        if settings.ce_collector_required_rpms_installed and settings.htcondor_gateway_enabled:
            expected_services.add('condor-ce')
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        config_file = get_test_config("infoservices/disabled.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()

# vim:sw=2:sts=2
