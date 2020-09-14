""" Module to handle attributes and configuration for misc. sevices """

import re
import logging
import os
import shutil

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.baseconfiguration import BaseConfiguration

__all__ = ['MiscConfiguration']

GSI_AUTHZ_LOCATION = "/etc/grid-security/gsi-authz.conf"
LCMAPS_DB_LOCATION = "/etc/lcmaps.db"
LCMAPS_DB_TEMPLATES_LOCATION = "/usr/share/lcmaps/templates"
HTCONDOR_CE_CONFIG_FILE = '/etc/condor-ce/config.d/50-osg-configure.conf'

VALID_AUTH_METHODS = ['gridmap', 'local-gridmap', 'vomsmap']

class MiscConfiguration(BaseConfiguration):
    """Class to handle attributes and configuration related to miscellaneous services"""

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('MiscConfiguration.__init__ started')
        self.options = {'authorization_method':
                            configfile.Option(name='authorization_method',
                                              default_value='vomsmap'),
                        'all_fqans':
                            configfile.Option(name='all_fqans',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False),
                        'edit_lcmaps_db':
                            configfile.Option(name='edit_lcmaps_db',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=True),
                        'copy_host_cert_for_service_certs':
                            configfile.Option(name='copy_host_cert_for_service_certs',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False)}
        self.config_section = "Misc Services"
        self.htcondor_gateway_enabled = True
        self.authorization_method = None
        self.log('MiscConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """
        Try to get configuration information from ConfigParser or SafeConfigParser
        object given by configuration and write recognized settings to options dict
        """
        self.log('MiscConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.enabled = False
            self.log("%s section not in config files" % self.config_section)
            self.log('MiscConfiguration.parse_configuration completed')
            return

        self.enabled = True
        self.get_options(configuration)

        self.htcondor_gateway_enabled = utilities.config_safe_getboolean(configuration, 'Gateway',
                                                                         'htcondor_gateway_enabled', True)
        self.authorization_method = self.options['authorization_method'].value
        self.all_fqans = self.options['all_fqans'].value

        self.log('MiscConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('MiscConfiguration.check_attributes started')
        attributes_ok = True

        if not self.enabled:
            self.log('Not enabled, returning True')
            self.log('MiscConfiguration.check_attributes completed')
            return True

        if self.authorization_method not in VALID_AUTH_METHODS:
            self.log("Setting is not one of: " + ", ".join(VALID_AUTH_METHODS),
                     option='authorization_method',
                     section=self.config_section,
                     level=logging.ERROR)
            attributes_ok = False

        self.log('MiscConfiguration.check_attributes completed')
        return attributes_ok

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('MiscConfiguration.configure started')

        if not self.enabled:
            self.log('Not enabled')
            self.log('MiscConfiguration.configure completed')
            return True

        # run fetch-crl script
        if not utilities.fetch_crl():
            self.log("Error while running fetch-crl script", level=logging.ERROR)
            raise exceptions.ConfigureError('fetch-crl returned non-zero exit code')

        if self.authorization_method == 'gridmap':
            self._set_lcmaps_callout(False)
        elif self.authorization_method == 'local-gridmap':
            self.log("local-gridmap is a deprecated auth method -- use 'gridmap' instead",
                     level=logging.WARNING)
            self._set_lcmaps_callout(False)
        elif self.authorization_method == 'vomsmap':
            self._set_lcmaps_callout(True)
        else:
            assert False, "Invalid authorization_method should have been caught in check_attributes()"

        if self.options['edit_lcmaps_db'].value:
            self._write_lcmaps_file()
        else:
            self.log("Not updating lcmaps.db because edit_lcmaps_db is false",
                     level=logging.DEBUG)

        if self.htcondor_gateway_enabled and utilities.ce_installed():
            self.write_gridmap_to_htcondor_ce_config()

        self.log('MiscConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "Misc"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def _set_lcmaps_callout(self, enable):
        self.log("Updating " + GSI_AUTHZ_LOCATION, level=logging.INFO)

        if enable:
            gsi_contents = "globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout\n"
        else:
            gsi_contents = "#globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout\n"
        if not utilities.atomic_write(GSI_AUTHZ_LOCATION, gsi_contents):
            msg = "Error while writing to " + GSI_AUTHZ_LOCATION
            self.log(msg, level=logging.ERROR)
            raise exceptions.ConfigureError(msg)

    def _write_lcmaps_file(self):
        old_lcmaps_contents = utilities.read_file(LCMAPS_DB_LOCATION, default='')
        if old_lcmaps_contents and 'THIS FILE WAS WRITTEN BY OSG-CONFIGURE' not in old_lcmaps_contents:
            backup_path = LCMAPS_DB_LOCATION + '.pre-configure'
            self.log("Backing up %s to %s" % (LCMAPS_DB_LOCATION, backup_path), level=logging.INFO)
            if not utilities.atomic_write(backup_path, old_lcmaps_contents):
                msg = "Unable to back up old lcmaps.db to %s" % backup_path
                self.log(msg, level=logging.ERROR)
                raise exceptions.ConfigureError(msg)

        self.log("Writing " + LCMAPS_DB_LOCATION, level=logging.INFO)
        if self.authorization_method == 'gridmap' or self.authorization_method == 'local-gridmap':
            lcmaps_template_fn = 'lcmaps.db.gridmap'
        elif self.authorization_method == 'vomsmap':
            if self.all_fqans:
                lcmaps_template_fn = 'lcmaps.db.vomsmap.allfqans'
            else:
                lcmaps_template_fn = 'lcmaps.db.vomsmap'
        else:
            assert False

        lcmaps_template_path = os.path.join(LCMAPS_DB_TEMPLATES_LOCATION, lcmaps_template_fn)

        if not validation.valid_file(lcmaps_template_path):
            msg = "lcmaps.db template file not found at %s; ensure lcmaps-db-templates >= 1.6.6-1.8" \
                  " is installed or set edit_lcmaps_db=False" % lcmaps_template_path
            self.log(msg, level=logging.ERROR)
            raise exceptions.ConfigureError(msg)

        old_lcmaps_contents = utilities.read_file(LCMAPS_DB_LOCATION, default='')
        if old_lcmaps_contents and 'THIS FILE WAS WRITTEN BY OSG-CONFIGURE' not in old_lcmaps_contents:
            backup_path = LCMAPS_DB_LOCATION + '.pre-configure'
            self.log("Backing up %s to %s" % (LCMAPS_DB_LOCATION, backup_path), level=logging.INFO)
            try:
                shutil.copy2(LCMAPS_DB_LOCATION, backup_path)
            except EnvironmentError as err:
                msg = "Unable to back up old lcmaps.db: " + str(err)
                self.log(msg, level=logging.ERROR)
                raise exceptions.ConfigureError(msg)

        lcmaps_contents = utilities.read_file(lcmaps_template_path)
        lcmaps_contents = ("# THIS FILE WAS WRITTEN BY OSG-CONFIGURE AND WILL BE OVERWRITTEN ON FUTURE RUNS\n"
                           "# Set edit_lcmaps_db = False in the [%s] section of your OSG configuration to\n"
                           "# keep your changes.\n" % self.config_section
                           + lcmaps_contents)
        if not utilities.atomic_write(LCMAPS_DB_LOCATION, lcmaps_contents):
            msg = "Error while writing to " + LCMAPS_DB_LOCATION
            self.log(msg, level=logging.ERROR)
            raise exceptions.ConfigureError(msg)

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """

        if not self.enabled or self.ignored:
            return set()

        services = set()
        if utilities.rpm_installed('fetch-crl'):
            services = {'fetch-crl-cron', 'fetch-crl-boot'}

        return services

    def write_gridmap_to_htcondor_ce_config(self):
        contents = utilities.read_file(HTCONDOR_CE_CONFIG_FILE,
                                       default="# This file is managed by osg-configure\n")
        if 'gridmap' not in self.authorization_method:
            # Remove GRIDMAP setting
            contents = re.sub(r'(?m)^\s*GRIDMAP\s*=.*?$[\n]?', "", contents)
        else:
            contents = utilities.add_or_replace_setting(contents, "GRIDMAP", "/etc/grid-security/grid-mapfile",
                                                        quote_value=False)
        utilities.atomic_write(HTCONDOR_CE_CONFIG_FILE, contents)
