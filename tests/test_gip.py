"""Module for unit testing gip configuration"""

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

global_logger = logging.getLogger(__name__)
if sys.version_info[0] >= 2 and sys.version_info[1] > 6:
    global_logger.addHandler(logging.NullHandler())
else:
    # NullHandler is only in python 2.7 and above
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

    global_logger.addHandler(NullHandler())

from osg_configure.configure_modules import gip
from osg_configure.configure_modules import localsettings

from osg_configure.modules import exceptions
from osg_configure.modules import utilities

from osg_configure.modules.utilities import get_test_config

SAMPLE_VO_MAP_LOCATION = 'gip/sample_vo_map'


class TestGip(unittest.TestCase):
    """Class for unit testing GIP configuration code"""

    def test_missing_sc(self):
        """
        Make sure that we have failures when there is no configured SC.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/red-missing-sc.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
            gip_config._parse_configuration_ce(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail, msg="Did not properly detect a missing SC.")

    def test_missing_se(self):
        """
        Make sure that we have failures when there is no configured SE and there
        is no classic SE.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/red-missing-se.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail, msg="Did not properly detect a missing SE.")

    def test_missing_se2(self):
        """
        Make sure that we have no when there is no configured SE and there
        is a classic SE.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/red-missing-se2.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertFalse(did_fail, msg="Did not properly detect a missing SE.")

    def test_changeme1(self):
        """
        Test should pass if SE CHANGEME section is disabled.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/changeme_section.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertFalse(did_fail, msg="Falsely detected an enabled CHANGEME section.")

    def test_changeme2(self):
        """
        Test should fail because SE CHANGEME section is enabled.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/changeme_section_bad.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail, msg="Did not detect SE CHANGEME section.")

    def test_changeme3(self):
        """
        Test should fail because SE CHANGEME section is enabled.
        Variant 2.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/changeme_section_bad2.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail, msg="Did not detect enabled CHANGEME section.")

    def test_changeme4(self):
        """
        Test should fail because SC CHANGEME section is present.

        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/changeme_section_sc.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
            gip_config._parse_configuration_ce(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail, msg="Did not detect enabled CHANGEME section.")

    def test_changeme5(self):
        """
        Test should not fail because SE CHANGEME section is disabled.
        Variant 2.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/changeme_section_bad3.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertFalse(did_fail, msg="Falsely detected an enabled CHANGEME section.")

    def test_missing_attributes(self):
        """
        Make sure that we have failures when there are missing attributes.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/red-missing-attributes.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config._parse_configuration(config_parser)
            gip_config._parse_configuration_ce(config_parser)
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail, msg="Did not properly detect missing attrs.")

    def test_old_config(self):
        """
        Make sure that we can correctly parse an old-style GIP config.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/red-old-gip-config.ini")
        config_parser.read(config_file)
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)

    def test_new_config(self):
        """
        Make sure that we can correctly parse a correct new-style GIP config.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/red-new-gip-config.ini")
        config_parser.read(config_file)
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

    def test_doherty(self):
        """
        Make sure that we can correctly parse a correct new-style GIP config.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/doherty.ini")
        config_parser.read(config_file)
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

    def test_local_settings(self):
        """
        Test to see if the local settings parsing works.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_parser.optionxform = str
        config_file = get_test_config("gip/local_settings.ini")
        config_parser.read(config_file)
        local_settings = localsettings.LocalSettings(logger= \
                                                         global_logger)
        local_settings.parse_configuration(config_parser)
        attributes = local_settings.get_attributes()
        self.assertTrue('default' not in attributes,
                        msg="Attributes set that weren't in the test config file")
        self.assertTrue('Foo' in attributes and attributes['Foo'] == 'value1',
                        msg="Incorrectly named key." \
                            "  Desired name: Foo; only found  %s." %
                            (" ".join(attributes.keys())))
        self.assertTrue(attributes['Foo'] == 'value1',
                        msg="Incorrect value wanted value1, " \
                            "got %s" % attributes['Foo'])
        self.assertTrue('bar' in attributes and attributes['bar'] == 'value2',
                        msg="Incorrectly named key." \
                            "  Desired name: bar; only found  %s." %
                            (" ".join(attributes.keys())))
        self.assertTrue('bar' in attributes and attributes['bar'] == 'value2',
                        msg="Incorrect value wanted value2, " \
                            "got %s" % attributes['bar'])

    def test_allowed_vos(self):
        """
        Make sure the allowed VOs is filtered properly.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/allowed_vos.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

    def test_allowed_jobmanagers(self):
        """
        Make sure the allowed VOs is filtered properly.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/allowed_jobmanager1.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/allowed_jobmanager2.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/allowed_jobmanager3.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/allowed_jobmanager4.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/allowed_jobmanager5.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/allowed_jobmanager6.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config._parse_configuration(config_parser)
        gip_config._parse_configuration_ce(config_parser)

        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/invalid_jobmanager1.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        self.failUnlessRaises(exceptions.SettingError,
                              gip_config._parse_configuration,
                              configuration=config_parser)

    def test_mount_point_valid(self):
        """
        Make sure we pass validation for a valid mount_point specification
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/mount_point.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.check_se(config_parser, "SE Valid")
        except exceptions.SettingError:
            did_fail = True
        self.assertFalse(did_fail, msg="Improperly rejected a valid SE.")

    def test_mount_point_wrong_len(self):
        """
        Make sure that if the incorrect number of paths were specified
        for mount_point, then an exception is thrown
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/mount_point.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.check_se(config_parser, "SE Wrong len")
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail,
                        msg="Did not throw an exception for incorrect # " \
                            "of paths in mount_point")

    def test_mount_point_invalid_path1(self):
        """
        Make sure that if the first path is invalid, then an exception is thrown.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/mount_point.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.check_se(config_parser, "SE Invalid Path 1")
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail,
                        msg="Did not throw an exception for invalid first " \
                            "mount_point path.")

    def test_mount_point_invalid_path2(self):
        """
        Make sure that if the first path is invalid, then an exception is thrown.
        """
        did_fail = False
        try:
            config_parser = ConfigParser.SafeConfigParser()
            config_file = get_test_config("gip/mount_point.ini")
            config_parser.read(config_file)
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.check_se(config_parser, "SE Invalid Path 2")
        except exceptions.SettingError:
            did_fail = True
        self.assertTrue(did_fail,
                        msg="Did not throw an exception for invalid " \
                            "second mount_point path.")

    def test_hepspec_valid(self):
        """
        Make sure a valid HEPSPEC value is accepted.
        """
        did_fail = False
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/sc_samples.ini")
        config_parser.read(config_file)
        gip_config = gip.GipConfiguration(logger=global_logger)
        try:
            gip_config.check_sc(config_parser, "Subcluster Valid")
        except exceptions.SettingError:
            did_fail = True
        self.assertFalse(did_fail, msg="Valid HEPSPEC entry threw an exception.")

    def test_hepspec_invalid(self):
        """
        Make sure a invalid HEPSPEC value causes an error..
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/sc_samples.ini")
        config_parser.read(config_file)
        gip_config = gip.GipConfiguration(logger=global_logger)
        try:
            gip_config.check_sc(config_parser, "Subcluster Bad HEPSPEC")
        except exceptions.SettingError:
            pass
        else:
            self.fail(msg="Invalid HEPSPEC entry did not throw an exception.")
        try:
            gip_config.check_sc(config_parser, "Subcluster Formerly Bad Cores")
        except exceptions.SettingError:
            self.fail(msg="Formerly Bad Cores entry threw an exception")

    def test_no_name(self):
        """
        Make sure a missing name causes an error
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/sc_samples.ini")
        config_parser.read(config_file)
        gip_config = gip.GipConfiguration(logger=global_logger)
        self.assertRaises(exceptions.SettingError, gip_config.check_sc, config_parser, "Subcluster No Name")

    def test_user_check_invalid_user(self):
        """
        Check to make sure gip class will distinguish between valid and
        invalid users
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/invalid_user.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        self.assertRaises(exceptions.SettingError,
                          gip_config._parse_configuration,
                          config_parser)

    def test_user_check_valid_user(self):
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("gip/valid_user.ini")
        config_parser.read(config_file)
        config_parser.set('Install Locations',
                          'user_vo_map',
                          get_test_config(SAMPLE_VO_MAP_LOCATION))
        gip_config = gip.GipConfiguration(logger=global_logger)
        self.assertTrue(gip_config._parse_configuration(config_parser) is None,
                        "Flagged valid user as being missing")


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)

    unittest.main()
