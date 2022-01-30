"""This module provides a class to handle configuration
 for CE collector info services"""

import re
from configparser import ConfigParser
import subprocess
import logging

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules.baseconfiguration import BaseConfiguration
from osg_configure.modules import ce_attributes
from osg_configure.modules import subcluster
from osg_configure.modules import reversevomap

__all__ = ['InfoServicesConfiguration']

CE_COLLECTOR_ATTRIBUTES_FILE = '/etc/condor-ce/config.d/10-osg-attributes-generated.conf'
CE_COLLECTOR_CONFIG_FILE = '/etc/condor-ce/config.d/10-ce-collector-generated.conf'
HTCONDOR_CE_COLLECTOR_PORT = 9619
USER_VO_MAP_LOCATION = '/var/lib/osg/user-vo-map'
BAN_VOMS_MAPFILE = reversevomap.BAN_MAPFILE
BAN_MAPFILE = '/etc/grid-security/ban-mapfile'


try:
    import classad
except ImportError:
    classad = None


class InfoServicesConfiguration(BaseConfiguration):
    """
    Class to handle attributes and configuration related to
    info services
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log("InfoServicesConfiguration.__init__ started")
        self.config_section = 'Info Services'
        self.options = {'ce_collectors': configfile.Option(name='ce_collectors',
                                                           default_value='',
                                                           required=configfile.Option.OPTIONAL)}
        self._itb_default_ce_collectors = \
            'collector-itb.opensciencegrid.org:%d' % HTCONDOR_CE_COLLECTOR_PORT
        self._production_default_ce_collectors = \
            'collector1.opensciencegrid.org:%d,collector2.opensciencegrid.org:%d' % (
                HTCONDOR_CE_COLLECTOR_PORT, HTCONDOR_CE_COLLECTOR_PORT)

        self.ce_collectors = []
        self.ce_collector_required_rpms_installed = utilities.rpm_installed('htcondor-ce')
        self.htcondor_gateway_enabled = None
        self.authorization_method = None
        self.configuration = None
        self.ce_attributes_str = ""

        self.log("InfoServicesConfiguration.__init__ completed")

    def _set_default_servers(self, configuration):
        group = utilities.config_safe_get(configuration, 'Site Information', 'group')
        if group == 'OSG-ITB':
            self.options['ce_collectors'].default_value = self._itb_default_ce_collectors
        else:
            self.options['ce_collectors'].default_value = self._production_default_ce_collectors

    def _parse_ce_collectors(self, val):
        if val == 'PRODUCTION':
            return self._production_default_ce_collectors.split(',')
        elif val == 'ITB':
            return self._itb_default_ce_collectors.split(',')
        else:
            return val.split(',')

    def parse_configuration(self, configuration: ConfigParser):
        """
        Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """

        self.log('InfoServicesConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
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
                                        'ress_servers',
                                        'enabled',
                                        'bdii_servers'])

        self.ce_collectors = self._parse_ce_collectors(self.options['ce_collectors'].value)

        self.htcondor_gateway_enabled = configuration.get('Gateway', 'htcondor_gateway_enabled', fallback=False)

        self.configuration = configuration  # save for later: the ce_attributes module reads the whole config.

        if utilities.ce_installed() and not subcluster.check_config(configuration):
            self.log("On a CE but no valid 'Subcluster', 'Resource Entry', or 'Pilot' sections defined."
                     " This is required to advertise the capabilities of your cluster to the central collector."
                     " Jobs may not be sent to this CE.",
                     level=logging.ERROR)
            raise exceptions.SettingError("No Subcluster, Resource Entry, or Pilot sections")

        # Check resource catalog
        # This is a bit clunky to parse it here and not use the result in
        # configure(), but at this point we don't have a way of knowing what
        # default_allowed_vos should be.
        if self.ce_collector_required_rpms_installed and self.htcondor_gateway_enabled and classad is not None:
            subcluster.resource_catalog_from_config(configuration, default_allowed_vos=["*"])

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

        if self.ce_collector_required_rpms_installed and self.htcondor_gateway_enabled:
            if classad is None:
                self.log("Cannot configure HTCondor CE info services: unable to import HTCondor Python bindings."
                         "\nEnsure the 'classad' Python module is installed and accessible to Python scripts."
                         "\nIf using HTCondor from RPMs, install the 'python3-condor' RPM."
                         "\nIf not, you may need to add the directory containing the Python bindings to PYTHONPATH."
                         "\nHTCondor version must be at least 8.2.0.", level=logging.WARNING)
            else:
                try:
                    self.ce_attributes_str = ce_attributes.get_ce_attributes_str(self.configuration)
                except exceptions.SettingError as err:
                    self.log("Error in info services configuration: %s" % err, level=logging.ERROR)
                    return False
                self._configure_ce_collector()

        self.log("InfoServicesConfiguration.configure completed")
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "Infoservices"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be
        configured separately"""
        return False

    def enabled_services(self):
        """
        Return a list of  system services needed for module to work
        """
        services = set()
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
        attributes_file_contents = (
            "# Do not edit - file generated by osg-configure\n"
            + self.ce_attributes_str + "\n"
        )
        return utilities.atomic_write(attributes_file, attributes_file_contents)

    def _write_ce_collector_file(self, info_services_file):
        """Write CE-Collector configuration file which specifies which
        host(s) to forward ads to

        """
        view_hosts = []
        for host in self.ce_collectors:
            if ':' not in host:
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
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       encoding="latin-1")
            output, error = process.communicate()
            if process.returncode != 0:
                if not (error and error.startswith('Not defined:')):
                    self.log('condor_ce_config_val OSG_ResourceCatalog failed; exit %d; error %s' % (
                    process.returncode, error),
                             level=errlevel)
                return None
        except OSError as err:
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
