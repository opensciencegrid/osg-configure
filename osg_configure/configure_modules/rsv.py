""" Module to handle attributes and configuration for RSV service """

import os
import re
import shutil
import logging
import configparser
import pwd

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import validation
from osg_configure.modules import configfile
from osg_configure.modules.baseconfiguration import BaseConfiguration

__all__ = ['RsvConfiguration']


class RsvConfiguration(BaseConfiguration):
    """Class to handle attributes and configuration related to osg-rsv services"""

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(RsvConfiguration, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('RsvConfiguration.__init__ started')
        self.options = {'enable_local_probes':
                            configfile.Option(name='enable_local_probes',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=True),
                        'gratia_probes':
                            configfile.Option(name='gratia_probes',
                                              default_value='',
                                              required=configfile.Option.OPTIONAL),
                        'ce_hosts':
                            configfile.Option(name='ce_hosts',
                                              default_value='',
                                              required=configfile.Option.OPTIONAL),
                        'htcondor_ce_hosts':
                            configfile.Option(name='htcondor_ce_hosts',
                                              default_value='',
                                              required=configfile.Option.OPTIONAL),
                        'gridftp_hosts':
                            configfile.Option(name='gridftp_hosts',
                                              default_value='',
                                              required=configfile.Option.OPTIONAL),
                        'gridftp_dir':
                            configfile.Option(name='gridftp_dir',
                                              default_value='/tmp'),
                        'srm_hosts':
                            configfile.Option(name='srm_hosts',
                                              default_value='',
                                              required=configfile.Option.OPTIONAL),
                        'srm_dir':
                            configfile.Option(name='srm_dir',
                                              required=configfile.Option.OPTIONAL),
                        'srm_webservice_path':
                            configfile.Option(name='srm_webservice_path',
                                              required=configfile.Option.OPTIONAL),
                        'service_cert':
                            configfile.Option(name='service_cert',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='/etc/grid-security/rsv/rsvcert.pem'),
                        'service_key':
                            configfile.Option(name='service_key',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='/etc/grid-security/rsv/rsvkey.pem'),
                        'service_proxy':
                            configfile.Option(name='service_proxy',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='/tmp/rsvproxy'),
                        'user_proxy':
                            configfile.Option(name='user_proxy',
                                              default_value='',
                                              required=configfile.Option.OPTIONAL),
                        'legacy_proxy':
                            configfile.Option(name='legacy_proxy',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False),
                        'enable_gratia':
                            configfile.Option(name='enable_gratia',
                                              opt_type=bool,
                                              required=configfile.Option.OPTIONAL,
                                              default_value=False),
                        'condor_location':
                            configfile.Option(name='condor_location',
                                              default_value='',
                                              required=configfile.Option.OPTIONAL),
                        'enable_nagios':
                            configfile.Option(name='enable_nagios',
                                              opt_type=bool),
                        'nagios_send_nsca':
                            configfile.Option(name='nagios_send_nsca',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False),
                        'enable_zabbix':
                            configfile.Option(name='enable_zabbix',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False),
                        'zabbix_use_sender':
                            configfile.Option(name='zabbix_use_sender',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=False)}

        self._rsv_user = "rsv"
        self._ce_hosts = []
        self._htcondor_ce_hosts = []
        self._gridftp_hosts = []
        self._srm_hosts = []
        self._gratia_probes_2d = []
        self._gratia_metric_map = {}
        self._enable_rsv_downloads = False
        self._meta = configparser.RawConfigParser()
        self.htcondor_gateway_enabled = True
        self.use_service_cert = True
        self.copy_host_cert_for_service_cert = False
        self.grid_group = 'OSG'
        self.site_name = 'Generic Site'
        self.config_section = "RSV"
        self.rsv_conf_dir = '/etc/rsv'
        self.rsv_control = '/usr/bin/rsv-control'
        self.rsv_meta_dir = '/etc/rsv/meta/metrics'
        self.rsv_metrics_dir = '/etc/rsv/metrics'
        self.rsv_conf = '/etc/rsv/rsv.conf'
        self.uid = None
        self.gid = None
        self.log('RsvConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """
        Try to get configuration information from ConfigParser or
        SafeConfigParser object given by configuration and write recognized settings
        to attributes dict
        """
        self.log('RsvConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.enabled = False
            self.log("%s section not in config file" % self.config_section)
            self.log('RsvConfiguration.parse_configuration completed')
            return True

        if not utilities.rpm_installed('rsv-core'):
            self.enabled = False
            self.log('rsv-core rpm not installed, disabling RSV configuration')
            return True

        if not self.set_status(configuration):
            self.log('RsvConfiguration.parse_configuration completed')
            return True

        self.get_options(configuration, ignore_options=['enabled', 'gratia_collector'])

        # If we're on a CE, get the grid group if possible
        if configuration.has_section('Site Information'):
            if configuration.has_option('Site Information', 'group'):
                self.grid_group = configuration.get('Site Information', 'group')

            if configuration.has_option('Site Information', 'resource'):
                self.site_name = configuration.get('Site Information', 'resource')
            elif configuration.has_option('Site Information', 'site_name'):
                self.site_name = configuration.get('Site Information', 'site_name')


        # Parse lists
        self._ce_hosts = split_list_exclude_blank(self.options['ce_hosts'].value)
        self._htcondor_ce_hosts = split_list_exclude_blank(self.options['htcondor_ce_hosts'].value)
        self._srm_hosts = split_list_exclude_blank(self.options['srm_hosts'].value)

        # If the gridftp hosts are not defined then they default to the CE hosts
        if self.options['gridftp_hosts'].value == '':
            # check to see if the setting is in the config file
            if configuration.has_option(self.config_section, 'gridftp_hosts'):
                # present and set to default so we don't want gridftp tests
                self._gridftp_hosts = []
            else:
                # option is commented out, use ce_hosts setting
                self._gridftp_hosts = self._ce_hosts
        else:
            self._gridftp_hosts = split_list(self.options['gridftp_hosts'].value)

        if self.options['gratia_probes'].value != '':
            self._gratia_probes_2d = self.split_2d_list(self.options['gratia_probes'].value)

        # Check the options for which gateways are enabled
        # How we run remote probes depends on this
        if configuration.has_section('Gateway'):
            if configuration.has_option('Gateway', 'htcondor_gateway_enabled'):
                self.htcondor_gateway_enabled = configuration.getboolean('Gateway', 'htcondor_gateway_enabled')

        if configuration.has_section('Misc Services'):
            if configuration.has_option('Misc Services', 'copy_host_cert_for_service_certs'):
                self.copy_host_cert_for_service_cert = configuration.getboolean('Misc Services',
                                                                                'copy_host_cert_for_service_certs')

        self.log('RsvConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """
        Check attributes currently stored and make sure that they are consistent
        """

        self.log('RsvConfiguration.check_attributes started')
        attributes_ok = True

        if not self.enabled:
            self.log('Not enabled, returning True')
            self.log('RsvConfiguration.check_attributes completed')
            return attributes_ok

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('RsvConfiguration.check_attributes completed')
            return attributes_ok

        try:
            (self.uid, self.gid) = pwd.getpwnam(self._rsv_user)[2:4]
        except KeyError:  # no such user
            self.log("The %s user does not exist. RSV will not work without that user."
                     " Please reinstall the rsv* RPMs or create the user yourself."
                     " Note: it needs a valid shell and home directory." % self._rsv_user,
                     level=logging.ERROR)
            return False

        # Slurp in all the meta files which will tell us what type of metrics
        # we have and if they are enabled by default.
        self.load_rsv_meta_files()

        attributes_ok &= self._check_auth_settings()

        # check hosts
        attributes_ok &= self._validate_host_list(self._ce_hosts, "ce_hosts")
        attributes_ok &= self._validate_host_list(self._srm_hosts, "srm_hosts")
        if self.htcondor_gateway_enabled:
            attributes_ok &= self._validate_host_list(self._htcondor_ce_hosts, "htcondor_ce_hosts")

        attributes_ok &= self._check_gridftp_settings()
        attributes_ok &= self._check_srm_settings()
        # check Gratia list
        attributes_ok &= self._check_gratia_settings()

        # Make sure that the condor_location is valid if it is supplied
        attributes_ok &= self._check_condor_location()

        self.log('RsvConfiguration.check_attributes completed')
        return attributes_ok

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('RsvConfiguration.configure started')

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log('RsvConfiguration.configure completed')
            return True

        if not self.enabled:
            self.log('Not enabled, returning True')
            self.log('RsvConfiguration.configure completed')
            return True

        try:
            # Reset always?
            self._reset_configuration()
            self._create_cert_key_if_needed()
            # Put proxy information into rsv.conf
            self._configure_cert_info()
            # Enable consumers
            self._configure_consumers()
            # Enable metrics
            self._configure_ce_metrics()
            self._configure_gridftp_metrics()
            self._configure_gratia_metrics()
            self._configure_local_metrics()
            self._configure_srm_metrics()
            self._configure_condor_cron_ids()
            self._configure_default_ce_type()
            self._configure_ce_types()
            # Setup Apache?  I think this is done in the RPM

            self._configure_condor_location()
        except exceptions.ConfigureError:
            return False

        self.log('RsvConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "RSV"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def _check_gridftp_settings(self):
        """ Check gridftp settings and make sure they are valid """
        status_check = self._validate_host_list(self._gridftp_hosts, "gridftp_hosts")

        if utilities.blank(self.options['gridftp_dir'].value):
            self.log("Invalid gridftp_dir given: %s" %
                     self.options['gridftp_dir'].value,
                     section=self.config_section,
                     option='gridftp_dir',
                     level=logging.ERROR)
            status_check = False

        return status_check

    def _check_auth_settings(self):
        """ Check authorization/certificate settings and make sure that they are valid """

        check_value = True

        # Do not allow both the service cert settings and proxy settings
        # first create some helper variables
        blank_service_vals = (utilities.blank(self.options['service_cert'].value) and
                              utilities.blank(self.options['service_key'].value) and
                              utilities.blank(self.options['service_proxy'].value))

        default_service_vals = (self.options['service_cert'].value ==
                                self.options['service_cert'].default_value)
        default_service_vals &= (self.options['service_key'].value ==
                                 self.options['service_key'].default_value)
        default_service_vals &= (self.options['service_proxy'].value ==
                                 self.options['service_proxy'].default_value)

        blank_user_proxy = utilities.blank(self.options['user_proxy'].value)

        if (not blank_user_proxy and default_service_vals):
            self.log('User proxy specified and service_cert, service_key, ' +
                     'service_proxy at default values, assuming user_proxy ' +
                     'takes precedence in ' + self.config_section + ' section')
            self.use_service_cert = False
        elif not blank_user_proxy and not blank_service_vals:
            self.log("You cannot specify user_proxy with any of (service_cert, " +
                     "service_key, service_proxy).  They are mutually exclusive " +
                     "options in %s section." % self.config_section,
                     level=logging.ERROR)
            check_value = False

        # Make sure that either a service cert or user cert is selected
        if not ((self.options['service_cert'].value and
                     self.options['service_key'].value and
                     self.options['service_proxy'].value)
                or
                    self.options['user_proxy'].value):
            self.log("You must specify either service_cert/service_key/" +
                     "service_proxy *or* user_proxy in order to provide " +
                     "credentials for RSV to run jobs in " +
                     " %s section" % self.config_section,
                     level=logging.ERROR)
            check_value = False

        if not blank_user_proxy:
            # if not using a service certificate, make sure that the proxy file exists
            value = self.options['user_proxy'].value
            if utilities.blank(value) or not validation.valid_file(value):
                self.log("user_proxy does not point to an existing file: %s" % value,
                         section=self.config_section,
                         option='user_proxy',
                         level=logging.ERROR)
                check_value = False
        else:
            for optname in 'service_cert', 'service_key':
                value = self.options[optname].value
                if utilities.blank(value):
                    self.log("%s must have a valid location" % optname,
                             section=self.config_section,
                             option=optname,
                             level=logging.ERROR)
                    check_value = False
                elif not self.copy_host_cert_for_service_cert and not validation.valid_file(value):
                    self.log("%s must point to an existing file" % optname,
                             section=self.config_section,
                             option=optname,
                             level=logging.ERROR)
                    check_value = False

            value = self.options['service_proxy'].value
            if utilities.blank(value):
                self.log("service_proxy must have a valid location: %s" % value,
                         section=self.config_section,
                         option='service_proxy',
                         level=logging.ERROR)
                check_value = False

            value = os.path.dirname(self.options['service_proxy'].value)
            if not validation.valid_location(value):
                self.log("service_proxy must be located in a valid " +
                         "directory: %s" % value,
                         section=self.config_section,
                         option='service_proxy',
                         level=logging.ERROR)
                check_value = False

        return check_value

    def _reset_configuration(self):
        """ Reset all metrics and consumers to disabled """

        self.log("Resetting all metrics and consumers to disabled")

        for filename in os.listdir(self.rsv_conf_dir):
            if not re.search('\.conf$', filename):
                continue

            if filename in ('rsv.conf', 'rsv-nagios.conf', 'rsv-zabbix.conf'):
                continue

            path = os.path.join(self.rsv_conf_dir, filename)
            self.log("Removing %s as part of reset" % path)
            os.unlink(path)

        # Remove any host specific metric configuration
        for directory in os.listdir(self.rsv_metrics_dir):
            path = os.path.join(self.rsv_metrics_dir, directory)
            if not os.path.isdir(path):
                continue

            shutil.rmtree(path)

    def _create_cert_key_if_needed(self):
        if not self.copy_host_cert_for_service_cert:
            # User explicitly told us not to make a copy
            return
        service_cert = self.options['service_cert'].value
        service_key = self.options['service_key'].value
        if utilities.blank(service_cert) or utilities.blank(service_key):
            # cert/key location not specified so don't make anything
            return

        if not self.create_missing_service_cert_key(service_cert, service_key, 'rsv'):
            # creation unsuccessful
            self.log("Could not create service cert (%s) and key (%s)" % (service_cert, service_key),
                     level=logging.ERROR)
            raise exceptions.ConfigureError

    def _get_metrics_by_type(self, metric_type, enabled=True):
        """
        Examine meta info and return the metrics that are enabled by default
        for the defined type
        """

        metrics = []

        for metric in self._meta.sections():
            if re.search(" env$", metric):
                continue

            if self._meta.has_option(metric, "service-type"):
                if self._meta.get(metric, "service-type") == metric_type:
                    if not enabled:
                        metrics.append(metric)
                    else:
                        if self._meta.has_option(metric, "enable-by-default"):
                            if self._meta.get(metric, "enable-by-default") == "true":
                                metrics.append(metric)

        return metrics

    def _enable_metrics(self, host, metrics, args=None):
        """Given a host and array of metrics, enable them via rsv-control

        :param host: FQDN of host to enable metrics for
        :type host: str
        :param metrics: list of metrics to enable
        :type metrics: list
        :param args: extra arguments to rsv-control
        :type args: list or None
        :raise ConfigFailed: if rsv-control fails

        """
        # need this to prevent weird behaviour if [] as a default argument in function def
        args = args or []
        if not metrics:
            return

        if not utilities.run_script([self.rsv_control, "-v0", "--enable", "--host", host] +
                                            args +
                                            metrics):
            self.log("ERROR: Attempt to enable metrics via rsv-control failed",
                     level=logging.ERROR)
            self.log("Host: %s" % host,
                     level=logging.ERROR)
            self.log("Metrics: %s" % " ".join(metrics),
                     level=logging.ERROR)
            raise exceptions.ConfigureError

    def _configure_ce_metrics(self):
        """Enable CE metrics.
        This consists of OSG-HTCondor-CE
        metrics for htcondor_ce_hosts and OSG-CE metrics for ce_hosts (which should
        include htcondor_ce_hosts).

        :raise ConfigFailed: if enabling metrics fails
        """

        def _set_metrics_for_hosts(label, metric_type, hosts_var_name, hosts, enabled):
            if not enabled:
                self.log("%s disabled.  Not configuring %s metrics" % (label, label))
                return

            if not hosts:
                self.log("No %s defined.  Not configuring %s metrics" % (hosts_var_name, label))
                return

            metrics = self._get_metrics_by_type(metric_type)

            for host in hosts:
                self.log("Enabling %s metrics for host '%s'" % (label, host))
                self._enable_metrics(host, metrics)

        _set_metrics_for_hosts(label='CE', metric_type='OSG-CE', hosts_var_name='ce_hosts',
                               hosts=self._ce_hosts, enabled=True)
        _set_metrics_for_hosts(label='HTCondor-CE', metric_type='OSG-HTCondor-CE',
                               hosts_var_name='htcondor_ce_hosts', hosts=self._htcondor_ce_hosts,
                               enabled=self.htcondor_gateway_enabled)

    def _configure_gridftp_metrics(self):
        """ Enable GridFTP metrics for each GridFTP host declared    """

        if not self._gridftp_hosts:
            self.log("No gridftp_hosts defined.  Not configuring GridFTP metrics")
            return

        gridftp_dirs = split_list(self.options['gridftp_dir'].value)
        if len(self._gridftp_hosts) != len(gridftp_dirs) and len(gridftp_dirs) != 1:
            self.log("RSV.gridftp_dir is set incorrectly.  When enabling GridFTP " +
                     "metrics you must specify either exactly 1 entry, or the same " +
                     "number of entries in the gridftp_dir variable as you have in " +
                     "the gridftp_hosts section.  There are %i host entries " \
                     "and %i gridftp_dir entries." % (len(self._gridftp_hosts),
                                                      len(gridftp_dirs)),
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Failed to configure RSV")

        gridftp_metrics = self._get_metrics_by_type("GridFTP")

        count = 0
        for gridftp_host in self._gridftp_hosts:
            self.log("Enabling GridFTP metrics for host '%s'" % gridftp_host)

            if len(gridftp_dirs) == 1:
                directories = gridftp_dirs[0]
            else:
                directories = gridftp_dirs[count]

            args = ["--arg", "destination-dir=%s" % directories]

            self._enable_metrics(gridftp_host, gridftp_metrics, args)

            count += 1

    def _configure_local_metrics(self):
        """ Enable appropriate local metrics """

        if not self.options['enable_local_probes'].value:
            self.log("Local probes disabled.")
            return

        local_metrics = self._get_metrics_by_type("OSG-Local-Monitor")

        self.log("Enabling local metrics for host '%s'" % utilities.get_hostname())
        self._enable_metrics(utilities.get_hostname(), local_metrics)

    def _configure_srm_metrics(self):
        """ Enable SRM metric """

        if not self._srm_hosts:
            self.log("No srm_hosts defined.  Not configuring SRM metrics")
            return

        # Do some checking on the values.  perhaps this should be in the validate section?
        srm_dirs = split_list(self.options['srm_dir'].value)
        if len(self._srm_hosts) != len(srm_dirs):
            self.log("When enabling SRM metrics you must specify the same number " +
                     "of entries in the srm_dir variable as you have in the " +
                     "srm_hosts section.  There are %i host entries and %i " \
                     "srm_dir entries." % (len(self._srm_hosts), len(srm_dirs)),
                     level=logging.ERROR)
            raise exceptions.ConfigureError("Failed to configure RSV")

        srm_ws_paths = []
        if not utilities.blank(self.options['srm_webservice_path'].value):
            srm_ws_paths = split_list(self.options['srm_webservice_path'].value)

            if len(self._srm_hosts) != len(srm_ws_paths):
                self.log("If you set srm_webservice_path when enabling SRM metrics " +
                         "you must specify the same number of entries in the " +
                         "srm_webservice_path variable as you have in the srm_hosts " +
                         "section.  There are %i host entries and %i " \
                         "srm_webservice_path entries." % (len(self._srm_hosts),
                                                           len(srm_ws_paths)),
                         level=logging.ERROR)
                raise exceptions.ConfigureError("Failed to configure RSV")

        # Now time to do the actual configuration
        srm_metrics = self._get_metrics_by_type("OSG-SRM")
        count = 0
        for srm_host in self._srm_hosts:
            self.log("Enabling SRM metrics for host '%s'" % srm_host)

            args = ["--arg", "srm-destination-dir=%s" % srm_dirs[count]]
            if srm_ws_paths:
                args += ["--arg", "srm-webservice-path=%s" % srm_ws_paths[count]]

            self._enable_metrics(srm_host, srm_metrics, args)

            count += 1

    def _map_gratia_metric(self, gratia_type):
        """
        Map gratia type to rsv metric
        """
        # The first time through we will populate the map.  It will be cached as a
        # data member in this class so that we don't have to do this each time
        if not self._gratia_metric_map:
            ce_metrics = self._get_metrics_by_type("OSG-CE", enabled=False)
            for metric in ce_metrics:
                match = re.search("\.gratia\.(\S+)$", metric)
                if match:
                    self._gratia_metric_map[match.group(1)] = metric
                    self.log("Gratia map -> %s = %s" % (match.group(1), metric))

        # Now that we have the mapping, simply return the appropriate type.
        # This is the only code that should execute every time after the data structure is loaded.
        if gratia_type in self._gratia_metric_map:
            return self._gratia_metric_map[gratia_type]
        else:
            return None

    def _check_gratia_settings(self):
        """ Check to see if gratia settings are valid """

        tmp_2d = []

        # While checking the Gratia settings we will translate them to a list of
        # the actual probes to enable.
        status_check = True
        for item_list in self._gratia_probes_2d:
            tmp = []
            for metric_type in item_list:
                metric = self._map_gratia_metric(metric_type)
                if metric:
                    tmp.append(metric)
                else:
                    status_check = False
                    self.log("In %s section, gratia_probes setting: Probe %s is " \
                             "not a valid probe" % (self.config_section, metric_type),
                             level=logging.ERROR)

            tmp_2d.append(tmp)

        self._gratia_probes_2d = tmp_2d

        return status_check

    def _configure_gratia_metrics(self):
        """
        Enable Gratia metrics
        """

        if not self._gratia_probes_2d:
            self.log("Skipping Gratia metric configuration because gratia_probes_2d is empty")
            return

        if not self._ce_hosts:
            self.log("Skipping Gratia metric configuration because ce_hosts is empty")
            return

        num_ces = len(self._ce_hosts)
        num_gratia = len(self._gratia_probes_2d)
        if num_ces != num_gratia and num_gratia != 1:
            self.log("The number of CE hosts does not match the number of " +
                     "Gratia host definitions",
                     level=logging.ERROR)
            self.log("Number of CE hosts: %s" % num_ces,
                     level=logging.ERROR)
            self.log("Number of Gratia host definitions: %s" % num_gratia,
                     level=logging.ERROR)
            self.log("They must match, or you must have only one Gratia host " +
                     "definition (which will be used for all hosts",
                     level=logging.ERROR)
            raise exceptions.ConfigureError

        i = 0
        for ce in self._ce_hosts:
            gratia = None

            # There will either be a Gratia definition for each host, or else a single Gratia
            # definition which we will use across all hosts.
            if num_gratia == 1:
                gratia = self._gratia_probes_2d[0]
            else:
                gratia = self._gratia_probes_2d[i]
                i += 1

            self._enable_metrics(ce, gratia)

    def _check_condor_location(self):
        """ Make sure that a supplied Condor location is valid """

        if not self.options['condor_location'].value:
            self.log("Skipping condor_location validation because it is empty")
            return True

        condor_bin = os.path.join(self.options['condor_location'].value, "bin")
        condor_sbin = os.path.join(self.options['condor_location'].value, "sbin")

        if not os.path.exists(condor_bin) or not os.path.exists(condor_sbin):
            self.log("There is not a bin/ or sbin/ subdirectory at the supplied " +
                     "condor_location (%s)" % (self.options['condor_location'].value),
                     level=logging.ERROR)
            return False
        return True

    def _configure_condor_location(self):
        """ Put the Condor location into the necessary places """

        # Note: make sure that we write empty files if condor_location is not set
        # so that we can reverse the action of someone setting condor_location

        condor_dir = self.options['condor_location'].value

        # Put the location into the condor-cron-env.sh file so that the condor-cron
        # wrappers and init script have the binaries in their PATH
        sysconf_file = "/etc/sysconfig/condor-cron"
        try:
            sysconf = open(sysconf_file, 'w')
            if self.options['condor_location'].value:
                sysconf.write("PATH=%s/bin:%s/sbin:$PATH\n" % (condor_dir,
                                                               condor_dir))
                sysconf.write("export PATH\n")
            sysconf.close()
            self.log("Wrote %s", sysconf_file, level=logging.DEBUG)
        except IOError as err:
            self.log("Error trying to write to file (%s): %s" % (sysconf_file, err))
            raise exceptions.ConfigureError

        # Adjust the Condor-Cron configuration
        conf_file = "/etc/condor-cron/config.d/condor_location"
        try:
            config = open(conf_file, 'w')
            if self.options['condor_location'].value:
                config.write("RELEASE_DIR = %s" % condor_dir)
            config.close()
            self.log("Wrote %s", conf_file, level=logging.DEBUG)
        except IOError as err:
            self.log("Error trying to write to file (%s): %s" % (conf_file, err))
            raise exceptions.ConfigureError

    def _validate_host_list(self, hosts, setting):
        """ Validate a list of hosts """
        ret = True
        for host in hosts:
            # Strip off the port
            hostname, port = utilities.split_host_port(host)
            if not validation.valid_domain(hostname):
                self.log("Invalid domain in [%s].%s: %s" % (self.config_section,
                                                            setting, host),
                         level=logging.ERROR)
                ret = False

            if port and re.search('[^0-9]', port):
                self.log("Invalid port in [%s].%s: %s" % (self.config_section,
                                                          setting, host),
                         level=logging.ERROR)
                ret = False

        return ret

    def _read_rsv_conf(self):
        """Return a ConfigParser with the contents of the rsv.conf file"""
        config = configparser.RawConfigParser()
        config.optionxform = str  # rsv.conf is case-sensitive

        if os.path.exists(self.rsv_conf):
            config.read(self.rsv_conf)

        if not config.has_section('rsv'):
            config.add_section('rsv')

        return config

    def _write_rsv_conf(self, config):
        """Write the contents of a ConfigParser back to the rsv.conf file"""
        config_fp = open(self.rsv_conf, 'w')
        try:
            config.write(config_fp)
            self.log("Wrote %s", self.rsv_conf, level=logging.DEBUG)
        finally:
            config_fp.close()

    def _configure_cert_info(self):
        """ Configure certificate information """

        config = self._read_rsv_conf()

        # Set the appropriate options in the rsv.conf file
        if self.use_service_cert:
            config.set('rsv', 'service-cert', self.options['service_cert'].value)
            config.set('rsv', 'service-key', self.options['service_key'].value)
            config.set('rsv', 'service-proxy', self.options['service_proxy'].value)
        else:
            config.set('rsv', 'proxy-file', self.options['user_proxy'].value)

            # Remove these keys or they will override the proxy-file setting in rsv-control
            config.remove_option('rsv', 'service-cert')
            config.remove_option('rsv', 'service-key')
            config.remove_option('rsv', 'service-proxy')

        if self.options['legacy_proxy'].value:
            config.set('rsv', 'legacy-proxy', 'True')
        else:
            config.remove_option('rsv', 'legacy-proxy')

        self._write_rsv_conf(config)

    def _configure_default_ce_type(self):
        """Set the ce-type in rsv.conf to htcondor-ce.
        The setting may be overridden in probe-specific configs (set by _configure_ce_types for example)

        """
        config = self._read_rsv_conf()

        config.set('rsv', 'ce-type', 'htcondor-ce')

        self._write_rsv_conf(config)

    def _configure_ce_types(self):
        """Write config files that set the ce-type for HTCondor-CE hosts.

        :raise ConfigFailed: if writing any config file failed.

        """
        if self.htcondor_gateway_enabled:
            for host in self._htcondor_ce_hosts:
                self._configure_ce_type_for_host(host)

    def _configure_ce_type_for_host(self, hostname):
        """Write config file that sets the ce-type for all probes on a host.
        Specifically, a directory is created (if missing) under the metrics config
        dir for that host, and an allmetrics.conf file is placed into it.
        An existing allmetrics.conf for the host will be parsed and rewritten;
        comments inside it will be lost.

        :param hostname: FQDN of the host to configure probes for
        :type hostname: str
        :raise ConfigFailed: if writing the config file failed
        :rtype: None

        """
        host_metrics_dir = os.path.join(self.rsv_metrics_dir, hostname)
        allmetrics_conf_path = os.path.join(host_metrics_dir, "allmetrics.conf")

        try:
            os.mkdir(host_metrics_dir)
        except OSError:
            pass  # Dir already exists.

        config = configparser.RawConfigParser()
        config.optionxform = str  # Conf is case-sensitive.

        config.read(allmetrics_conf_path)  # Does nothing if the file can't be read.

        if not config.has_section('allmetrics'):
            config.add_section('allmetrics')
        config.set('allmetrics', 'ce-type', 'htcondor-ce')

        config_fp = open(allmetrics_conf_path, 'w')
        try:
            try:
                config.write(config_fp)
                self.log("Wrote %s", allmetrics_conf_path, level=logging.DEBUG)
            except EnvironmentError as err:
                self.log("Error writing to %s: %s" % (allmetrics_conf_path, str(err)), level=logging.ERROR)
                raise exceptions.ConfigureError
        finally:
            config_fp.close()

    def _configure_consumers(self):
        """ Enable the appropriate consumers """

        # The current logic is:
        #  - we ALWAYS want the html-consumer if we are told to install consumers
        #  - we NEVER want the gratia-consumer
        #  - we want the nagios-consumer if enable_nagios is True
        #  - we want the zabbix-consumer if enable_zabbix is True and rsv-consumers-zabbix is installed

        consumers = ["html-consumer"]

        if self.opt_val("enable_gratia"):
            self.log("Your configuration has enabled the Gratia consumer but the service which the Gratia consumer "
                     "reports to has been shut down. Please turn off 'enable_gratia' in the RSV section. "
                     "Gratia consumer configuration will be ignored.",
                     level=logging.WARNING)

        if self.options['enable_nagios'].value:
            consumers.append("nagios-consumer")
            self._configure_nagios_files()

        if self.options['enable_zabbix'].value:
            if not utilities.rpm_installed('rsv-consumers-zabbix'):
                self.log('Your configuration has enabled the Zabbix consumer '
                         'but rsv-consumers-zabbix is not installed. Zabbix consumer configuration will be ignored.',
                         level=logging.WARNING)
            else:
                consumers.append("zabbix-consumer")
                self._configure_zabbix_files()

        consumer_list = " ".join(consumers)
        self.log("Enabling consumers: %s " % consumer_list)

        if not utilities.run_script([self.rsv_control, "-v0", "--enable"] + consumers):
            raise exceptions.ConfigureError
        utilities.run_script([self.rsv_control, "-v0", "--disable", "gratia-consumer"])  # don't care if this fails

    def _configure_nagios_files(self):
        """ Store the nagios configuration """

        # The Nagios conf file contains a password so set it to mode 0400 owned by rsv
        pw_file = os.path.join(self.rsv_conf_dir, 'rsv-nagios.conf')
        os.chown(pw_file, self.uid, self.gid)
        os.chmod(pw_file, 0o400)

        # Add the configuration file
        nagios_conf_file = os.path.join(self.rsv_conf_dir, 'consumers/nagios-consumer.conf')
        config = configparser.RawConfigParser()
        config.optionxform = str

        if os.path.exists(nagios_conf_file):
            config.read(nagios_conf_file)

        if not config.has_section('nagios-consumer'):
            config.add_section('nagios-consumer')

        args = "--conf-file %s" % pw_file
        if self.options['nagios_send_nsca'].value:
            args += " --send-nsca"

        config.set("nagios-consumer", "args", args)

        config_fp = open(nagios_conf_file, 'w')
        config.write(config_fp)
        config_fp.close()
        self.log("Wrote %s", nagios_conf_file, level=logging.DEBUG)

    def _configure_zabbix_files(self):
        """ Store the zabbix configuration """

        rsv_zabbix_file = os.path.join(self.rsv_conf_dir, 'rsv-zabbix.conf')

        # Add the configuration file
        zabbix_conf_file = os.path.join(self.rsv_conf_dir, 'consumers/zabbix-consumer.conf')
        config = configparser.RawConfigParser()
        config.optionxform = str

        if os.path.exists(zabbix_conf_file):
            config.read(zabbix_conf_file)

        if not config.has_section('zabbix-consumer'):
            config.add_section('zabbix-consumer')

        args = "--conf-file %s" % rsv_zabbix_file
        if self.options['zabbix_use_sender'].value:
            args += " --zabbix-sender"

        config.set("zabbix-consumer", "args", args)

        config_fp = open(zabbix_conf_file, 'w')
        config.write(config_fp)
        config_fp.close()
        self.log("Wrote %s", zabbix_conf_file, level=logging.DEBUG)

    def load_rsv_meta_files(self):
        """ All the RSV meta files are in INI format.  Pull them in so that we know what
        metrics to enable """

        if not os.path.exists(self.rsv_meta_dir):
            self.log("In RSV configuration, meta dir (%s) does not exist." % self.rsv_meta_dir)
            return

        files = os.listdir(self.rsv_meta_dir)

        for filename in files:
            if re.search('\.meta$', filename):
                self._meta.read(os.path.join(self.rsv_meta_dir, filename))

    def split_2d_list(self, item_list):
        """
        Split a comma/whitespace separated item_list of item_list of items.
        Each item_list needs to be enclosed in parentheses and separated by whitespace and/or a comma.
        Parentheses are optional if only one item_list is supplied.

        Valid examples include:
        (1,2,3),(4,5)
        1,2,3,4,5
        (1,2), (4) , (5,6)  (8),    # comma at end is ok, comma between lists is optional

        Invalid examples:
        (1,2,3), 4    # 4 needs to be in parentheses
        1,2,3, (4,5)  # 1,2,3 needs to be parenthesized
        (1,2, (3, 4)  # missing a right parenthesis
        """

        if not item_list:
            return [[]]

        original_list = item_list

        # If there are no parentheses then just treat this like a normal comma-separated item_list
        # and return it as a 2-D array (with only one element in one direction)
        if not re.search("\(", item_list) and not re.search("\)", item_list):
            return [split_list(item_list)]

        # We want to grab parenthesized chunks
        pattern = re.compile("\s*\(([^()]+)\)\s*,?")
        array = []
        while 1:
            match = re.match(pattern, item_list)
            if not match:
                # If we don't have a match then we are either finished processing, or there is
                # a syntax error.  So if we have anything left in the string we will bail
                if re.search("\S", item_list):
                    self.log("ERROR: syntax error in parenthesized item_list",
                             level=logging.ERROR)
                    self.log("ERROR: Supplied item_list:\n\t%s" % original_list,
                             level=logging.ERROR)
                    self.log("ERROR: Leftover after parsing:\n\t%s" % item_list,
                             level=logging.ERROR)
                    return False
                else:
                    return array

            array.append(split_list(match.group(1)))

            # Remove what we just matched so that we get the next chunk on the next iteration
            match_length = len(match.group(0))
            item_list = item_list[match_length:]

        # We shouldn't reach here, but just in case...
        return array

    def _check_srm_settings(self):
        """
        Check srm settings to make sure settings are consistent and properly
        set
        """
        if (self._srm_hosts == [] or
                    self._srm_hosts is None or
                utilities.blank(self.options['srm_hosts'].value)):
            return True

        all_ok = True
        if self.options['srm_dir'].value.upper() == 'DEFAULT':
            self.log("srm_dir has to be set and can't be set to DEFAULT for each " +
                     "srm host defined (set to %s)" % dir,
                     option='srm_dir',
                     section='rsv',
                     level=logging.ERROR)
            all_ok = False

        srm_dirs = split_list(self.options['srm_dir'].value)
        if len(self._srm_hosts) != len(srm_dirs):
            self.log("When enabling SRM metrics you must specify the same number " +
                     "of entries in the srm_dir variable as you have in the " +
                     "srm_hosts section.  There are %i host entries and %i " \
                     "srm_dir entries." % (len(self._srm_hosts), len(srm_dirs)),
                     level=logging.ERROR)
            all_ok = False

        for directory in srm_dirs:
            if directory.upper() == 'DEFAULT':
                self.log("srm_dir has to be set and can't be set to DEFAULT for each " +
                         "srm host defined (set to %s)" % directory,
                         option='srm_dir',
                         section='rsv',
                         level=logging.ERROR)
                all_ok = False

        if not utilities.blank(self.options['srm_webservice_path'].value):
            srm_ws_paths = split_list(self.options['srm_webservice_path'].value)
            if len(self._srm_hosts) != len(srm_ws_paths):
                self.log("If you set srm_webservice_path when enabling SRM metrics " +
                         "you must specify the same number of entries in the " +
                         "srm_webservice_path variable as you have in the srm_hosts " +
                         "section.  There are %i host entries and %i " \
                         "srm_webservice_path entries." % (len(self._srm_hosts),
                                                           len(srm_ws_paths)),
                         level=logging.ERROR)
                all_ok = False

        return all_ok

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """

        if not self.enabled or self.ignored:
            return set()

        return {'rsv', 'condor-cron'}

    def _configure_condor_cron_ids(self):
        """Ensure UID/GID of cndrcron user is valid and is in the condor-cron configs
        :raise ConfigFailed: if modifying condor-cron configs failed

        """
        # check the uid/gid in the condor_ids file
        condor_id_fname = "/etc/condor-cron/config.d/condor_ids"
        ids = open(condor_id_fname, "r", encoding="latin-1").read()
        id_regex = re.compile(r'^\s*CONDOR_IDS\s+=\s+(\d+)\.(\d+).*', re.MULTILINE)
        condor_ent = pwd.getpwnam('cndrcron')
        match = id_regex.search(ids)
        if ((match is not None) and
                (((int(match.group(1)) != condor_ent.pw_uid) or
                      (int(match.group(2)) != condor_ent.pw_gid)))):
            self.log("Condor-cron uid/gid not correct, correcting",
                     level=logging.ERROR)
            (ids, count) = id_regex.subn("CONDOR_IDS  = %s.%s" % (condor_ent.pw_uid,
                                                                  condor_ent.pw_gid),
                                         ids,
                                         1)
            if count == 0:
                self.log("Can't correct condor-cron uid/gid, please double check",
                         level=logging.ERROR)
            if not utilities.atomic_write(condor_id_fname, ids, encoding="latin-1"):
                raise exceptions.ConfigureError
        elif match is None:
            ids += "CONDOR_IDS = %d.%d\n" % (condor_ent.pw_uid, condor_ent.pw_gid)
            if not utilities.atomic_write(condor_id_fname, ids, encoding="latin-1"):
                raise exceptions.ConfigureError


def split_list(item_list):
    """ Split a comma separated list of items """

    # Special case - when the list just contains UNAVAILABLE we want to ignore it
    if utilities.blank(item_list):
        return []

    items = []
    for entry in item_list.split(','):
        items.append(entry.strip())

    return items


def exclude_blank(item_list):
    """Return a copy of a list with blank values removed"""
    return [item for item in item_list if not utilities.blank(item)]


def split_list_exclude_blank(item_list):
    """Split a comma-separated list of items, returning non-blanks only"""
    return exclude_blank(split_list(item_list))
