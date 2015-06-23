"""This module provides a class to handle attributes and configuration
 for OSG info services subscriptions"""

import re
import subprocess
import urlparse
import logging

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration
from osg_configure.modules import subcluster

__all__ = ['InfoServicesConfiguration']

CE_COLLECTOR_ATTRIBUTES_FILE = '/etc/condor-ce/config.d/10-osg-attributes-generated.conf'
CE_COLLECTOR_CONFIG_FILE = '/etc/condor-ce/config.d/10-ce-collector-generated.conf'
HTCONDOR_CE_COLLECTOR_PORT = 9619

SERVICECERT_PATH = "/etc/grid-security/http/httpcert.pem"
SERVICEKEY_PATH = "/etc/grid-security/http/httpkey.pem"

# BATCH_SYSTEMS here is both the config sections for the batch systems
# and the values in the OSG_BatchSystems attribute since they are
# coincidentally the same. If they ever change, make a mapping.
BATCH_SYSTEMS = ['Condor', 'LSF', 'PBS', 'SGE', 'SLURM']

try:
    import classad
except ImportError:
    classad = None


class InfoServicesConfiguration(BaseConfiguration):
    """
    Class to handle attributes and configuration related to
    miscellaneous services
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(InfoServicesConfiguration, self).__init__(*args, **kwargs)
        self.log("InfoServicesConfiguration.__init__ started")
        # file location for xml file with info services subscriptions
        self.config_section = 'Info Services'
        self.options = {'ress_servers': configfile.Option(name='ress_servers',
                                                          default_value=''),
                        'bdii_servers': configfile.Option(name='bdii_servers',
                                                          default_value=''),
                        'ce_collectors': configfile.Option(name='ce_collectors',
                                                           default_value='',
                                                           required=configfile.Option.OPTIONAL)}
        self._itb_defaults = {
            'ress_servers': 'https://osg-ress-4.fnal.gov:8443/ig/services/CEInfoCollector[OLD_CLASSAD]',
            'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW],http://is2.grid.iu.edu:14001[RAW]',
            'ce_collectors': 'collector-itb.opensciencegrid.org:%d' % HTCONDOR_CE_COLLECTOR_PORT}
        self._production_defaults = {
            'ress_servers': 'https://osg-ress-1.fnal.gov:8443/ig/services/CEInfoCollector[OLD_CLASSAD]',
            'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW],http://is2.grid.iu.edu:14001[RAW]',
            'ce_collectors': 'collector1.opensciencegrid.org:%d,collector2.opensciencegrid.org:%d' % (
                HTCONDOR_CE_COLLECTOR_PORT, HTCONDOR_CE_COLLECTOR_PORT)}
        self.bdii_servers = {}
        self.ress_servers = {}
        self.copy_host_cert_for_service_cert = False

        self.ois_required_rpms_installed = utilities.gateway_installed() and utilities.rpm_installed(
            'osg-info-services')

        # for htcondor-ce-info-services:
        self.ce_collectors = []
        self.ce_collector_required_rpms_installed = utilities.rpm_installed('htcondor-ce')
        self.osg_resource = ""
        self.osg_resource_group = ""
        self.enabled_batch_systems = []
        self.htcondor_gateway_enabled = None
        self.resource_catalog = None

        self.log("InfoServicesConfiguration.__init__ completed")

    def _set_default_servers(self, configuration):
        group = utilities.config_safe_get(configuration, 'Site Information', 'group')
        for key in ['ress_servers', 'bdii_servers', 'ce_collectors']:
            if group == 'OSG-ITB':
                self.options[key].default_value = self._itb_defaults[key]
            else:
                self.options[key].default_value = self._production_defaults[key]

    def _parse_ce_collectors(self, val):
        if val == 'PRODUCTION':
            return self._production_defaults['ce_collectors'].split(',')
        elif val == 'ITB':
            return self._itb_defaults['ce_collectors'].split(',')
        else:
            return val.split(',')

    def parse_configuration(self, configuration):
        """
        Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """

        self.log('InfoServicesConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section) and self.ois_required_rpms_installed:
            self.log('Section missing and on a CE, autoconfiguring')
            self._auto_configure(configuration)
            self.log('InfoServicesConfiguration.parse_configuration completed')
            return True
        elif not configuration.has_section(self.config_section):
            self.enabled = False
            self.log("%s section not in config file" % self.config_section)
            self.log('InfoServicesConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('InfoServicesConfiguration.parse_configuration completed')
            return True

        self._set_default_servers(configuration)

        self.get_options(configuration,
                        ignore_options=['itb-ress-servers',
                                        'itb-bdii-servers',
                                        'osg-ress-servers',
                                        'osg-bdii-servers',
                                        'enabled'])

        self.ress_servers = self._parse_servers(self.options['ress_servers'].value)
        self.bdii_servers = self._parse_servers(self.options['bdii_servers'].value)
        self.ce_collectors = self._parse_ce_collectors(self.options['ce_collectors'].value)

        def csg(section, option):
            return utilities.config_safe_get(configuration, section, option, None)

        def csgbool(section, option):
            return utilities.config_safe_getboolean(configuration, section, option, False)

        # We get some values for HTCondor-CE from the Site Information section
        self.osg_resource = csg('Site Information', 'resource')
        self.osg_resource_group = csg('Site Information', 'resource_group')
        # and the enabled batch systems from their respective sections
        self.enabled_batch_systems = [bs for bs in BATCH_SYSTEMS if csgbool(bs, 'enabled')]

        self.copy_host_cert_for_service_cert = csgbool('Misc Services', 'copy_host_cert_for_service_certs')
        self.htcondor_gateway_enabled = csgbool('Gateway', 'htcondor_gateway_enabled')
        if self.htcondor_gateway_enabled and self.ce_collector_required_rpms_installed:
            if classad is not None:
                self.resource_catalog = subcluster.resource_catalog_from_config(configuration, logger=self.logger)
            else:
                self.log("Cannot configure HTCondor CE info services: unable to import HTCondor Python bindings."
                         "\nEnsure the 'classad' Python module is installed and accessible to Python scripts."
                         "\nIf using HTCondor from RPMs, install the 'condor-python' RPM."
                         "\nIf not, you may need to add the directory containing the Python bindings to PYTHONPATH."
                         "\nHTCondor version must be at least 8.2.0.", level=logging.WARNING)

        self.log('InfoServicesConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log("InfoServicesConfiguration.configure started")

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log('InfoServicesConfiguration.configure completed')
            return True

        if not self.enabled:
            self.log("Not enabled")
            self.log("InfoServicesConfiguration.configure completed")
            return True

        if self.copy_host_cert_for_service_cert:
            if not self.create_missing_service_cert_key(SERVICECERT_PATH, SERVICEKEY_PATH, 'tomcat'):
                self.log("Could not create service cert/key", level=logging.ERROR)
                return False

        if self.ce_collector_required_rpms_installed and self.htcondor_gateway_enabled and classad is not None:
            self._configure_ce_collector()

        self.log("InfoServicesConfiguration.configure completed")
        return True

    def check_attributes(self, attributes):
        """Check configuration and make sure things are setup correctly"""
        self.log("InfoServicesConfiguration.check_attributes started")

        if not self.enabled:
            self.log("Not enabled")
            self.log("InfoServicesConfiguration.check_attributes completed")
            return True

        if self.ignored:
            self.log('Ignored, returning True')
            self.log("InfoServicesConfiguration.check_attributes completed")
            return True

        valid = True
        self.log("Checking BDII subscriptions")
        for subscription in self.bdii_servers:
            valid &= self._check_subscription(subscription,
                                              self.bdii_servers[subscription])

        self.log("Checking ReSS subscriptions")
        for subscription in self.ress_servers:
            valid &= self._check_subscription(subscription,
                                              self.ress_servers[subscription])

        self.log("InfoServicesConfiguration.check_attributes completed")
        return valid

    def module_name(self):
        """Return a string with the name of the module"""
        return "Infoservices"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be
        configured separately"""
        return False

    def _check_subscription(self, subscription, dialect):
        """
        Check a subscription and dialect to make sure it's valid, return True if
        that's the case, otherwise false.

        subscription must be a uri and dialect must be CLASSAD, RAW, or OLD_CLASSAD
        """

        valid = True
        # check for valid uri
        result = urlparse.urlsplit(subscription)
        if result[1] == '':
            self.log("Subscription must be a uri, got %s" % subscription,
                     level=logging.ERROR)
            valid = False

        # check to see if host resolves
        server = result[1]
        if ':' in server:
            server = server.split(':')[0]
        if not validation.valid_domain(server, True):
            self.log("Host in subscription does not resolve: %s" % server,
                     level=logging.ERROR)
            valid = False

        # check to make sure dialect is correct
        if dialect not in ('CLASSAD', 'RAW', 'OLD_CLASSAD'):
            self.log("Dialect for subscription %s is not valid: %s" % (server, dialect),
                     level=logging.ERROR)
            valid = False
        return valid

    @classmethod
    def _parse_servers(cls, servers):
        """
        Take a list of servers and parse it into a list of
        (server, subscription_type) tuples
        """
        server_list = {}
        if servers.lower() == 'ignore':
            # if the server list is set to ignore, then don't use any servers
            # this allows cemon to be send ress information but not bdii or vice versa
            return server_list

        server_regex = re.compile(r'(.*)\[(.*)\]')
        for entry in servers.split(','):
            match = server_regex.match(entry)
            if match is None:
                raise exceptions.SettingError('Invalid subscription: %s' % entry)
            server_list[match.group(1).strip()] = match.group(2)
        return server_list

    def _auto_configure(self, configuration):
        """
        Method to configure cemon without any cemon section on a CE
        """

        self.enabled = True
        if configuration.has_option('Site Information', 'group'):
            group = configuration.get('Site Information', 'group')
        else:
            self.log('No group defined in Site Information, this is required on a CE',
                     level=logging.ERROR)
            raise exceptions.SettingError('In Site Information, group needs to be set')
        if group == 'OSG':
            ress_servers = self._production_defaults['ress_servers']
            bdii_servers = self._production_defaults['bdii_servers']
        elif group == 'OSG-ITB':
            ress_servers = self._itb_defaults['ress_servers']
            bdii_servers = self._itb_defaults['bdii_servers']
        else:
            self.log('Group must be OSG or OSG-ITB',
                     level=logging.ERROR)
            raise exceptions.SettingError('In Site Information, group needs to be OSG or OSG-ITB')

        self.options['ress_servers'].value = ress_servers
        self.options['bdii_servers'].value = bdii_servers
        self.ress_servers = self._parse_servers(ress_servers)
        self.bdii_servers = self._parse_servers(bdii_servers)

    def enabled_services(self):
        """
        Return a list of  system services needed for module to work
        """
        services = set()
        if self.ois_required_rpms_installed:
            services.add('osg-info-services')
        if self.ce_collector_required_rpms_installed and self.htcondor_gateway_enabled:
            services.add('condor-ce')
        return services

    def _configure_ce_collector(self):
        for filename, description, writer_func in [
            (CE_COLLECTOR_ATTRIBUTES_FILE, "attributes file", self._write_ce_collector_attributes_file),
            (CE_COLLECTOR_CONFIG_FILE, "CE collector config file", self._write_ce_collector_file)
        ]:
            if not writer_func(filename):
                self.log("Writing %s %r failed" % (description, filename),
                         level=logging.ERROR)
                return False

        resourcecatalog_location = self._resourcecatalog_location()
        if not resourcecatalog_location:
            # shouldn't happen -- we just wrote this
            self.log("Verifying OSG_ResourceCatalog failed!", level=logging.ERROR)
            return False
        else:
            if resourcecatalog_location != CE_COLLECTOR_ATTRIBUTES_FILE:
                self.log("Generated OSG_ResourceCatalog is overridden by %s" % resourcecatalog_location,
                         level=logging.WARNING)

    def _write_ce_collector_attributes_file(self, attributes_file):
        """Write config file that contains the osg attributes for the
        CE-Collector to advertise

        """
        schedd_attrs_list = ["$(SCHEDD_ATTRS)"]
        attributes_file_lines = []

        for name, value in [
            ('OSG_Resource', self.osg_resource),
            ('OSG_ResourceGroup', self.osg_resource_group),
            ('OSG_BatchSystems', ",".join(self.enabled_batch_systems))
        ]:
            attributes_file_lines.append("%s = %s" % (name, utilities.classad_quote(value)))
            schedd_attrs_list.append(name)

        if self.resource_catalog:
            attributes_file_lines.append(self.resource_catalog.compose_text())
            schedd_attrs_list.append('OSG_ResourceCatalog')

        attributes_file_contents = (
            "# Do not edit - file generated by osg-configure\n"
            + "\n".join(attributes_file_lines) + "\n"
            + "SCHEDD_ATTRS = " + " ".join(schedd_attrs_list) + "\n"
        )

        return utilities.atomic_write(attributes_file, attributes_file_contents)

    def _write_ce_collector_file(self, info_services_file):
        """Write CE-Collector configuration file which specifies which
        host(s) to forward ads to

        """
        view_hosts = []
        for host in self.ce_collectors:
            if host.find(':') == -1:
                view_hosts.append("%s:%d" % (host, HTCONDOR_CE_COLLECTOR_PORT))
            else:
                view_hosts.append(host)
        info_services_file_contents = """\
# Do not edit - file generated by osg-configure
CONDOR_VIEW_HOST = %s
""" % ",".join(view_hosts)

        return utilities.atomic_write(info_services_file, info_services_file_contents)

    def _resourcecatalog_location(self):
        """Returns the name of the condor-ce config file where OSG_ResourceCatalog
        is actually defined (from condor_ce_config_val), or None if not defined

        """
        errlevel = logging.ERROR
        try:
            process = subprocess.Popen(['condor_ce_config_val', '-verbose', 'OSG_ResourceCatalog'],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if process.returncode != 0:
                if not (error and error.startswith('Not defined:')):
                    self.log('condor_ce_config_val OSG_ResourceCatalog failed; exit %d; error %s' % (
                    process.returncode, error),
                             level=errlevel)
                return None
        except OSError, err:
            self.log('Could not run condor_ce_config_val: %s' % str(err), level=errlevel)
            return None
        output = output.strip()
        match = re.search(r'# at: (\S+), line \d+', output)
        if not match:
            self.log('Could not find definition of OSG_ResourceCatalog; condor_ce_config_val output was: \n%s' % output,
                     level=errlevel)
            return None
        else:
            return match.group(1)
