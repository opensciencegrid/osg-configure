""" Module to handle attributes related to the sge jobmanager configuration """

import os
import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.jobmanagerconfiguration import JobManagerConfiguration

__all__ = ['SGEConfiguration']


class SGEConfiguration(JobManagerConfiguration):
    """Class to handle attributes related to sge job manager configuration"""

    BLAH_CONFIG = JobManagerConfiguration.BLAH_CONFIG

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(SGEConfiguration, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('SGEConfiguration.__init__ started')
        # option information
        self.options = {'sge_root':
                            configfile.Option(name='sge_root',
                                              mapping='OSG_SGE_ROOT'),
                        'sge_cell':
                            configfile.Option(name='sge_cell',
                                              default_value='default',
                                              mapping='OSG_SGE_CELL'),
                        'sge_config':
                            configfile.Option(name='sge_config',
                                              default_value='/etc/sysconfig/gridengine'),
                        'sge_bin_location':
                            configfile.Option(name='sge_bin_location',
                                              default_value='default'),
                        'default_queue':
                            configfile.Option(name='default_queue',
                                              required=configfile.Option.OPTIONAL,
                                              default_value=''),
                        'validate_queues':
                            configfile.Option(name='validate_queues',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False),
                        'available_queues':
                            configfile.Option(name='available_queues',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='')}
        self.config_section = "SGE"
        self.log('SGEConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        super(SGEConfiguration, self).parse_configuration(configuration)

        self.log('SGEConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.log('SGE section not found in config file')
            self.log('SGEConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('SGEConfiguration.parse_configuration completed')
            return True

        self.get_options(configuration, ignore_options=['enabled'])

        # fill in values for sge_location and home
        self.options['job_manager'] = configfile.Option(name='job_manager',
                                                        value='SGE',
                                                        mapping='OSG_JOB_MANAGER')
        self.options['home'] = configfile.Option(name='job_manager_home',
                                                 value=self.options['sge_root'].value,
                                                 mapping='OSG_JOB_MANAGER_HOME')
        self.options['osg_sge_location'] = configfile.Option(name='sge_location',
                                                             value=self.options['sge_root'].value,
                                                             mapping='OSG_SGE_LOCATION')

        self.log('SGEConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('SGEConfiguration.check_attributes started')
        attributes_ok = True
        if not self.enabled:
            self.log('SGE not enabled, returning True')
            self.log('SGEConfiguration.check_attributes completed')
            return attributes_ok

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('SGEConfiguration.check_attributes completed')
            return attributes_ok

        # make sure locations exist
        if not validation.valid_location(self.options['sge_root'].value):
            attributes_ok = False
            self.log("Non-existent location given: %s" %
                     (self.options['sge_root'].value),
                     option='sge_root',
                     section=self.config_section,
                     level=logging.ERROR)

        settings_file = os.path.join(self.options['sge_root'].value,
                                     self.options['sge_cell'].value.lstrip("/"),
                                     'common/settings.sh')

        if not validation.valid_file(settings_file):
            attributes_ok = False
            self.log("$SGE_ROOT/$SGE_CELL/common/settings.sh not present: %s" %
                     settings_file,
                     option='sge_cell',
                     section=self.config_section,
                     level=logging.ERROR)

        if not validation.valid_directory(self.options['sge_bin_location'].value):
            attributes_ok = False
            self.log("sge_bin_location not valid: %s" % self.options['sge_bin_location'].value,
                     option='sge_bin_location',
                     section=self.config_section,
                     level=logging.ERROR)

        key = 'sge_config'
        if (not self.options[key].value or
                not validation.valid_file(self.options[key].value)):
            attributes_ok = False
            self.log("%s is not a valid file: %s" % (key, self.options[key].value),
                     section=self.config_section,
                     option=key,
                     level=logging.ERROR)

        self.log('SGEConfiguration.check_attributes completed')
        return attributes_ok

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('SGEConfiguration.configure started')

        if not self.enabled:
            self.log('SGE not enabled, returning True')
            self.log('SGEConfiguration.configure completed')
            return True

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log('SGEConfiguration.configure completed')
            return True

        if self.htcondor_gateway_enabled:
            self.setup_blah_config()
            self.write_binpaths_to_blah_config('sge', self.options['sge_bin_location'].value)
            self.write_blah_disable_wn_proxy_renewal_to_blah_config()
            self.write_htcondor_ce_sentinel()

        self.log('SGEConfiguration.configure started')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "SGE"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def setup_blah_config(self):
        """
        Populate blah.config with correct values

        Return True if successful, False otherwise
        """
        if os.path.exists(self.BLAH_CONFIG):
            contents = utilities.read_file(self.BLAH_CONFIG)
            contents = utilities.add_or_replace_setting(contents, "sge_rootpath", self.options['sge_root'].value,
                                                        quote_value=True)
            contents = utilities.add_or_replace_setting(contents, "sge_cellname", self.options['sge_cell'].value,
                                                        quote_value=True)
            return utilities.atomic_write(self.BLAH_CONFIG, contents)
        return False

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """
        if not self.enabled or self.ignored:
            return set()

        services = {'globus-gridftp-server'}
        services.update(self.gateway_services())
        return services

    def get_accounting_file(self):
        """
        Return the location of the SGE Accounting file
        """

        return os.path.join(self.options['sge_root'].value,
                            self.options['sge_cell'].value.lstrip("/"),
                            "common/accounting")
