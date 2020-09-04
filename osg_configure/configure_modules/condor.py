""" Module to handle attributes and configuration related to the condor 
jobmanager configuration """

import re
import os
import logging

from osg_configure.modules import utilities
from osg_configure.modules import validation
from osg_configure.modules import configfile
from osg_configure.modules.jobmanagerconfiguration import JobManagerConfiguration

__all__ = ['CondorConfiguration']


class CondorConfiguration(JobManagerConfiguration):
    """Class to handle attributes related to condor job manager configuration"""

    DEFAULT_LOCAL_CONFIG_DIR = '/etc/condor/config.d'

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('CondorConfiguration.__init__ started')
        self.config_section = "Condor"
        self.options = {'condor_location':
                            configfile.Option(name='condor_location',
                                              default_value=utilities.get_condor_location(),
                                              mapping='OSG_CONDOR_LOCATION'),
                        'condor_config':
                            configfile.Option(name='condor_config',
                                              required=configfile.Option.OPTIONAL,
                                              default_value=utilities.get_condor_config(),
                                              mapping='OSG_CONDOR_CONFIG')}
        self.condor_bin_location = None
        self.log('CondorConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """
        Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        super().parse_configuration(configuration)

        self.log('CondorConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.enabled = False
            self.log("%s section not in config file" % self.config_section)
            self.log('CondorConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('CondorConfiguration.parse_configuration completed')
            return True

        self.get_options(configuration, ignore_options=['enabled'])

        # set OSG_JOB_MANAGER and OSG_JOB_MANAGER_HOME
        self.options['job_manager'] = configfile.Option(name='job_manager',
                                                        value='Condor',
                                                        mapping='OSG_JOB_MANAGER')
        self.options['home'] = configfile.Option(name='job_manager_home',
                                                 value=self.options['condor_location'].value,
                                                 mapping='OSG_JOB_MANAGER_HOME')

        self.condor_bin_location = os.path.join(self.options['condor_location'].value, 'bin')

        self.log('CondorConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('CondorConfiguration.check_attributes started')

        if not self.enabled:
            self.log('CondorConfiguration.check_attributes completed returning True')
            return True

        if self.ignored:
            self.log('CondorConfiguration.check_attributes completed returning True')
            return True

        attributes_ok = True

        # make sure locations exist
        self.log('checking condor_location')
        if not validation.valid_location(self.options['condor_location'].value):
            attributes_ok = False
            self.log("Non-existent location given: %s" %
                     (self.options['condor_location'].value),
                     option='condor_location',
                     section=self.config_section,
                     level=logging.ERROR)

        if not validation.valid_directory(self.condor_bin_location):
            attributes_ok = False
            self.log("Given condor_location %r has no bin/ directory" % self.options['condor_location'].value,
                     option='condor_location',
                     section=self.config_section,
                     level=logging.ERROR)

        self.log('checking condor_config')
        if not validation.valid_file(self.options['condor_config'].value):
            attributes_ok = False
            self.log("Non-existent location given: %s" %
                     (self.options['condor_config'].value),
                     option='condor_config',
                     section=self.config_section,
                     level=logging.ERROR)

        self.log('CondorConfiguration.check_attributes completed returning %s' \
                 % attributes_ok)
        return attributes_ok

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('CondorConfiguration.configure started')

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log('CondorConfiguration.configure completed')
            return True

        if not self.enabled:
            self.log('condor not enabled')
            self.log('CondorConfiguration.configure completed')
            return True

        if self.htcondor_gateway_enabled:
            if not self.setup_htcondor_ce_config():
                self.log('Error writing to ' + JobManagerConfiguration.HTCONDOR_CE_CONFIG_FILE,
                         level=logging.ERROR)
                return False
            self.write_binpaths_to_blah_config('condor', self.condor_bin_location)
            self.write_htcondor_ce_sentinel()

        if not utilities.reconfig_service('condor', 'condor_reconfig'):
            self.log('Error reloading condor config', level=logging.WARNING)

        self.warn_on_non_default_local_config_dir()

        self.log('CondorConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "Condor"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def setup_htcondor_ce_config(self):
        """
        Populate the config file that tells htcondor-ce where the condor
        pool is and where the spool directory is.

        Returns True if successful, False otherwise
        """
        if not utilities.rpm_installed('htcondor-ce'):
            self.log("Unable to configure htcondor-ce for Condor: htcondor-ce not installed", level=logging.ERROR)
            return False

        def get_condor_ce_config_val(variable):
            return utilities.get_condor_config_val(variable, executable='condor_ce_config_val', quiet_undefined=True)

        # Get values for the settings we want to update. We can get the
        # values from condor_config_val; in the case of JOB_ROUTER_SCHEDD2_NAME,
        # we have FULL_HOSTNAME as a fallback in case SCHEDD_NAME is missing.
        # We also get the current / default value from condor_ce_config_val;
        # only update the setting in case the value from
        # condor_config_val is different from the value from condor_ce_config_val.
        condor_ce_config = {}
        for condor_ce_config_key, condor_config_keys in [
            ('JOB_ROUTER_SCHEDD2_NAME', ['SCHEDD_NAME', 'FULL_HOSTNAME']),
            ('JOB_ROUTER_SCHEDD2_POOL', ['COLLECTOR_HOST']),
            ('JOB_ROUTER_SCHEDD2_SPOOL', ['SPOOL'])]:

            condor_config_value = None
            for condor_config_value in (utilities.get_condor_config_val(k, quiet_undefined=True) for k in
                                        condor_config_keys):
                if condor_config_value:
                    break

            condor_ce_config_value = get_condor_ce_config_val(condor_ce_config_key)
            if not (condor_config_value or condor_ce_config_value):
                self.log("Unable to determine value for %s from %s and default not set; check your Condor config" %
                         (condor_ce_config_key, ' or '.join(condor_config_keys)), level=logging.ERROR)
                return False
            elif not condor_config_value:
                continue  # can't set anything for this

            # Special case for JOB_ROUTER_SCHEDD2_POOL: append port if necessary (SOFTWARE-1744)
            if condor_ce_config_key == 'JOB_ROUTER_SCHEDD2_POOL':
                condor_collector_port = (utilities.get_condor_config_val('COLLECTOR_PORT', quiet_undefined=True)
                                         or '9618')
                condor_config_value = self._add_port_if_necessary(condor_config_value, condor_collector_port)

            if not condor_ce_config_value or condor_ce_config_value != condor_config_value:
                condor_ce_config[condor_ce_config_key] = condor_config_value

        if condor_ce_config:
            buf = utilities.read_file(JobManagerConfiguration.HTCONDOR_CE_CONFIG_FILE,
                                      default="# This file is managed by osg-configure\n")
            for key, value in condor_ce_config.items():
                buf = utilities.add_or_replace_setting(buf, key, value, quote_value=False)

            if not utilities.atomic_write(JobManagerConfiguration.HTCONDOR_CE_CONFIG_FILE, buf):
                return False

        return True

    @staticmethod
    def _add_port_if_necessary(hoststr, port):
        assert port
        colon_count = hoststr.count(':')
        if colon_count == 0:
            # hostname or ipv4 address without port
            return '%s:%s' % (hoststr, port)
        elif colon_count == 1:
            # hostname or ipv4 address with port
            return hoststr
        elif colon_count > 1:
            # ipv6 address, must be bracketed if it has a port at the end, i.e. [ADDR]:PORT
            if ']:' not in hoststr:
                # no port
                # take off the brackets if they're already there so we don't get double
                hoststr_no_brackets = hoststr.lstrip('[').rstrip(']')
                return '[%s]:%s' % (hoststr_no_brackets, port)
            else:
                return hoststr

    def warn_on_non_default_local_config_dir(self):
        """Warn the user if the default condor local config dir
        (/etc/condor/config.d) is not searched by their Condor install,
        i.e. is not in the LOCAL_CONFIG_DIR variable.  (Note that despite
        the name, LOCAL_CONFIG_DIR may be a list).

        """
        real_default_local_config_dir = os.path.realpath(self.DEFAULT_LOCAL_CONFIG_DIR)

        if not os.path.exists(real_default_local_config_dir):
            self.log("%s does not exist; check your Condor installation" % self.DEFAULT_LOCAL_CONFIG_DIR,
                     level=logging.WARNING)
            return

        local_config_dir = utilities.get_condor_config_val('LOCAL_CONFIG_DIR', quiet_undefined=True)
        if not local_config_dir:
            self.log("LOCAL_CONFIG_DIR cannot be determined; check your Condor config", level=logging.WARNING)
            return

        # does not handle dir names with spaces or commas but apparently neither does condor
        real_local_config_dirs = [os.path.realpath(x) for x in re.split('[, ]+', local_config_dir)]
        if real_default_local_config_dir not in real_local_config_dirs:
            self.log("%s not found in LOCAL_CONFIG_DIR; this may cause failures with gratia and htcondor-ce."
                     " Check your Condor config" % self.DEFAULT_LOCAL_CONFIG_DIR,
                     level=logging.WARNING)
            return

    @staticmethod
    def get_condor_location(configuration):
        """
        Get the condor location based on the information in a configParser
        object (configuration argument) and environment variables if possible
        """

        location = configfile.Option(name='condor_location',
                                     default_value=utilities.get_condor_location())
        configfile.get_option(configuration, 'Condor', location)
        return location.value

    @staticmethod
    def get_condor_config(configuration):
        """
        Get the condor config location based on the information in a configParser
        object (configuration argument) and environment variables if possible
        """

        location = configfile.Option(name='condor_config',
                                     required=configfile.Option.OPTIONAL,
                                     default_value=utilities.get_condor_config())
        configfile.get_option(configuration, 'Condor', location)
        return location.value

    def enabled_services(self):
        """Return a list of system services needed for module to work
        """
        if not self.enabled or self.ignored:
            return set()

        return {'globus-gridftp-server'}.union(self.gateway_services())
