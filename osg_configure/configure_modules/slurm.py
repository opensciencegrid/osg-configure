"""
Module to handle attributes related to the slurm jobmanager 
configuration
"""
import os
import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.jobmanagerconfiguration import JobManagerConfiguration

__all__ = ['SlurmConfiguration']


class SlurmConfiguration(JobManagerConfiguration):
    """Class to handle attributes related to SLURM job manager configuration"""

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('SlurmConfiguration.__init__ started')
        # dictionary to hold information about options
        self.options = {'slurm_location':
                            configfile.Option(name='slurm_location',
                                              default_value='/usr',
                                              mapping='OSG_PBS_LOCATION'),
                        'db_host':
                            configfile.Option(name='db_host',
                                              required=configfile.Option.OPTIONAL,
                                              default_value=''),
                        'db_port':
                            configfile.Option(name='db_port',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=int,
                                              default_value=3306),
                        'db_user':
                            configfile.Option(name='db_user',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='slurm'),
                        'db_name':
                            configfile.Option(name='db_name',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='slurm_acct_db'),
                        'db_pass':
                            configfile.Option(name='db_pass',
                                              required=configfile.Option.OPTIONAL,
                                              default_value=''),
                        'slurm_cluster':
                            configfile.Option(name='slurm_cluster',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='')}
        self.config_section = "SLURM"
        self.slurm_bin_location = None
        self.log('SlurmConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        super(SlurmConfiguration, self).parse_configuration(configuration)

        self.log('SlurmConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.log('SLURM section not found in config file')
            self.log('SlurmConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('SlurmConfiguration.parse_configuration completed')
            return True

        self.get_options(configuration, ignore_options=['enabled'])

        # set OSG_JOB_MANAGER and OSG_JOB_MANAGER_HOME
        self.options['job_manager'] = configfile.Option(name='job_manager',
                                                        value='SLURM',
                                                        mapping='OSG_JOB_MANAGER')
        self.options['home'] = configfile.Option(name='job_manager_home',
                                                 value=self.options['slurm_location'].value,
                                                 mapping='OSG_JOB_MANAGER_HOME')

        self.slurm_bin_location = os.path.join(self.options['slurm_location'].value, 'bin')

        self.log('SlurmConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('SlurmConfiguration.check_attributes started')

        attributes_ok = True

        if not self.enabled:
            self.log('SLURM not enabled, returning True')
            self.log('SlurmConfiguration.check_attributes completed')
            return attributes_ok

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('SlurmConfiguration.check_attributes completed')
            return attributes_ok

        # make sure locations exist
        if not validation.valid_location(self.options['slurm_location'].value):
            attributes_ok = False
            self.log("Non-existent location given: %s" %
                     (self.options['slurm_location'].value),
                     option='slurm_location',
                     section=self.config_section,
                     level=logging.ERROR)

        if not validation.valid_directory(self.slurm_bin_location):
            attributes_ok = False
            self.log("Given slurm_location %r has no bin/ directory" % self.options['slurm_location'].value,
                     option='slurm_location',
                     section=self.config_section,
                     level=logging.ERROR)

        self.log('SlurmConfiguration.check_attributes completed')
        return attributes_ok

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('SlurmConfiguration.configure started')

        if not self.enabled:
            self.log('Slurm not enabled, returning True')
            self.log('SlurmConfiguration.configure completed')
            return True

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log('SlurmConfiguration.configure completed')
            return True

        if self.htcondor_gateway_enabled:
            self.write_binpaths_to_blah_config('slurm', self.slurm_bin_location)
            self.write_blah_disable_wn_proxy_renewal_to_blah_config()
            self.write_htcondor_ce_sentinel()

        self.log('SlurmConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "SLURM"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """

        if not self.enabled or self.ignored:
            return set()

        return {'globus-gridftp-server'}.union(self.gateway_services())

    def get_db_host(self):
        """
        Return the hostname of the machine with the Slurm DB
        """

        return self.options['db_host'].value

    def get_db_port(self):
        """
        Return the port for Slurm DB service
        """

        return self.options['db_port'].value

    def get_db_user(self):
        """
        Return the user to use when accessing Slurm DB
        """

        return self.options['db_user'].value

    def get_db_pass(self):
        """
        Return the location of the file containing the password
        to use when accessing Slurm DB
        """

        return self.options['db_pass'].value

    def get_db_name(self):
        """
        Return the name of the data slurm is using for accounting info
        """

        return self.options['db_name'].value

    def get_slurm_cluster(self):
        """
        Return the name of the data slurm is using for accounting info
        """

        return self.options['slurm_cluster'].value

    def get_location(self):
        """
        Return the location where slurm is installed
        """

        return self.options['slurm_location'].value
