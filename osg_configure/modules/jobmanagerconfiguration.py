""" Base class for all job manager configuration classes """

from __future__ import absolute_import
import os
import logging

from osg_configure.modules.baseconfiguration import BaseConfiguration
from osg_configure.modules import utilities

__all__ = ['JobManagerConfiguration']


class JobManagerConfiguration(BaseConfiguration):
    """Base class for inheritance by jobmanager configuration classes"""
    HTCONDOR_CE_CONFIG_FILE = '/etc/condor-ce/config.d/50-osg-configure.conf'
    BLAH_CONFIG = '/etc/blah.config'

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(JobManagerConfiguration, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.attributes = {}
        self.htcondor_gateway_enabled = True

    def parse_configuration(self, configuration):
        super(JobManagerConfiguration, self).parse_configuration(configuration)
        self.log('JobManagerConfiguration.parse_configuration started')
        if configuration.has_section('Gateway'):
            if configuration.has_option('Gateway', 'htcondor_gateway_enabled'):
                self.htcondor_gateway_enabled = configuration.getboolean('Gateway', 'htcondor_gateway_enabled')
        self.log('JobManagerConfiguration.parse_configuration completed')

    def gateway_services(self):
        services = set([])
        if self.htcondor_gateway_enabled:
            services.add('condor-ce')
        return services

    def write_binpaths_to_blah_config(self, jobmanager, submit_binpath):
        """
        Change the *_binpath variables in /etc/blah.config for the given
        jobmanager to point to the locations specified by the user in the
        config for that jobmanager. Does not do anything if /etc/blah.config
        is missing (e.g. if blahp is not installed).
        :param jobmanager: The name of a job manager that has a _binpath
          variable in /etc/blah.config
        :param submit_binpath: The fully-qualified path to the submit
          executables for that jobmanager
        """
        if os.path.exists(self.BLAH_CONFIG):
            contents = utilities.read_file(self.BLAH_CONFIG)
            contents = utilities.add_or_replace_setting(contents, jobmanager + "_binpath", submit_binpath,
                                                        quote_value=True)
            utilities.atomic_write(self.BLAH_CONFIG, contents)

    def write_blah_disable_wn_proxy_renewal_to_blah_config(self):
        if os.path.exists(self.BLAH_CONFIG):
            contents = utilities.read_file(self.BLAH_CONFIG)
            for option, value in [("blah_disable_wn_proxy_renewal", "yes"),
                                  ("blah_delegate_renewed_proxies", "no"),
                                  ("blah_disable_limited_proxy", "yes")]:
                contents = utilities.add_or_replace_setting(contents, option, value,
                                                            quote_value=True)
            utilities.atomic_write(self.BLAH_CONFIG, contents)

    def write_htcondor_ce_sentinel(self):
        if self.htcondor_gateway_enabled and utilities.ce_installed():
            contents = utilities.read_file(self.HTCONDOR_CE_CONFIG_FILE,
                                           default="# This file is managed by osg-configure\n")
            contents = utilities.add_or_replace_setting(contents, "OSG_CONFIGURED", "true", quote_value=False)
            utilities.atomic_write(self.HTCONDOR_CE_CONFIG_FILE, contents)
