""" Module to handle attributes related to the lsf jobmanager 
configuration """

import os
import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['LSFConfiguration']


class LSFConfiguration(JobManagerConfiguration):
    """Class to handle attributes related to lsf job manager configuration"""

    LSF_CONFIG_FILE = '/etc/grid-services/available/jobmanager-lsf-seg'
    GRAM_CONFIG_FILE = '/etc/globus/globus-lsf.conf'

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(LSFConfiguration, self).__init__(*args, **kwargs)
        self.log('LSFConfiguration.__init__ started')
        # dictionary to hold information about options
        self.options = {'lsf_location':
                            configfile.Option(name='lsf_location',
                                              default_value='/usr',
                                              mapping='OSG_LSF_LOCATION'),
                        'lsf_profile':
                            configfile.Option(name='lsf_profile',
                                              default_value=''),
                        'lsf_conf':
                            configfile.Option(name='lsf_conf',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='/etc'),
                        'job_contact':
                            configfile.Option(name='job_contact',
                                              mapping='OSG_JOB_CONTACT'),
                        'util_contact':
                            configfile.Option(name='util_contact',
                                              mapping='OSG_UTIL_CONTACT'),
                        'seg_enabled':
                            configfile.Option(name='seg_enabled',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False),
                        'log_directory':
                            configfile.Option(name='log_directory',
                                              required=configfile.Option.OPTIONAL,
                                              default_value=''),
                        'accept_limited': configfile.Option(name='accept_limited',
                                                            required=configfile.Option.OPTIONAL,
                                                            opt_type=bool,
                                                            default_value=False)}
        self.config_section = 'LSF'
        self.lsf_bin_location = None
        self._set_default = True

        self.log('LSFConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        super(LSFConfiguration, self).parse_configuration(configuration)

        self.log('LSFConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.enabled = False
            self.log('LSF section not found in config file')
            self.log('LSFConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('LSFConfiguration.parse_configuration completed')
            return True

        self.get_options(configuration, ignore_options=['enabled'])

        # set OSG_JOB_MANAGER_HOME
        # set OSG_JOB_MANAGER and OSG_JOB_MANAGER_HOME
        self.options['job_manager'] = configfile.Option(name='job_manager',
                                                        value='LSF',
                                                        mapping='OSG_JOB_MANAGER')
        self.options['home'] = configfile.Option(name='job_manager_home',
                                                 value=self.options['lsf_location'].value,
                                                 mapping='OSG_JOB_MANAGER_HOME')

        if (configuration.has_section('Managed Fork') and
                configuration.has_option('Managed Fork', 'enabled') and
                configuration.getboolean('Managed Fork', 'enabled')):
            self._set_default = False

        self.lsf_bin_location = os.path.join(self.options['lsf_location'].value, 'bin')

        self.log('LSFConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('LSFConfiguration.check_attributes started')

        attributes_ok = True

        if not self.enabled:
            self.log('LSF not enabled, returning True')
            self.log('LSFConfiguration.check_attributes completed')
            return attributes_ok

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('LSFConfiguration.check_attributes completed')
            return attributes_ok


        # make sure locations exist
        if not validation.valid_location(self.options['lsf_location'].value):
            attributes_ok = False
            self.log("Non-existent location given: %s" %
                     (self.options['lsf_location'].value),
                     option='lsf_location',
                     section=self.config_section,
                     level=logging.ERROR)

        if not validation.valid_directory(self.lsf_bin_location):
            attributes_ok = False
            self.log("Given lsf_location %r has no bin/ directory" % self.options['lsf_location'].value,
                     option='lsf_location',
                     section=self.config_section,
                     level=logging.ERROR)

        if self.options['lsf_conf'].value and not validation.valid_directory(self.options['lsf_conf'].value):
            attributes_ok = False
            self.log("Non-existent directory given: %s" %
                     (self.options['lsf_conf'].value),
                     option='lsf_conf',
                     section=self.config_section,
                     level=logging.ERROR)

        if not validation.valid_file(self.options['lsf_profile'].value):
            attributes_ok = False
            self.log("Non-existent location given: %s" %
                     (self.options['lsf_profile'].value),
                     option='lsf_profile',
                     section=self.config_section,
                     level=logging.ERROR)

        if not validation.valid_contact(self.options['job_contact'].value,
                                        'lsf'):
            attributes_ok = False
            self.log("Invalid job contact: %s" %
                     (self.options['job_contact'].value),
                     option='job_contact',
                     section=self.config_section,
                     level=logging.ERROR)

        if not validation.valid_contact(self.options['util_contact'].value,
                                        'lsf'):
            attributes_ok = False
            self.log("Invalid util contact: %s" %
                     (self.options['util_contact'].value),
                     option='util_contact',
                     section=self.config_section,
                     level=logging.ERROR)

        self.log('LSFConfiguration.check_attributes completed')
        return attributes_ok

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('LSFConfiguration.configure started')

        if not self.enabled:
            self.log('LSF not enabled, returning True')
            self.log('LSFConfiguration.configure completed')
            return True

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log('LSFConfiguration.configure completed')
            return True

        if self.gram_gateway_enabled:

            # The accept_limited argument was added for Steve Timm.  We are not adding
            # it to the default config.ini template because we do not think it is
            # useful to a wider audience.
            # See VDT RT ticket 7757 for more information.
            if self.options['accept_limited'].value:
                if not self.enable_accept_limited(LSFConfiguration.LSF_CONFIG_FILE):
                    self.log('Error writing to ' + LSFConfiguration.LSF_CONFIG_FILE,
                             level=logging.ERROR)
                    self.log('LSFConfiguration.configure completed')
                    return False
            elif self.options['accept_limited'].value:
                if not self.disable_accept_limited(LSFConfiguration.LSF_CONFIG_FILE):
                    self.log('Error writing to ' + LSFConfiguration.LSF_CONFIG_FILE,
                             level=logging.ERROR)
                    self.log('LSFConfiguration.configure completed')
                    return False

            if not self.options['seg_enabled'].value:
                self.log("SEG must be enabled for LSF jobmanager",
                         option='seg_enabled',
                         section=self.config_section,
                         level=logging.ERROR)
            self.enable_seg('lsf', LSFConfiguration.LSF_CONFIG_FILE)

            if not self.setup_gram_config():
                self.log('Error writing to ' + LSFConfiguration.GRAM_CONFIG_FILE,
                         level=logging.ERROR)
                return False

            if self._set_default:
                self.log('Configuring gatekeeper to use regular fork service')
                self.set_default_jobmanager('fork')

        if self.htcondor_gateway_enabled:
            self.write_binpaths_to_blah_config('lsf', self.lsf_bin_location)
            self.write_blah_disable_wn_proxy_renewal_to_blah_config()
            self.write_htcondor_ce_sentinel()
            if not self.reconfig_service('condor-ce', 'condor_ce_reconfig'):
                self.log('Error reloading condor-ce config', level=logging.WARNING)
            if self.options['lsf_conf'].value:
                self.write_lsf_confpath_to_blah_config()

        self.log('LSFConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "LSF"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def write_lsf_confpath_to_blah_config(self):
        if os.path.exists(self.BLAH_CONFIG):
            contents = utilities.read_file(self.BLAH_CONFIG)
            contents = utilities.add_or_replace_setting(contents, 'lsf_confpath', self.options['lsf_conf'].value,
                                                        quote_value=False)
            utilities.atomic_write(self.BLAH_CONFIG, contents)

    def setup_gram_config(self):
        """
        Populate the gram config file with correct values

        Returns True if successful, False otherwise
        """
        buf = open(LSFConfiguration.GRAM_CONFIG_FILE).read()
        for binfile in ['bsub', 'bqueues', 'bjobs', 'bhist', 'bacct', 'bkill']:
            bin_location = os.path.join(self.lsf_bin_location, binfile)
            if validation.valid_file(bin_location):
                buf = utilities.add_or_replace_setting(buf, binfile, 'bin_location')

        if self.options['seg_enabled'].value:
            if (self.options['log_directory'].value is None or
                    not validation.valid_directory(self.options['log_directory'].value)):
                mesg = "%s is not a valid directory location " % self.options['log_directory'].value
                mesg += "for lsf log files"
                self.log(mesg,
                         section=self.config_section,
                         option='log_directory',
                         level=logging.ERROR)
                return False

            buf = utilities.add_or_replace_setting(buf, 'log_path', self.options['log_directory'].value)

        buf = utilities.add_or_replace_setting(buf, 'lsf_profile', self.options['lsf_profile'].value)

        if not utilities.atomic_write(LSFConfiguration.GRAM_CONFIG_FILE, buf):
            return False
        return True

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """

        if not self.enabled or self.ignored:
            return set()

        services = set(['globus-gridftp-server'])
        services.update(self.gateway_services())
        if self.options['seg_enabled'].value:
            services.add('globus-scheduler-event-generator')
            services.add('globus-gatekeeper')
        return services
