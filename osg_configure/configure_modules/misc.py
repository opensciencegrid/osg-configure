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
GUMS_CLIENT_LOCATION = "/etc/gums/gums-client.properties"
LCMAPS_DB_LOCATION = "/etc/lcmaps.db"
LCMAPS_DB_TEMPLATES_LOCATION = "/usr/share/lcmaps/templates"
HTCONDOR_CE_CONFIG_FILE = '/etc/condor-ce/config.d/50-osg-configure.conf'

VALID_AUTH_METHODS = ['gridmap', 'local-gridmap', 'xacml', 'vomsmap']

IGNORED_OPTIONS = [
    'enable_cleanup',
    'cleanup_age_in_days',
    'cleanup_users_list',
    'cleanup_cron_time'
]

class MiscConfiguration(BaseConfiguration):
    """Class to handle attributes and configuration related to miscellaneous services"""

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(MiscConfiguration, self).__init__(*args, **kwargs)
        self.log('MiscConfiguration.__init__ started')
        self.options = {'glexec_location':
                            configfile.Option(name='glexec_location',
                                              required=configfile.Option.OPTIONAL),
                        'gums_host':
                            configfile.Option(name='gums_host',
                                              required=configfile.Option.OPTIONAL),
                        'authorization_method':
                            configfile.Option(name='authorization_method',
                                              default_value='vomsmap'),
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
        self.get_options(configuration, ignore_options=IGNORED_OPTIONS)

        self.htcondor_gateway_enabled = utilities.config_safe_getboolean(configuration, 'Gateway',
                                                                         'htcondor_gateway_enabled', True)
        self.authorization_method = self.options['authorization_method'].value
        self.using_glexec = not utilities.blank(self.options['glexec_location'].value)

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

        if self.authorization_method == 'xacml':
            gums_host = self.options['gums_host'].value
            if utilities.blank(gums_host):
                self.log("Gums host not given",
                         section=self.config_section,
                         option='gums_host',
                         level=logging.ERROR)
                attributes_ok = False
            elif not validation.valid_domain(gums_host, resolve=True):
                self.log("Gums host not a valid domain name or does not resolve",
                         section=self.config_section,
                         option='gums_host',
                         level=logging.ERROR)
                attributes_ok = False
            self.log("Gums is deprecated in OSG 3.4. The replacement is the LCMAPS VOMS plugin; please see"
                     " installation instructions at"
                     " https://twiki.opensciencegrid.org/bin/view/Documentation/Release3/InstallLcmapsVoms",
                     section=self.config_section,
                     option='authorization_method',
                     level=logging.WARNING)

        if self.using_glexec:
            msg = "glExec is not supported in OSG 3.4; unset glexec_location"
            self.log(msg, options='glexec_location', section=self.config_section, level=logging.ERROR)
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

        if self.authorization_method == 'xacml':
            self._set_lcmaps_callout(True)
            self._update_gums_client_location()
        elif self.authorization_method == 'gridmap':
            self._set_lcmaps_callout(False)
        elif self.authorization_method == 'local-gridmap':
            self._set_lcmaps_callout(False)
        elif self.authorization_method == 'vomsmap':
            self._set_lcmaps_callout(True)
        else:
            self.log("Unknown authorization method: %s; should be one of: %s" %
                     (self.authorization_method, ", ".join(VALID_AUTH_METHODS)),
                     option='authorization_method',
                     section=self.config_section,
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Invalid authorization_method option in Misc Services")

        if self.options['edit_lcmaps_db'].value:
            self._write_lcmaps_file()
        else:
            self.log("Not updating lcmaps.db because edit_lcmaps_db is false",
                     level=logging.DEBUG)

        if self.htcondor_gateway_enabled:
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

    def _update_gums_client_location(self):
        self.log("Updating " + GUMS_CLIENT_LOCATION, level=logging.INFO)
        location_re = re.compile("^gums.location=.*$", re.MULTILINE)
        authz_re = re.compile("^gums.authz=.*$", re.MULTILINE)
        if not validation.valid_file(GUMS_CLIENT_LOCATION):
            gums_properties = "gums.location=https://%s:8443" % (self.options['gums_host'].value)
            gums_properties += "/gums/services/GUMSAdmin\n"
            gums_properties += "gums.authz=https://%s:8443" % (self.options['gums_host'].value)
            gums_properties += "/gums/services/GUMSXACMLAuthorizationServicePort"
        else:
            gums_properties = open(GUMS_CLIENT_LOCATION).read()
            replacement = "gums.location=https://%s:8443" % (self.options['gums_host'].value)
            replacement += "/gums/services/GUMSAdmin"
            gums_properties = location_re.sub(replacement, gums_properties)
            replacement = "gums.authz=https://%s:8443" % (self.options['gums_host'].value)
            replacement += "/gums/services/GUMSXACMLAuthorizationServicePort"
            gums_properties = authz_re.sub(replacement, gums_properties)
        utilities.atomic_write(GUMS_CLIENT_LOCATION, gums_properties)

    def _write_lcmaps_file(self):
        old_lcmaps_contents = utilities.read_file(LCMAPS_DB_LOCATION, default='')
        if old_lcmaps_contents and 'THIS FILE WAS WRITTEN BY OSG-CONFIGURE' not in old_lcmaps_contents:
            backup_path = LCMAPS_DB_LOCATION + '.pre-configure'
            self.log("Backing up %s to %s" % (LCMAPS_DB_LOCATION, backup_path), level=logging.WARNING)
            if not utilities.atomic_write(backup_path, old_lcmaps_contents):
                msg = "Unable to back up old lcmaps.db to %s" % backup_path
                self.log(msg, level=logging.ERROR)
                raise exceptions.ConfigureError(msg)

        self.log("Writing " + LCMAPS_DB_LOCATION, level=logging.INFO)
        if self.authorization_method == 'xacml':
            lcmaps_template_fn = 'lcmaps.db.gums'
        elif self.authorization_method == 'gridmap' or self.authorization_method == 'local-gridmap':
            lcmaps_template_fn = 'lcmaps.db.gridmap'
        elif self.authorization_method == 'vomsmap':
            lcmaps_template_fn = 'lcmaps.db.vomsmap'
        else:
            assert False

        lcmaps_template_path = os.path.join(LCMAPS_DB_TEMPLATES_LOCATION, lcmaps_template_fn)

        if not validation.valid_file(lcmaps_template_path):
            msg = "lcmaps.db template file not found at %s; ensure lcmaps-db-templates is installed or set"\
                  " edit_lcmaps_db=False" % lcmaps_template_path
            self.log(msg, level=logging.ERROR)
            raise exceptions.ConfigureError(msg)

        old_lcmaps_contents = utilities.read_file(LCMAPS_DB_LOCATION, default='')
        if old_lcmaps_contents and 'THIS FILE WAS WRITTEN BY OSG-CONFIGURE' not in old_lcmaps_contents:
            backup_path = LCMAPS_DB_LOCATION + '.pre-configure'
            self.log("Backing up %s to %s" % (LCMAPS_DB_LOCATION, backup_path), level=logging.WARNING)
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
                           + lcmaps_contents.replace('@GUMSHOST@', str(self.options['gums_host'].value)))
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
            services = set(['fetch-crl-cron', 'fetch-crl-boot'])

        if self.authorization_method == 'xacml':
            services.add('gums-client-cron')
        elif self.authorization_method == 'gridmap':
            services.add('edg-mkgridmap')
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
