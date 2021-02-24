""" Module to handle attributes and configuration for Gratia """

import os
import re
import sys
import logging
from xml.sax import saxutils

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import validation
from osg_configure.modules import configfile
from osg_configure.modules.baseconfiguration import BaseConfiguration

__all__ = ['GratiaConfiguration']

GRATIA_CONFIG_FILES = {
    'htcondor-ce': '/etc/gratia/htcondor-ce/ProbeConfig'
}

CE_PROBE_RPMS = ['gratia-probe-htcondor-ce']


def requirements_are_installed():
    return (utilities.gateway_installed() and
            utilities.any_rpms_installed(CE_PROBE_RPMS))


class GratiaConfiguration(BaseConfiguration):
    """Class to handle attributes and configuration related to gratia services"""

    metric_probe_deprecation = """WARNING:
The metric probe should no longer be configured using 'probes' option in the 
[Gratia] section. All OSG installations will automatically report to the GOC 
RSV collector.  If you want to send to a different collector use the 
'gratia_collector' option in the [RSV] section and specify the 
hostname:port of the desired collector.  If you do not understand what to 
do then just remove the metric probe specification in the 'probes' option 
in your config.ini file."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log("GratiaConfiguration.__init__ started")

        self.config_section = 'Gratia'
        self.options = {'probes':
                            configfile.Option(name='probes',
                                              default_value=''),
                        'resource':
                            configfile.Option(name='resource',
                                              default_value='',
                                              required=configfile.Option.OPTIONAL)}

        # Dictionary of which host[:port] to send probe data to, keyed by probe.
        self.enabled_probe_hosts = {}

        # defaults for itb and production use
        self._itb_defaults = {'probes':
                                   'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
        self._production_defaults = {'probes':
                                          'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}

        self._job_managers = ['htcondor-ce']
        self._old_job_managers = ['pbs', 'sge', 'lsf', 'condor', 'slurm']
        self._probe_config = {}
        self.grid_group = 'OSG'

        self.log("GratiaConfiguration.__init__ completed")

    def parse_configuration(self, configuration):
        """
        Try to get configuration information from ConfigParser or SafeConfigParser
        object given by configuration and write recognized settings to attributes
        dict
        """

        self.log('GratiaConfiguration.parse_configuration started')

        self.check_config(configuration)

        if (not configuration.has_section(self.config_section) and requirements_are_installed()):
            self.log('CE probes installed but no Gratia section, auto-configuring gratia')
            self._configure_default_ce(configuration)
            self.log('GratiaConfiguration.parse_configuration completed')
            return True
        elif not configuration.has_section(self.config_section):
            self.enabled = False
            self.log("%s section not in config file" % self.config_section)
            self.log('Gratia.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('GratiaConfiguration.parse_configuration completed')
            return True

        # set the appropriate defaults if we're on a CE
        if requirements_are_installed():
            if configuration.has_option('Site Information', 'group'):
                self.grid_group = configuration.get('Site Information', 'group')

            if self.grid_group == 'OSG':
                self.options['probes'].default_value = \
                    self._production_defaults['probes']
            elif self.grid_group == 'OSG-ITB':
                self.options['probes'].default_value = \
                    self._itb_defaults['probes']

            # grab configuration information for various jobmanagers
            probes_iter = self.get_installed_probe_config_files().keys()
            for probe in probes_iter:
                if probe == 'htcondor-ce':
                    self._probe_config['htcondor-ce'] = {}

        self.get_options(configuration,
                        ignore_options=['itb-jobmanager-gratia',
                                        'itb-gridftp-gratia',
                                        'osg-jobmanager-gratia',
                                        'osg-gridftp-gratia',
                                        'enabled'])

        if utilities.blank(self.options['probes'].value):
            self.log('GratiaConfiguration.parse_configuration completed')
            return

        self._set_enabled_probe_host(self.options['probes'].value)
        self.log('GratiaConfiguration.parse_configuration completed')

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log("GratiaConfiguration.configure started")

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log("GratiaConfiguration.configure completed")
            return True

        # disable all gratia services
        # if gratia is enabled, probes will get enabled below
        if not self.enabled:
            self.log("Not enabled")
            self.log("GratiaConfiguration.configure completed")
            return True

        if utilities.blank(self.options['resource'].value):
            if 'OSG_SITE_NAME' not in attributes:
                self.log('No resource found for gratia reporting. You must give it '
                         'using the resource option in the Gratia section or specify '
                         'it in the Site Information section',
                         level=logging.ERROR)
                self.log("GratiaConfiguration.configure completed")
                return False
            else:
                self.options['resource'].value = attributes['OSG_SITE_NAME']

        # TODO Why is gratia looking at attributes instead of just using the options
        # directly?  If it's not necessary, drop the OSG_HOSTNAME attribute from
        # siteinformation.py.
        if 'OSG_HOSTNAME' not in attributes:
            self.log('Hostname of this machine not specified. Please give this '
                     'in the host_name option in the Site Information section',
                     level=logging.ERROR)
            self.log("GratiaConfiguration.configure completed")
            return False

        hostname = attributes['OSG_HOSTNAME']
        probe_config_files = self.get_installed_probe_config_files()
        probes_iter = probe_config_files.keys()
        for probe in probes_iter:
            if probe in self._job_managers:
                if probe not in self._probe_config:
                    # Probe is installed but we don't have configuration for it
                    # might be due to pbs-lsf probe sharing or relevant job
                    # manager is not shared
                    continue

                if 'jobmanager' in self.enabled_probe_hosts:
                    probe_host = self.enabled_probe_hosts['jobmanager']
                else:
                    continue
            elif probe in self._old_job_managers:
                continue
            else:
                if probe in self.enabled_probe_hosts:
                    probe_host = self.enabled_probe_hosts[probe]
                else:
                    continue

            self._subscribe_probe_to_remote_host(
                probe,
                probe_config_files[probe],
                remote_host=probe_host,
                local_resource=self.options['resource'].value,
                local_host=hostname
            )
            if probe == 'htcondor-ce':
                self._configure_htcondor_ce_probe()

        self.log("GratiaConfiguration.configure completed")
        return True

    # pylint: disable-msg=R0201
    @staticmethod
    def get_installed_probe_config_files():
        """Return a mapping of probe name -> ProbeConfig file.
        Note that "pbs" and "lsf" have the same probe.
        """

        probes = {}
        probe_list = os.listdir('/etc/gratia/')
        for probe in probe_list:
            if probe.lower() == 'common':
                # the common directory isn't a probe
                continue
            elif probe.lower() == 'pbs-lsf' and os.path.isfile('/etc/gratia/pbs-lsf/ProbeConfig'):
                probes['pbs'] = '/etc/gratia/pbs-lsf/ProbeConfig'
                probes['lsf'] = '/etc/gratia/pbs-lsf/ProbeConfig'
                continue
            # Chech the config file before adding the probe
            probePath = os.path.join('/etc/gratia',
                                     probe,
                                     'ProbeConfig')
            if os.path.isfile(probePath):
                probes[probe] = probePath
        return probes

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check configuration  and make sure things are setup correctly"""
        self.log("GratiaConfiguration.check_attributes started")

        if self.ignored:
            self.log("%s section ignored" % self.config_section)
            self.log("GratiaConfiguration.check_attributes completed")
            return True

        if not self.enabled:
            self.log("Not enabled")
            self.log("GratiaConfiguration.check_attributes completed")
            return True
        status = self._check_servers()
        self.log("GratiaConfiguration.check_attributes completed")
        return status

    def _subscription_present(self, probe_file, remote_host):
        """
        Check probe file to see if subscription to the host is present
        """

        self.log("GratiaConfiguration._subscription_present started")
        elements = utilities.get_elements('ProbeConfiguration', probe_file)
        for element in elements:
            try:
                if (element.getAttribute('EnableProbe') == 1 and
                            element.getAttribute('SOAPHost') == remote_host):
                    self.log("Subscription for %s in %s found" % (remote_host, probe_file))
                    return True
            # pylint: disable-msg=W0703
            except Exception as e:
                self.log("Exception checking element, %s" % e)

        self.log("GratiaConfiguration._subscription_present completed")
        return False

    def _subscribe_probe_to_remote_host(
            self, probe, probe_file, remote_host, local_resource, local_host):
        """Subscribe the given probe to the given remote host if necessary --
        this means:
        - Enable the probe
        - Set the local host name in the probe config (in ProbeName)
        - Set the local resource name (in SiteName)
        - Set the grid group (in Grid)
        - Set the *Host settings to the the remote host

        Check to see if a given probe has the correct subscription and if not
        make it.
        """

        self.log("GratiaConfiguration._subscribe_probe_to_remote_host started")

        # XXX This just checks EnableProbe and SOAPHost; should we check the other *Host
        # settings or are we using SOAPHost as a "don't configure me" sentinel?
        # -mat 2/19/21
        if self._subscription_present(probe_file, remote_host):
            self.log("Subscription found %s probe, returning" % probe)
            self.log("GratiaConfiguration._subscribe_probe_to_remote_host completed")
            return True

        if probe == 'gridftp':
            probe = 'gridftp-transfer'

        try:
            buf = open(probe_file, "r", encoding="latin-1").read()
            buf = self.replace_setting(buf, 'ProbeName', "%s:%s" % (probe, local_host))
            buf = self.replace_setting(buf, 'SiteName', local_resource)
            buf = self.replace_setting(buf, 'Grid', self.grid_group)
            buf = self.replace_setting(buf, 'EnableProbe', '1')
            for var in ['SSLHost', 'SOAPHost', 'SSLRegistrationHost', 'CollectorHost']:
                buf = self.replace_setting(buf, var, remote_host)

            if not utilities.atomic_write(probe_file, buf, mode=0o644):
                self.log("Error while configuring gratia probes: " +
                         "can't write to %s" % probe_file,
                         level=logging.ERROR)
                raise exceptions.ConfigureError("Error configuring gratia")
        except OSError:
            self.log("Error while configuring gratia probes",
                     exception=True,
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Error configuring gratia")

        self.log("GratiaConfiguration._subscribe_probe_to_remote_host completed")
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "Gratia"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return False

    def _check_servers(self):
        """
        Returns True or False depending whether the server_list is a valid list
        of servers.
        A valid list consists of host[:port] entries separated by commas,
        e.g. server1.example.com,server2.example.com:2188
        """
        valid = True
        for probe in self.enabled_probe_hosts:
            if probe == 'metric':
                sys.stdout.write(self.metric_probe_deprecation + "\n")
                self.log(self.metric_probe_deprecation, level=logging.WARNING)
            server = self.enabled_probe_hosts[probe].split(':')[0]
            if not validation.valid_domain(server, False):
                err_mesg = "The server specified for probe %s is not " % probe
                err_mesg += "a valid domain: %s" % server
                self.log(err_mesg, level=logging.ERROR)
                valid = False
            elif not validation.valid_domain(server, True):
                err_mesg = "The server specified for probe %s does not " % probe
                err_mesg += "resolve: %s" % server
                self.log(err_mesg, level=logging.WARNING)
            if server != self.enabled_probe_hosts[probe]:
                port = self.enabled_probe_hosts[probe].split(':')[1]
                try:
                    temp = int(port)
                    if temp < 0:
                        raise ValueError()
                except ValueError:
                    self.log("The port specified for probe %s is not valid, either it "
                             "is less than 0 or not an integer" % probe,
                             exception=True,
                             level=logging.ERROR)
        return valid

    def _set_enabled_probe_host(self, probes):
        """Parse a list of probes (taken from the Gratia.probes option)
        and set the `enabled_probe_hosts`, which is a probe name -> upload host
        mapping (with an optional port).
        Treat "gridftp" as an alias for "gridftp-transfer".
        """

        for probe_entry in probes.split(','):
            tmp = probe_entry.split(':')
            probe_name = tmp[0].strip()
            if probe_name == 'gridftp':
                probe_name = 'gridftp-transfer'
            if len(tmp[1:]) == 1:
                self.enabled_probe_hosts[probe_name] = tmp[1]
            else:
                self.enabled_probe_hosts[probe_name] = ':'.join(tmp[1:])

    def _configure_default_ce(self, configuration):
        """
        Configure gratia for a ce which does not have the gratia section
        """
        self.enabled = True

        if configuration.has_option('Site Information', 'resource'):
            resource = configuration.get('Site Information', 'resource')
            self.options['resource'].value = resource
        elif configuration.has_option('Site Information', 'site_name'):
            resource = configuration.get('Site Information', 'site_name')
            self.options['resource'].value = resource
        else:
            self.log('No resource defined in Site Information, this is required on a CE',
                     level=logging.ERROR)
            raise exceptions.SettingError('In Site Information, resource needs to be set')

        if configuration.has_option('Site Information', 'group'):
            group = configuration.get('Site Information', 'group')
        else:
            self.log('No group defined in Site Information, this is required on a CE',
                     level=logging.ERROR)
            raise exceptions.SettingError('In Site Information, group needs to be set')

        if group == 'OSG':
            probes = self._production_defaults['probes']
        elif group == 'OSG-ITB':
            probes = self._itb_defaults['probes']
        else:
            raise exceptions.SettingError('In Site Information, group must be '
                                          'OSG or OSG-ITB')

        self.options['probes'].value = probes
        self._set_enabled_probe_host(probes)

        return True

    def _configure_htcondor_ce_probe(self):
        """
        Do HTCondor-CE probe specific configuration
        Set to suppress grid local jobs (pre-routed jobs)
        """
        config_location = GRATIA_CONFIG_FILES['htcondor-ce']
        buf = open(config_location, "r", encoding="latin-1").read()
        buf = self.replace_setting(buf, 'SuppressGridLocalRecords', '1')
        
        if not utilities.atomic_write(config_location, buf):
            return False
        return True

    @staticmethod
    def replace_setting(buf, setting, value, xml_file=True):
        """
          Replace the first instance of the option within a string, adding
          the option if it's not present

          e.g.
          "a=b\n  setting=old_value" => "a=b\n setting=value"
          and
          "a=b\n " => "a=b\n setting=value"

          returns the string with the option string replaced/added
        """
        value = str(value)
        if xml_file:
            quoted_value = saxutils.quoteattr(value)
        else:
            # urCollector.conf files are a custom format that require '"'
            # surrounding the value but support no escaping of quotes or
            # anything.
            quoted_value = '"' + value + '"'

        re_obj = re.compile(r"^(\s*)%s\s*=.*$" % setting, re.MULTILINE)
        new_buf, count = re_obj.subn(r'\1%s=%s' % (setting, quoted_value), buf, 1)
        if count == 0:
            if xml_file:
                new_buf = new_buf.replace('/>', "    %s=%s\n/>" % (setting, quoted_value))
            else:
                new_buf += "%s = %s\n" % (setting, quoted_value)
        return new_buf

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """

        if not self.enabled or self.ignored:
            return set()

        return {'gratia-probes-cron'}
