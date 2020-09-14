""" Module to handle site specific local settings """

import logging
import re
from osg_configure.modules.baseconfiguration import BaseConfiguration
from osg_configure.modules.exceptions import SettingError

__all__ = ['LocalSettings']


class LocalSettings(BaseConfiguration):
    """Class to handle site specific local settings"""

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('LocalSettings.__init__ started')
        self.config_section = 'Local Settings'
        self.attributes = {}
        self.log('LocalSettings.__init__ completed')

    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        self.log('LocalSettings.parse_configuration started')

        self.check_config(configuration)

        # Parser preserves case so need to create a mapping between normalized sections
        # and actual names to find if this section is present
        sections = configuration.sections()
        section_map = {}
        for section in sections:
            section_map[section.lower()] = section

        if not self.config_section.lower() in section_map:
            self.log("%s section not found in config file" % self.config_section)
            return
        else:
            section_name = section_map[self.config_section.lower()]

        # variables from default section appear, so we need to cross reference
        # the ini defaults and then skip the variable if it also appears in the
        # defaults section
        for (name, value) in configuration.items(section_name):
            self.log("Found %s key with value %s" % (name, value))
            if name in configuration.defaults():
                self.log("%s is a default, skipping" % (name))
                continue
            # Validate name because it will be used as the name of an env var
            if not re.match(r"[A-Za-z_][A-Za-z0-9_]*$", name):
                raise SettingError("Invalid variable name " + name)
            # Values are already double-quoted so adding quotes would be a syntax error
            if value.startswith('"') or value.rstrip().endswith('"'):
                raise SettingError("Value for " + name + " should not be quoted")
            self.attributes[name] = value
        self.log('LocalSettings.parse_configuration completed')

    def module_name(self):
        """Return a string with the name of the module"""
        return "LocalSettings"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def get_attributes(self, converter=str):
        """
        Need to override because this class doesn't use the self.options to store
        a dictionary with ConfigOption objects
        """
        return self.attributes
