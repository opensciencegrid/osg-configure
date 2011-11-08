#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions

pathname = os.path.join('../scripts', 'osg-configure')
pathname = os.path.abspath(pathname)

global_logger = logging.getLogger('test gip configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

try:
    has_configure_osg = False
    fp = open(pathname, 'r')
    configure_osg = imp.load_module('osg-configure', fp, pathname, ('', '', 1))
    has_configure_osg = True
except:
    raise

from osg_configure.configure_modules import gip, localsettings
from osg_configure.configure_modules import localsettings

from osg_configure.modules import exceptions
from osg_configure.modules import configfile

class TestConfigureOsg(unittest.TestCase):

    def test_configure_osg(self):
        """
        Test to see if the configure_osg module properly loaded
        """
        self.failUnless(has_configure_osg, msg="osg-configure failed to " \
            "load.")


    def test_missing_sc(self):
        """
        Make sure that we have failures when there is no configured SC.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/red-missing-sc.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not properly detect a missing SC.")

    def test_missing_se(self):
        """
        Make sure that we have failures when there is no configured SE and there
        is no classic SE.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/red-missing-se.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not properly detect a missing SE.")

    def test_missing_se2(self):
        """
        Make sure that we have no when there is no configured SE and there
        is a classic SE.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/red-missing-se2.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failIf(did_fail, msg="Did not properly detect a missing SE.")

    def test_changeme1(self):
        """
        Test should pass if SE CHANGEME section is disabled.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/changeme_section.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failIf(did_fail, msg="Falsely detected an enabled CHANGEME section.")

    def test_changeme2(self):
        """
        Test should fail because SE CHANGEME section is enabled.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/changeme_section_bad.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not detect SE CHANGEME section.")

    def test_changeme3(self):
        """
        Test should fail because SE CHANGEME section is enabled.
        Variant 2.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/changeme_section_bad2.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not detect enabled CHANGEME section.")

    def test_changeme4(self):
        """
        Test should fail because SC CHANGEME section is present.
        
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/changeme_section_sc.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not detect enabled CHANGEME section.")

    def test_changeme5(self):
        """
        Test should not fail because SE CHANGEME section is disabled.
        Variant 2.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/changeme_section_bad3.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failIf(did_fail, msg="Falsely detected an enabled CHANGEME section.")

    def test_missing_attributes(self):
        """
        Make sure that we have failures when there are missing attributes.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/" \
                "red-missing-attributes.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.parseConfiguration(cp)
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not properly detect missing attrs.")

    def test_old_config(self):
        """
        Make sure that we can correctly parse an old-style GIP config.
        """
        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/red-old-gip-config.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

    def test_new_config(self):
        """
        Make sure that we can correctly parse a correct new-style GIP config.
        """
        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/red-new-gip-config.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

    def test_doherty(self):
        """
        Make sure that we can correctly parse a correct new-style GIP config.
        """
        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/doherty.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

    def test_local_settings(self):
        """
        Test to see if the local settings parsing works.
        """
        cp = ConfigParser.SafeConfigParser()
        cp.optionxform = str
        cp.read("configs/gip/local_settings.ini")        
        local_settings = localsettings.LocalSettings(logger = \
                                                     global_logger)
        local_settings.parseConfiguration(cp)
        attributes = local_settings.getAttributes()
        self.failUnless('default' not in attributes,
                        msg="Attributes set that weren't in the test config file")
        self.failUnless('Foo' in attributes and attributes['Foo'] == 'value1', 
                        msg="Incorrectly named key."\
                        "  Desired name: Foo; only found  %s."  % 
                        (" ".join(attributes.keys())))
        self.failUnless(attributes['Foo'] == 'value1', 
                        msg="Incorrect value wanted value1, " \
                        "got %s" % attributes['Foo'])
        self.failUnless('bar' in attributes and attributes['bar'] == 'value2', 
                        msg="Incorrectly named key."\
                        "  Desired name: bar; only found  %s."  % 
                        (" ".join(attributes.keys())))
        self.failUnless('bar' in attributes and attributes['bar'] == 'value2', 
                        msg="Incorrect value wanted value2, " \
                        "got %s" % attributes['bar'])

    def test_allowed_vos(self):
        """
        Make sure the allowed VOs is filtered properly.
        """
        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/allowed_vos.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

    def test_allowed_jobmanagers(self):
        """
        Make sure the allowed VOs is filtered properly.
        """
        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/allowed_jobmanager1.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/allowed_jobmanager2.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/allowed_jobmanager3.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/allowed_jobmanager4.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/allowed_jobmanager5.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/allowed_jobmanager6.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        gip_config.parseConfiguration(cp)

        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/invalid_jobmanager1.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        self.failUnlessRaises(exceptions.SettingError, 
                              gip_config.parseConfiguration, 
                              configuration = cp)


    def test_mount_point_valid(self):
        """
        Make sure we pass validation for a valid mount_point specification
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/mount_point.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.checkSE(cp, "SE Valid")
        except exceptions.SettingError:
            did_fail = True
        self.failIf(did_fail, msg="Improperly rejected a valid SE.")

    def test_mount_point_wrong_len(self):
        """
        Make sure that if the incorrect number of paths were specified
        for mount_point, then an exception is thrown
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/mount_point.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.checkSE(cp, "SE Wrong len")
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not throw an exception for incorrect # of paths in mount_point")

    def test_mount_point_invalid_path1(self):
        """ 
        Make sure that if the first path is invalid, then an exception is thrown.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/mount_point.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.checkSE(cp, "SE Invalid Path 1")
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not throw an exception for invalid first mount_point path.")

    def test_mount_point_invalid_path2(self):
        """ 
        Make sure that if the first path is invalid, then an exception is thrown.
        """
        did_fail = False
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.read("configs/gip/mount_point.ini")
            gip_config = gip.GipConfiguration(logger=global_logger)
            gip_config.checkSE(cp, "SE Invalid Path 2")
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Did not throw an exception for invalid second mount_point path.")

    def test_hepspec_valid(self):
        """
        Make sure a valid HEPSPEC value is accepted.
        """
        did_fail = False
        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/sc_samples.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        try:
            gip_config.checkSC(cp, "Subcluster Valid")
        except exceptions.SettingError:
            did_fail = True
        self.failIf(did_fail, msg="Valid HEPSPEC entry threw an exception.")

    def test_hepspec_invalid(self):
        """
        Make sure a invalid HEPSPEC value causes an error..
        """
        did_fail = False
        cp = ConfigParser.SafeConfigParser()
        cp.read("configs/gip/sc_samples.ini")
        gip_config = gip.GipConfiguration(logger=global_logger)
        try:
            gip_config.checkSC(cp, "Subcluster Bad HEPSPEC")
        except exceptions.SettingError:
            did_fail = True
        self.failUnless(did_fail, msg="Invalid HEPSPEC entry did not throw an exception.")


if __name__ == '__main__':
    unittest.main()

