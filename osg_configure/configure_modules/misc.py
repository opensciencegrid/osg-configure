""" Module to handle attributes and configuration for misc. sevices """

import re
import logging
import sys

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.baseconfiguration import BaseConfiguration

__all__ = ['MiscConfiguration']

GSI_AUTHZ_LOCATION = "/etc/grid-security/gsi-authz.conf"
GUMS_CLIENT_LOCATION = "/etc/gums/gums-client.properties"
LCMAPS_DB_LOCATION = "/etc/lcmaps.db"
USER_VO_MAP_LOCATION = '/var/lib/osg/user-vo-map'
HTCONDOR_CE_CONFIG_FILE = '/etc/condor-ce/config.d/50-osg-configure.conf'


class MiscConfiguration(BaseConfiguration):
    """Class to handle attributes and configuration related to miscellaneous services"""

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(MiscConfiguration, self).__init__(*args, **kwargs)
        self.log('MiscConfiguration.__init__ started')
        self.options = {'glexec_location':
                            configfile.Option(name='glexec_location',
                                              required=configfile.Option.OPTIONAL,
                                              mapping='OSG_GLEXEC_LOCATION'),
                        'gums_host':
                            configfile.Option(name='gums_host',
                                              required=configfile.Option.OPTIONAL),
                        'authorization_method':
                            configfile.Option(name='authorization_method',
                                              default_value='xacml'),
                        'edit_lcmaps_db':
                            configfile.Option(name='edit_lcmaps_db',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=True),
                        'enable_cleanup':
                            configfile.Option(name='enable_cleanup',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False),
                        'cleanup_age_in_days':
                            configfile.Option(name='cleanup_age_in_days',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=int,
                                              default_value=14),
                        'cleanup_users_list':
                            configfile.Option(name='cleanup_users_list',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='@vo-file'),
                        'cleanup_cron_time':
                            configfile.Option(name='cleanup_cron_time',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='15 1 * * *'),
                        'copy_host_cert_for_service_certs':
                            configfile.Option(name='copy_host_cert_for_service_certs',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False)}
        self.config_section = "Misc Services"
        self.htcondor_gateway_enabled = True
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

        if (self.options['authorization_method'].value not in \
                    ['gridmap', 'local-gridmap', 'xacml']):
            self.log("Setting is not xacml, or gridmap",
                     option='authorization_method',
                     section=self.config_section,
                     level=logging.ERROR)
            attributes_ok = False

        if self.options['authorization_method'].value == 'xacml':
            if utilities.blank(self.options['gums_host'].value):
                self.log("Gums host not given",
                         section=self.config_section,
                         option='gums_host',
                         level=logging.ERROR)
                attributes_ok = False

            if not validation.valid_domain(self.options['gums_host'].value):
                self.log("Gums host not a valid domain name",
                         section=self.config_section,
                         option='gums_host',
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

        using_gums = False
        if self.options['authorization_method'].value == 'xacml':
            using_gums = True
            self._enable_xacml()
        elif self.options['authorization_method'].value == 'gridmap':
            self._disable_callout()
        elif self.options['authorization_method'].value == 'local-gridmap':
            self._disable_callout()
        else:
            self.log("Unknown authorization method: %s" % \
                     self.options['authorization_method'].value,
                     option='authorization_method',
                     section=self.config_section,
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Invalid authorization_method option " +
                                            "in Misc Services")

        if self.options['edit_lcmaps_db'].value:
            if validation.valid_file(LCMAPS_DB_LOCATION):
                self._update_lcmaps_file(using_gums)
            else:
                self.log("Not updating lcmaps.db because it's not accessible",
                         level=logging.DEBUG)
        else:
            self.log("Not updating lcmaps.db because edit_lcmaps_db is false",
                     level=logging.DEBUG)

        if self.htcondor_gateway_enabled:
            self.write_gridmap_to_htcondor_ce_config()

        ensure_valid_user_vo_file(using_gums, logger=self.logger)
        # Call configure_vdt_cleanup (enabling or disabling as necessary)
        self._configure_cleanup()

        self.log('MiscConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "Misc"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def _enable_xacml(self):
        """
        Enable authorization services using xacml protocol
        """

        self.log("Updating " + GSI_AUTHZ_LOCATION, level=logging.INFO)

        gsi_contents = "globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout\n"
        if not utilities.atomic_write(GSI_AUTHZ_LOCATION, gsi_contents):
            self.log("Error while writing to " + GSI_AUTHZ_LOCATION,
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Error while writing to " +
                                            GSI_AUTHZ_LOCATION)

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

    def _update_lcmaps_file(self, gums=True):
        """
        Update lcmaps file and give appropriate messages if lcmaps.db.rpmnew exists
        """
        warning_message = """It appears that you've updated the lcmaps RPM and the
configuration has changed.
If you have ever edited /etc/lcmaps.db by hand (most people don't), then you
should:
   1. Edit /etc/lcmaps.db.rpmnew to make your changes again
   2. mv /etc/lcmaps.db.rpmnew /etc/lcmaps.db
If you haven't edited /etc/lcmaps.db by hand, then you can just use the new
configuration:
   1. mv /etc/lcmaps.db.rpmnew /etc/lcmaps.db"""

        files_to_update = [LCMAPS_DB_LOCATION]
        rpmnew_file = LCMAPS_DB_LOCATION + ".rpmnew"
        if validation.valid_file(rpmnew_file):
            self.log(warning_message, level=logging.WARNING)
            files_to_update.append(rpmnew_file)

        for lcmaps_db_file in files_to_update:
            self.log("Updating " + lcmaps_db_file, level=logging.INFO)
            lcmaps_db = open(lcmaps_db_file).read()

            lcmaps_db = self._update_lcmaps_text(lcmaps_db, gums, self.options['gums_host'].value)

            utilities.atomic_write(lcmaps_db_file, lcmaps_db)

    def _update_lcmaps_text(self, lcmaps_db, gums, gums_host):
        #
        # Update GUMS endpoint (if using GUMS)
        #
        if gums:
            endpoint_re = re.compile(r'^\s*"--endpoint\s+https://.*/gums/services.*"\s*?$',
                                     re.MULTILINE)
            replacement = "             \"--endpoint https://%s:8443" % (gums_host)
            replacement += "/gums/services/GUMSXACMLAuthorizationServicePort\""
            lcmaps_db = endpoint_re.sub(replacement, lcmaps_db)

        #
        # Update "authorize_only" section
        #
        addition_comment = ("\n"
                            "## Added by osg-configure\n"
                            "## Set 'edit_lcmaps_db=False' in the [%s] section of your OSG configs\n"
                            "## to keep osg-configure from modifying this file\n" %
                            self.config_section)

        # Split the string into three:
        # 1. Everything before the authorize_only section
        # 2. The authorize_only section (including the header 'authorize_only:')
        # 3. Everything after the authorize_only section (if present)
        #
        # The authorize_only section ends at the end of the file (\Z) or when
        # another section begins (^[ \t]*[a-zA-Z_]+:)
        authorize_only_re = re.compile(r'\A(.+)(^[ \t]*authorize_only:.+?)(^[ \t]*[a-zA-Z_]+:.+|\Z)',
                                       re.MULTILINE|re.DOTALL)
        match = authorize_only_re.search(lcmaps_db)

        if not match:
            self.log("No valid 'authorize_only' section in lcmaps.db; cannot update!",
                     level=logging.ERROR)
            raise exceptions.ConfigureError("No valid 'authorize_only' section in lcmaps.db")

        pre_authorize_only, authorize_only, post_authorize_only = match.group(1, 2, 3)

        # Look for lines like
        # "gumsclient -> good | bad" and
        # "gridmapfile -> good | bad"
        # which may be commented out.
        gumsclient_re = re.compile(r'^\s*?[#]*?\s*?gumsclient\s*?->\s*?good\s*?[|]\s*?bad\s*?$',
                                   re.MULTILINE)
        gridmapfile_re = re.compile(r'^\s*?[#]*?\s*?gridmapfile\s*?->\s*?good\s*?[|]\s*?bad\s*?$',
                                    re.MULTILINE)

        if gums:
            # Comment out gridmapfile line
            authorize_only = gridmapfile_re.sub("#gridmapfile -> good | bad", authorize_only)

            # If there's a gumsclient line, uncomment it. If not, add one to the end of the authorize_only section.
            authorize_only, changed = gumsclient_re.subn("gumsclient -> good | bad", authorize_only, count=1)
            if not changed:
                authorize_only += addition_comment
                authorize_only += "gumsclient -> good | bad\n"
                self.log("Added 'gumsclient' authorization method to authorize_only section of %s" % LCMAPS_DB_LOCATION,
                         level=logging.WARNING)
        else:
            # Comment out gumsclient line
            authorize_only = gumsclient_re.sub("#gumsclient -> good | bad", authorize_only)

            # If there's a gridmapfile line, uncomment it. If not, add one to the end of the authorize_only section.
            authorize_only, changed = gridmapfile_re.subn("gridmapfile -> good | bad", authorize_only, count=1)
            if not changed:
                authorize_only += addition_comment
                authorize_only += "gridmapfile -> good | bad\n"
                self.log("Added 'gridmapfile' authorization method to authorize_only section of %s" % LCMAPS_DB_LOCATION,
                         level=logging.WARNING)

        return pre_authorize_only + authorize_only + post_authorize_only

    def _disable_callout(self):
        """
        Enable authorization using gridmap files
        """
        self.log("Updating " + GSI_AUTHZ_LOCATION, level=logging.INFO)
        gsi_contents = "#globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout\n"
        if not utilities.atomic_write(GSI_AUTHZ_LOCATION, gsi_contents):
            self.log("Error while writing to " + GSI_AUTHZ_LOCATION,
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Error while writing to " +
                                            GSI_AUTHZ_LOCATION)

    def _configure_cleanup(self):
        """
        Configure osg-cleanup
        """

        # Do basic error checking to validate that this is a cron string
        if len(re.split(r'\s+', self.options['cleanup_cron_time'].value)) != 5:
            err_msg = "Error: the value of cleanup_cron_time must be a 5 part " \
                      "cron string: %s" % self.options['cleanup_cron_time'].value
            self.log(err_msg,
                     option='cleanup_cron_time',
                     section=self.config_section,
                     level=logging.ERROR)
            raise exceptions.ConfigureError(err_msg)

        filehandle = open('/etc/osg/osg-cleanup.conf', 'w')

        filehandle.write('# This file is automatically generated by osg-configure\n')
        filehandle.write('# Manual modifications to this file may be overwritten\n')
        filehandle.write('# Instead, modify /etc/osg/config.d/10-misc.ini\n')

        filehandle.write('age = %s\n' % (self.options['cleanup_age_in_days'].value))
        filehandle.write('users = %s\n' % (self.options['cleanup_users_list'].value))

        filehandle.close()

        # Writing this file seems a little hacky, but I'm not sure of a better way
        filehandle = open('/etc/cron.d/osg-cleanup', 'w')
        filehandle.write('%s root [ ! -f /var/lock/subsys/osg-cleanup-cron ] || /usr/sbin/osg-cleanup\n' %
                         (self.options['cleanup_cron_time'].value))
        filehandle.close()

        return True

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """

        if not self.enabled or self.ignored:
            return set()

        services = set()
        if utilities.rpm_installed('fetch-crl'):
            services = set(['fetch-crl-cron', 'fetch-crl-boot'])
        elif utilities.rpm_installed('fetch-crl3'):
            services = set(['fetch-crl3-cron', 'fetch-crl3-boot'])

        if self.options['authorization_method'].value == 'xacml':
            services.add('gums-client-cron')
        elif self.options['authorization_method'].value == 'gridmap':
            services.add('edg-mkgridmap')
        if self.options['enable_cleanup'].value:
            services.add('osg-cleanup-cron')
        return services

    def write_gridmap_to_htcondor_ce_config(self):
        contents = utilities.read_file(HTCONDOR_CE_CONFIG_FILE,
                                       default="# This file is managed by osg-configure\n")
        if self.options['authorization_method'].value == 'xacml':
            # Remove GRIDMAP setting
            contents = re.sub(r'(?m)^\s*GRIDMAP\s*=.*?$[\n]?', "", contents)
        else:
            contents = utilities.add_or_replace_setting(contents, "GRIDMAP", "/etc/grid-security/grid-mapfile",
                                                        quote_value=False)
        utilities.atomic_write(HTCONDOR_CE_CONFIG_FILE, contents)


def create_user_vo_file(using_gums=False):
    """
    Check and create a mapfile if needed
    """

    map_file = '/var/lib/osg/user-vo-map'
    try:
        if validation.valid_user_vo_file(map_file):
            return True
        if using_gums:
            gums_script = '/usr/bin/gums-host-cron'
        else:
            gums_script = '/usr/sbin/edg-mkgridmap'

        sys.stdout.write("Running %s, this process may take some time " % gums_script +
                         "to query vo and gums servers\n")
        sys.stdout.flush()
        if not utilities.run_script([gums_script]):
            return False
    except IOError:
        return False
    return True


def ensure_valid_user_vo_file(using_gums, logger=utilities.NullLogger):
    if not validation.valid_user_vo_file(USER_VO_MAP_LOCATION):
        logger.info("Trying to create user-vo-map file")
        result = create_user_vo_file(using_gums)
        temp, invalid_lines = validation.valid_user_vo_file(USER_VO_MAP_LOCATION, True)
        result = result and temp
        if not result:
            logger.error("Can't generate user-vo-map, manual intervention is needed")
            if not invalid_lines:
                logger.error("gums-host-cron or edg-mkgridmap generated an empty " +
                             USER_VO_MAP_LOCATION + " file, please check the "
                             "appropriate configuration and or log messages")
                raise exceptions.ConfigureError('Error when generating user-vo-map file')
            logger.error("Invalid lines in user-vo-map file:")
            logger.error("\n".join(invalid_lines))
            raise exceptions.ConfigureError("Error when invoking gums-host-cron or edg-mkgridmap")

