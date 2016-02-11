"""
Module to handle attributes related to the bosco jobmanager 
configuration
"""
import os
import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.jobmanagerconfiguration import JobManagerConfiguration

__all__ = ['BoscoConfiguration']


class BoscoConfiguration(JobManagerConfiguration):
    """Class to handle attributes related to Bosco job manager configuration"""


    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(BoscoConfiguration, self).__init__(*args, **kwargs)
        self.log('BoscoConfiguration.__init__ started')
        
        # dictionary to hold information about options
        self.options = {'endpoint':
                            configfile.Option(name='endpoint',
                                              requred=configfile.Option.MANDATORY),
                        'batch':
                            configfile.Option(name='batch',
                                              requred=configfile.Option.MANDATORY),
                        'ssh_key':
                            configfile.Option(name='ssh_key',
                                              requred=configfile.Option.MANDATORY),
                        'max_jobs':
                            configfile.Option(name='max_jobs',
                                              requred=configfile.Option.OPTIONAL,
                                              default_value=1000)}
        
        self.config_section = "Bosco"
        log("BoscoConfiguration.__init__ completed")
        
        
    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        super(BoscoConfiguration, self).parse_configuration(configuration)

        self.log('SlurmConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.log('Bosco section not found in config file')
            self.log('BoscoConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('BoscoConfiguration.parse_configuration completed')
            return True
            
            
        self.get_options(configuration, ignore_options=['enabled'])
        
        
    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('BoscoConfiguration.check_attributes started')
        
        attributes_ok = True
        
        if not self.enabled:
            self.log('Bosco not enabled, returning True')
            self.log('BoscoConfiguration.check_attributes completed')
            return attributes_ok

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('BoscoConfiguration.check_attributes completed')
            return attributes_ok
            
        if not validation.valid_domain(self.options['endpoint'].value):
            attributes_ok = False
            self.log("Endpoint is not a valid hostname: %s" % 
                     (self.options['endpoint'].value),
                     option='endpoint',
                     section=self.config_section,
                     level=logging.ERROR)
        
        if self.options['batch'].value not in ['pbs', 'lsf', 'sge', 'condor']:
            attributes_ok = False
            self.log("Batch attribute is not valid: %s" % 
                     (self.options['batch'].value),
                     option='batch',
                     section=self.config_section,
                     level=logging.ERROR)
        
        # TODO: check if the ssh_key has the correct permissions!
        if not validation.valid_file(self.options['ssh_key'].value):
            attributes_ok = False
            self.log("ssh_key given is not a file: %s" %
                     (self.options['ssh_key'].value),
                     option='ssh_key',
                     section=self.config_section,
                     level=logging.ERROR)
        
        
        if not validation.valid_integer(self.options['max_jobs'].value):
            attributes_ok = False
            self.log("max_jobs is not an integer: %s" %
                     (self.options['max_jobs'].value),
                     option='max_jobs',
                     section=self.config_section,
                     level=logging.ERROR)

        self.log('BoscoConfiguration.check_attributes completed')
        return attributes_ok
        
        
        def configure(self, attributes):
            """Configure installation using attributes"""
            self.log('BoscoConfiguration.configure started')
            
            if not self.enabled:
                self.log('Bosco not enabled, returning True')
                self.log('BoscoConfiguration.configure completed')
                return True

            if self.ignored:
                self.log("%s configuration ignored" % self.config_section,
                         level=logging.WARNING)
                self.log('BoscoConfiguration.configure completed')
                return True
            
            # Do all the things here!
            
            self.log('BoscoConfiguration.configure completed')
            return True
