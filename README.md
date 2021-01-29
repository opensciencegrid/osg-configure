OSG-Configure
=============

OSG-Configure is a tool to configure multiple pieces of Grid software from a single set of configuration files.


Installation
------------

OSG-Configure is typically installed via RPMs from the OSG repositories.
See [OSG documentation for how to enable the repositories](https://opensciencegrid.org/docs/common/yum/);
once the repos are enabled, install by running

    yum install osg-configure


OSG-Configure can also be installed from a checkout.
Run

    git clone https://github.com/opensciencegrid/osg-configure
    cd osg-configure
    make install

**NOTE:** this will overwrite existing config files in `/etc/osg/config.d`;
to install only the program, instead of `make install`, run

    make install-noconfig


Invocation and script usage
---------------------------

The `osg-configure` script is used to process the INI files and apply changes to the system.
`osg-configure` must be run as root.

The typical workflow of OSG-Configure is to first edit the INI files, then verify them, then apply the changes.

To verify the config files, run:
``` console
[root@server] osg-configure -v
```

OSG-Configure will list any errors in your configuration, usually including the section and option where the problem is.
Potential problems are:

-   Required option not filled in
-   Invalid value
-   Syntax error
-   Inconsistencies between options

To apply changes, run:
``` console
[root@server] osg-configure -c
```

Errors are logged in `/var/log/osg/osg-configure.log`.
To get more detailed error information in the log, add `-d` to the `osg-configure` invocation.

OSG-Configure is split up into modules. Normally, all modules are run when calling `osg-configure`.
However, it is possible to run specific modules separately.
To see a list of modules, including whether they can be run separately, run:
``` console
[root@server] osg-configure -l
```
If the module can be run separately, specify it with the `-m <MODULE>` option, where `<MODULE>` is one of the items
of the output of the previous command.

``` console
[root@server] osg-configure -c -m <MODULE>
```

Options may be specified in multiple INI files, which may make it hard to determine which value OSG-Configure uses.
You may query the final value of an option via one of these methods:
``` console
[root@server] osg-configure -q -o <OPTION>
[root@server] osg-configure -q -o <SECTION>.<OPTION>
```

Where `<OPTION>` is the variable from which we want to know the value and `<SECTION>` refers to a section in any of the INI
files, i.e. any name between brackets e.g. `[Squid]`.



### Conventions ###

In the tables below:

-   Mandatory options for a section are given in **bold** type. Sometime the default value may be OK and no edit required, but the variable has to be in the file.
-   Options that are not found in the default ini file are in *italics*.



Syntax and layout
-----------------

The configuration files used by `osg-configure` are the one supported by Python's [SafeConfigParser](https://docs.python.org/library/configparser.html), similar in format to the [INI configuration file](https://en.wikipedia.org/wiki/INI_file) used by MS Windows:

-   Config files are separated into sections, specified by a section name in square brackets (e.g. `[Section 1]`)
-   Options should be set using `name = value` pairs
-   Lines that begin with `;` or `#` are comments
-   Long lines can be split up using continutations: each white space character can be preceded by a newline to fold/continue the field on a new line (same syntax as specified in [email RFC 822](https://tools.ietf.org/html/rfc822.html))
-   Variable substitutions are supported -- [see below](#variable-substitution)

`osg-configure` reads and uses all of the files in `/etc/osg/config.d` that have a ".ini" suffix. The files in this directory are ordered with a numeric prefix with higher numbers being applied later and thus having higher precedence (e.g. `00-foo.ini` has a lower precedence than `99-local-site-settings.ini`). Configuration sections and options can be specified multiple times in different files. E.g. a section called `[PBS]` can be given in `20-pbs.ini` as well as `99-local-site-settings.ini`.

Each of the files are successively read and merged to create a final configuration that is then used to configure OSG software. Options and settings in files read later override the ones in previous files. This allows admins to create a file with local settings (e.g. `99-local-site-settings.ini`) that can be read last and which will be take precedence over the default settings in configuration files installed by various RPMs and which will not be overwritten if RPMs are updated.


### Variable substitution ###

The osg-configure parser allows variables to be defined and used in the configuration file:
any option set in a given section can be used as a variable in that section.  Assuming that you have set an option with the name `myoption` in the section, you can substitute the value of that option elsewhere in the section by referring to it as `%(myoption)s`.

**Note:**<br>
The trailing `s` is required. Also, option names cannot have a variable substitution in them.

### Special Settings ###

If a setting is set to UNAVAILABLE or DEFAULT or left blank, osg-configure will try to use a sensible default for setting if possible.

#### Ignore setting ####

The `enabled` option, specifying whether a service is enabled or not, is a boolean but also accepts `Ignore` as a possible value. Using Ignore, results in the service associated with the section being ignored entirely (and any configuration is skipped). This differs from using `False` (or the `%(disabled)s` variable), because using `False` results in the service associated with the section being disabled. `osg-configure` will not change the configuration of the service if the `enabled` is set to `Ignore`.

This is useful, if you have a complex configuration for a given that can't be set up using the ini configuration files. You can manually configure that service by hand editing config files, manually start/stop the service and then use the `Ignore` setting so that `osg-configure` does not alter the service's configuration and status.




Configuration sections
----------------------

The OSG configuration is divided into sections with each section starting with a section name in square brackets (e.g. `[Section 1]`).
The configuration is split in multiple files and options form one section can be in more than one files.
All of the configuration files listed below are in `/etc/osg/config.d/`.


### 01-squid.ini / [Squid] section ###

This section handles the configuration and setup of the squid web caching and proxy service.

This section is contained in `/etc/osg/config.d/01-squid.ini` which is provided by the `osg-configure-squid` RPM.

| Option      | Values Accepted           | Explanation                                                    |
|-------------|---------------------------|----------------------------------------------------------------|
| **enabled** | `True`, `False`, `Ignore` | This indicates whether the squid service is being used or not. |
| location    | String                    | This should be set to the `hostname:port` of the squid server. |


### 10-gateway.ini / [Gateway] section ###

This section gives information about the options in the Gateway section of the configuration files. These options control the behavior of job gateways on the CE. CEs are based on HTCondor-CE, which uses `condor-ce` as the gateway.

This section is contained in `/etc/osg/config.d/10-gateway.ini` which is provided by the `osg-configure-gateway` RPM.

| Option                         | Values Accepted | Explanation                                                                                                                                                                              |
|--------------------------------|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **htcondor\_gateway\_enabled** | `True`, `False` | (default True). True if the CE is using HTCondor-CE, False otherwise. HTCondor-CE will be configured to support enabled batch systems. RSV will use HTCondor-CE to launch remote probes. |
| **job\_envvar\_path**          | String          | The value of the PATH environment variable to put into HTCondor jobs running with HTCondor-CE. This value is ignored if not using that batch system/gateway combination.                 |


### 10-misc.ini / [Misc Services] section ###

This section handles the configuration of services that do not have a dedicated section for their configuration.

This section is contained in `/etc/osg/config.d/10-misc.ini` which is provided by the `osg-configure-misc` RPM.

This section primarily deals with authentication/authorization. For information on suggested settings for your CE, see the [authentication section of the HTCondor-CE install documents](../compute-element/install-htcondor-ce#configuring-authentication).

| Option                                | Values Accepted                       | Explanation                                                                                                                                                                                                                                                                                                                                                                          |
|---------------------------------------|---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **authorization\_method**             | `gridmap`, `local-gridmap`, `vomsmap` | This indicates which authorization method your site uses.                                                                                                                                                                                                                                                                                    |
| edit\_lcmaps\_db                      | `True`, `False`                       | (Optional, default True) If true, osg-configure will overwrite `/etc/lcmaps.db` to set your authorization method. The previous version will be backed up to `/etc/lcmaps.db.pre-configure`                                                                                                                                                                                           |
| all\_fqans                            | `True`, `False`                       | (Optional, default False) If true, vomsmap auth will use all VOMS FQANs of a proxy for mapping -- see [documentation](../security/lcmaps-voms-authentication#mapping-using-all-fqans)                                                                                                                                                                                                |


### 10-storage.ini / [Storage] section ###

This section gives information about the options in the Storage section of the configuration file.
Several of these values are constrained and need to be set in a way that is consistent with one of the OSG storage models.
Please review the OSG documentation on the [Worker Node Environment](https://opensciencegrid.org/docs/worker-node/using-wn/#the-worker-node-environment),
and [Site Planning](https://opensciencegrid.org/docs/site-planning/).

This section is contained in `/etc/osg/config.d/10-storage.ini` which is provided by the `osg-configure-ce` RPM.

| Option           | Values Accepted | Explanation                                                                                                                                                                                                    |
|------------------|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **se_available** | `True`, `False` | This indicates whether there is an associated SE available.                                                                                                                                                    |
| default_se       | String          | If an SE is available at your cluster, set default_se to the hostname of this SE, otherwise set default_se to UNAVAILABLE.                                                                                     |
| **grid_dir**     | String          | This setting should point to the directory which holds the files from the OSG worker node package. See note                                                                                                    |
| **app_dir**      | String          | This setting should point to the directory which contains the VO specific applications. See note                                                                                                               |
| data_dir         | String          | This setting should point to a directory that can be used to store and stage data in and out of the cluster. See note                                                                                          |
| worker_node_temp | String          | This directory should point to a directory that can be used as scratch space on compute nodes. If not set, the default is UNAVAILABLE. See note                                                                |
| site_read        | String          | This setting should be the location or url to a directory that can be read to stage in data via the variable `$OSG_SITE_READ`. This is an url if you are using a SE. If not set, the default is UNAVAILABLE    |
| site_write       | String          | This setting should be the location or url to a directory that can be write to stage out data via the variable `$OSG_SITE_WRITE`. This is an url if you are using a SE. If not set, the default is UNAVAILABLE |


**Note:**<br>
The above variables may be set to an environment variable that is set on your site's worker nodes.
For example, if each of your worker nodes has a different location for its scratch directory specified by
`LOCAL_SCRATCH_DIR`, set the following configuration:

    [Storage]
    worker_node_temp = $LOCAL_SCRATCH_DIR

**Note for grid_dir:**<br>
If you have installed the worker node client via RPM (the normal case) it should be `/etc/osg/wn-client`.
If you have installed the worker node in a special location (perhaps via the worker node client tarball or via OASIS),
it should be the location of that directory.

This directory will be accessed via the `$OSG_GRID` environment variable.
It should be visible on all of the compute nodes. Read access is required,
though worker nodes don't need write access.

**Note for app_dir:**<br>
This directory will be accesed via the `$OSG_APP` environment variable. It
should be visible on both the CE and worker nodes. Only the CE needs to
have write access to this directory. This directory must also contain a
sub-directory `etc/` with 1777 permissions.

This directory may also be in OASIS, in which case set `app_dir` to
`/cvmfs/oasis.opensciencegrid.org`. (The CE does not need write access in
that case.)

**Note for data_dir:**<br>
This directory can be accessed via the `$OSG_DATA` environment variable. It
should be readable and writable on both the CE and worker nodes.

**Note for worker_node_temp:**<br>
This directory will be accessed via the `$OSG_WN_TMP` environment variable.
It should allow read and write access on a worker node and can be visible
to just that worker node.

### 20-bosco.ini / [Bosco] section ###

This section is contained in `/etc/osg/config.d/20-bosco.ini` which is provided by the `osg-configure-bosco` RPM.

| Option       | Values Accepted           | Explanation                                                                                                                                                                                                                                                                                                                   |
|--------------|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **enabled**  | `True`, `False`, `Ignore` | This indicates whether the Bosco jobmanager is being used or not.                                                                                                                                                                                                                                                             |
| **users**    | String                    | A comma separated string. The existing usernames on the CE for which to install Bosco and allow submissions. In order to have separate usernames per VO, for example the CMS VO to have the cms username, each user must have Bosco installed. The osg-configure service will install Bosco on each of the users listed here. |
| **endpoint** | String                    | The remote cluster submission host for which Bosco will submit jobs to the scheduler. This is in the form of <user@example.com>, exactly as you would use to ssh into the remote cluster.                                                                                                                                     |
| **batch**    | String                    | The type of scheduler installed on the remote cluster.                                                                                                                                                                                                                                                                        |
| **ssh\_key** | String                    | The location of the ssh key, as created above.                                                                                                                                                                                                                                                                                |


### 20-condor.ini / [Condor] section ###

This section describes the parameters for a Condor jobmanager if it's being used in the current CE installation.
If Condor is not being used, the `enabled` setting should be set to `False`.

This section is contained in `/etc/osg/config.d/20-condor.ini` which is provided by the `osg-configure-condor` RPM.

| Option            | Values Accepted           | Explanation                                                                                                                                                                                                                                                                                                                            |
|-------------------|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **enabled**       | `True`, `False`, `Ignore` | This indicates whether the Condor jobmanager is being used or not.                                                                                                                                                                                                                                                                     |
| condor\_location  | String                    | This should be set to be directory where condor is installed. If this is set to a blank variable, DEFAULT or UNAVAILABLE, the `osg-configure` script will try to get this from the CONDOR\_LOCATION environment variable if available otherwise it will use `/usr` which works for the RPM installation.                               |
| condor\_config    | String                    | This should be set to be path where the condor\_config file is located. If this is set to a blank variable, DEFAULT or UNAVAILABLE, the `osg-configure` script will try to get this from the CONDOR\_CONFIG environment variable if available otherwise it will use `/etc/condor/condor_config`, the default for the RPM installation. |


### 20-lsf.ini / [LSF] section ###

This section describes the parameters for a LSF jobmanager if it's being used in the current CE installation. If LSF is not being used, the `enabled` setting should be set to `False`.

This section is contained in `/etc/osg/config.d/20-lsf.ini` which is provided by the `osg-configure-lsf` RPM.

| Option             | Values Accepted           | Explanation                                                     |
|--------------------|---------------------------|-----------------------------------------------------------------|
| **enabled**        | `True`, `False`, `Ignore` | This indicates whether the LSF jobmanager is being used or not. |
| lsf\_location      | String                    | This should be set to be directory where lsf is installed       |


### 20-pbs.ini / [PBS] section ###

This section describes the parameters for a pbs jobmanager if it's being used in the current CE installation. If PBS is not being used, the `enabled` setting should be set to `False`.

This section is contained in `/etc/osg/config.d/20-pbs.ini` which is provided by the `osg-configure-pbs` RPM.

| Option                         | Values Accepted           | Explanation                                                                                                                               |
|--------------------------------|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **enabled**                    | `True`, `False`, `Ignore` | This indicates whether the PBS jobmanager is being used or not.                                                                           |
| pbs\_location                  | String                    | This should be set to be directory where pbs is installed. osg-configure will try to loocation for the pbs binaries in pbs\_location/bin. |
| **accounting\_log\_directory** | String                    | This setting is used to tell Gratia where to find your accounting log files, and it is required for proper accounting.                    |
| pbs\_server                    | String                    | This setting is optional and should point to your PBS server node if it is different from your OSG CE                                     |


### 20-sge.ini / [SGE] section ###

This section describes the parameters for a SGE jobmanager if it's being used in the current CE installation. If SGE is not being used, the `enabled` setting should be set to `False`.

This section is contained in `/etc/osg/config.d/20-sge.ini` which is provided by the `osg-configure-sge` RPM.

| Option            | Values Accepted           | Explanation                                                                                                                                                            |
|-------------------|---------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **enabled**       | `True`, `False`, `Ignore` | This indicates whether the SGE jobmanager is being used or not.                                                                                                        |
| **sge\_root**     | String                    | This should be set to be directory where sge is installed (e.g. same as **$SGE\_ROOT** variable).                                                                      |
| **sge\_cell**     | String                    | The sge\_cell setting should be set to the value of $SGE\_CELL for your SGE install.                                                                                   |
| default\_queue    | String                    | This setting determines queue that jobs should be placed in if the job description does not specify a queue.                                                           |
| available\_queues | String                    | This setting indicates which queues are available on the cluster and should be used for validation when `validate_queues` is set.                                      |
| validate\_queues  | String                    | This setting determines whether the globus jobmanager should check the job RSL and verify that any queue specified matches a queue available on the cluster. See note. |

**Note for validate_queues**:<br>
If `available_queues` is set, that list of queues will be used for
validation, otherwise SGE will be queried for available queues.


### 20-slurm.ini / [Slurm] section ###

This section describes the parameters for a Slurm jobmanager if it's being used in the current CE installation. If Slurm is not being used, the `enabled` setting should be set to `False`.

This section is contained in `/etc/osg/config.d/20-slurm.ini` which is provided by the `osg-configure-slurm` RPM.

| Option              | Values Accepted           | Explanation                                                                                                                                       |
|---------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **enabled**         | `True`, `False`, `Ignore` | This indicates whether the Slurm jobmanager is being used or not.                                                                                 |
| **slurm\_location** | String                    | This should be set to be directory where slurm is installed. osg-configure will try to location for the slurm binaries in slurm\_location/bin.    |
| db\_host            | String                    | Hostname of the machine hosting the SLURM database. This information is needed to configure the SLURM gratia probe.                               |
| db\_port            | String                    | Port of where the SLURM database is listening. This information is needed to configure the SLURM gratia probe.                                    |
| db\_user            | String                    | Username used to access the SLURM database. This information is needed to configure the SLURM gratia probe.                                       |
| db\_pass            | String                    | The location of a file containing the password used to access the SLURM database. This information is needed to configure the SLURM gratia probe. |
| db\_name            | String                    | Name of the SLURM database. This information is needed to configure the SLURM gratia probe.                                                       |
| slurm\_cluster      | String                    | The name of the Slurm cluster                                                                                                                     |


### 30-gratia.ini / [Gratia] section ###

This section configures Gratia. If `probes` is set to `UNAVAILABLE`, then `osg-configure` will use appropriate default values. If you need to specify custom reporting (e.g. a local gratia collector) in addition to the default probes, `%(osg-jobmanager-gratia)s`, `%(osg-gridftp-gratia)s`, `%(osg-metric-gratia)s`, `%(itb-jobmanager-gratia)s`, `%(itb-gridftp-gratia)s`, `%(itb-metric-gratia)s` are defined in the default configuration files to make it easier to specify the standard osg reporting.

This section is contained in `/etc/osg/config.d/30-gratia.ini` which is provided by the `osg-configure-gratia` RPM.

| Option       | Values Accepted            | Explanation                                                                                                                           |
|--------------|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| **enabled**  | `True` , `False`, `Ignore` | This should be set to True if gratia should be configured and enabled on the installation being configured.                           |
| **resource** | String                     | This should be set to the resource name as given in the OIM registration                                                              |
| **probes**   | String                     | This should be set to the gratia probes that should be enabled. A probe is specified by using as `[probe_type]:server:port`. See note |

**Note for probes:**<br>
Legal values for the `probe_type` part are:

-   `metric` (for RSV)
-   `jobmanager` (for the appropriate jobmanager probe)
-   `gridftp` (for the GridFTP transfer probe)


### 30-infoservices.ini / [Info Services] section ###

Reporting to the central CE Collectors is configured in this section.  In the majority of cases, this file can be left untouched; you only need to configure this section if you wish to report to your own CE Collector instead of the ones run by OSG Operations.

This section is contained in `/etc/osg/config.d/30-infoservices.ini`, which is provided by the `osg-configure-infoservices` RPM. (This is for historical reasons.)

| Option        | Values Accepted           | Explanation                                                       |
|---------------|---------------------------|-------------------------------------------------------------------|
| **enabled**   | `True`, `False`, `Ignore` | True if reporting should be configured and enabled                |
| ce_collectors | String                    | The server(s) HTCondor-CE information should be sent to. See note |

**Note for ce_collectors:**
-   Set this to `DEFAULT` to report to the OSG Production or ITB servers (depending on your [Site Information](#site-information) configuration).
-   Set this to `PRODUCTION` to report to the OSG Production servers
-   Set this to `ITB` to report to the OSG ITB servers
-   Otherwise, set this to the `hostname:port` of a host running a `condor-ce-collector` daemon


### 30-rsv.ini / [RSV] section ###

This section handles the configuration and setup of the RSV services.

This section is contained in `/etc/osg/config.d/30-rsv.ini` which is provided by the `osg-configure-rsv` RPM.

| Option               | Values Accepted           | Explanation                                                                                                                                                                                                                                                            |
|----------------------|---------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **enabled**          | `True`, `False`, `Ignore` | This indicates whether the rsv  service is being used or not.                                                                                                                                                                                                          |
| **rsv_user**         | String                    | This gives username that rsv will run under.  If this is blank or set to `UNAVAILABLE`, it will default to rsv.                                                                                                                                                        |
| **gratia_probes**    | String                    | This settings indicates which rsv gratia probes should be used.  It is a list of probes separated by a comma.  Valid probes are metric, condor, pbs, lsf, sge, managedfork, hadoop-transfer, and gridftp-transfer                                                      |
| ce_hosts             | String                    | This option lists the serviceURI of the CEs that generic RSV CE probes should check.  This should be a list of serviceURIs (`hostname[:port/service]`) separated by a comma (e.g. `my.host,my.host2,my.host3:2812`).                                                   |
| htcondor_ce_hosts    | String                    | This option lists the serviceURI of the HTCondor-CE-based CEs that the RSV HTCondor-CE probes should check. This should be a list of serviceURIs (`hostname[:port/service]`) separated by a comma (e.g. `my.host,my.host2,my.host3:2812`). |                           |
| gridftp_hosts        | String                    | This option lists the serviceURI of the GridFTP servers that the RSV GridFTP probes should check.  This should be a list of serviceURIs (`hostname[:port/service]`) separated by a comma (e.g. `my.host.iu.edu:2812,my.host2,my.host3`).                               |
| gridftp_dir          | String                    | This should be the directory that the GridFTP probes should use during testing.  This defaults to `/tmp` if left blank or set to `UNAVAILABLE`.                                                                                                                        |
| **srm_hosts**        | String                    | This option lists the serviceURI of the srm servers that the RSV srm probes should check.  This should be a list of serviceURIs (`hostname[:port/service]`) separated by a comma (e.g. `my.host,my.host2,my.host3:8444`).                                              |
| srm_dir              | String                    | This should be the directory that the srm probes should use during testing.                                                                                                                                                                                            |
| srm_webservice_path  | String                    | This option gives the webservice path that SRM probes need to use along with the host:port. See note.                                                                                                                                                                  |
| service_cert         | String                    | This option should point to the public key file (pem) for your service  certificate. If this is left blank or set to `UNAVAILABLE` and the `user_proxy` setting is set, it will default to `/etc/grid-security/rsvcert.pem`                                            |
| service_key          | String                    | This option should point to the private key file (pem) for your service  certificate. If this is left blank or set to `UNAVAILABLE` and the `service_cert` setting is enabled, it will default to `/etc/grid-security/rsvkey.pem` .                                    |
| service_proxy        | String                    | This should point to the location of the rsv proxy file. If this is left blank or set to `UNAVAILABLE` and the use_service_cert  setting is enabled, it will default to `/tmp/rsvproxy`.                                                                               |
| user_proxy           | String                    | If you don't use a service certificate for rsv, you will need to specify a  proxy file that RSV should use in the proxy_file setting.  If this is set, then  service_cert, service_key, and service_proxy should be left blank, or set to `UNAVAILABE` or `DEFAULT`.   |
| **setup_rsv_nagios** | `True`, `False`           | This option indicates whether rsv should upload results to a local  nagios server instance. This should be set to True or False.<br> This plugin is provided as an experimental component, and admins are recommend *not to enable* it on production resources.        |
| rsv_nagios_conf_file | String                    | This option indicates the location of the rsv nagios  file to use for configuration details. This file *needs to be configured locally for RSV-Nagios forwarding to work* -- see inline comments in file for more information.                                         |
| condor_location      | String                    | If you installed Condor in a non-standard location (somewhere other than /usr, which is where the RPM puts it)  you must specify the path to the install dir here.                                                                                                     |

**Note for srm_webservice_path:**<br>
For dcache installations, this should work if left blank. However
Bestman-xrootd SEs normally use `srm/v2/server` as web service path, and so
Bestman-xrootd admins will have to pass this option with the appropriate
value (for example: `srm/v2/server`) for the SRM probes to pass on their
SE.


### 30-gip.ini / [Subcluster] and [Resource Entry] sections ###

Subcluster and Resource Entry configuration is for reporting about the worker resources on your site. A **subcluster** is a homogeneous set of worker node hardware; a **resource** is a set of subcluster(s) with common capabilities that will be reported to the ATLAS AGIS system.

**At least one Subcluster or Resource Entry section** is required on a CE; please populate the information for all your subclusters. This information will be reported to a central collector and will be used to send GlideIns / pilot jobs to your site; having accurate information is necessary for OSG jobs to effectively use your resources.

This section is contained in `/etc/osg/config.d/30-gip.ini` which is provided by the `osg-configure-gip` RPM. (This is for historical reasons.)

This configuration uses multiple sections of the OSG configuration files:

-   [Subcluster\*](#subcluster-configuration): options about homogeneous subclusters
-   [Resource Entry\*](#resource-entry-configuration-atlas-only): options for specifying ATLAS queues for AGIS

#### Notes for multi-CE sites. ####

If you would like to properly advertise multiple CEs per cluster, make sure that you:

-   Set the value of site\_name in the "Site Information" section to be the same for each CE.
-   Have the **exact** same configuration values for the Subcluster\* and Resource Entry\* sections in each CE.


#### Subcluster Configuration ####

Each homogeneous set of worker node hardware is called a **subcluster**. For each subcluster in your cluster, fill in the information about the worker node hardware by creating a new Subcluster section with a unique name in the following format: `[Subcluster CHANGEME]`, where CHANGEME is the globally unique subcluster name (yes, it must be a **globally** unique name for the whole grid, not just unique to your site. Get creative.)

| Option               | Values Accepted             | Explanation                                                                   |
|----------------------|-----------------------------|-------------------------------------------------------------------------------|
| **name**             | String                      | The same name that is in the Section label; it should be **globally unique**  |
| **ram\_mb**          | Positive Integer            | Megabytes of RAM per node                                                     |
| **cores\_per\_node** | Positive Integer            | Number of cores per node                                                      |
| **allowed\_vos**     | Comma-separated List or `*` | The VOs that are allowed to run jobs on this subcluster (autodetected if `*`) |

The following attributes are optional:

| Option            | Values Accepted  | Explanation                                                                                                                |
|-------------------|------------------|----------------------------------------------------------------------------------------------------------------------------|
| max\_wall\_time   | Positive Integer | Maximum wall-clock time, in minutes, that a job is allowed to run on this subcluster. The default is 1440, or the equivalent of one day.
| queue             | String           | The queue to which jobs should be submitted in order to run on this subcluster                                             |
| extra\_transforms | Classad          | Transformation attributes which the HTCondor Job Router should apply to incoming jobs so they can run on this subcluster   |



#### Resource Entry Configuration (ATLAS only) ####

If you are configuring a CE for the ATLAS VO, you must provide hardware information to advertise the queues that are available to AGIS. For each queue, create a new `Resource Entry` section with a unique name in the following format: `[Resource Entry RESOURCE]` where RESOURCE is a globally unique resource name (it must be a **globally** unique name for the whole grid, not just unique to your site). The following options are required for the `Resource Entry` section and are used to generate the data required by AGIS:

| Option                                    | Values Accepted             | Explanation                                                                         |
|-------------------------------------------|-----------------------------|-------------------------------------------------------------------------------------|
| **name**                                  | String                      | The same name that is in the `Resource Entry` label; it must be **globally unique** |
| **max\_wall\_time**                       | Positive Integer            | Maximum wall-clock time, in minutes, that a job is allowed to run on this resource  |
| **queue**                                 | String                      | The queue to which jobs should be submitted to run on this resource                 |
| **cpucount** (alias **cores\_per\_node**) | Positive Integer            | Number of cores that a job using this resource can get                              |
| **maxmemory** (alias **ram\_mb**)         | Positive Integer            | Maximum amount of memory (in MB) that a job using this resource can get             |
| **allowed\_vos**                          | Comma-separated List or `*` | The VOs that are allowed to run jobs on this resource (autodetected if `*`)         |

The following attributes are optional:

| Option      | Values Accepted      | Explanation                                                                                                         |
|-------------|----------------------|---------------------------------------------------------------------------------------------------------------------|
| subclusters | Comma-separated List | The physical subclusters the resource entry refers to; must be defined as Subcluster sections elsewhere in the file |
| vo\_tag     | String               | An arbitrary label that is added to jobs routed through this resource                                               |



### 35-pilot.ini / [Pilot] ###

These sections describe the size and scale of GlideinWMS pilots that your site is willing to accept.
This file contains multiple sections of the form `[Pilot <PILOT_TYPE>]`,
where `<PILOT_TYPE>` is a free-form name of a type of pilot.
The name must be globally unique; we recommend including the resource name of your CE in the PILOT_TYPE.
For example, if your CE is registered in topology as `UW-ITB-CE1` and you are describing a type of pilot with 4 cores,
then use `UW-ITB-CE1_4CORE`.

The following attributes are required:
| Option                   | Values Accepted             | Explanation                                                                                                                        |
|--------------------------|-----------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| **allowed\_vos**         | Comma-separated List or `*` | The VOs that are allowed to run jobs on this resource (autodetected if `*`)                                                        |
| **max\_pilots**          | Positive Integer            | The maximum number of pilots of this type that the factory can send to this CE                                                     |
| **os**                   | Choice (see below)          | The operating system on the workers the pilot should request.  Not set by default.  Only required if **require\_singularity** is `False`               |
| **require\_singularity** | `True`, `False`             | `True` if the pilot should require Singularity support on any worker it lands on.  Default `False`; **os** is optional if this is `True` |

Valid values for the **os** option are: `rhel6`, `rhel7`, `rhel8`, or `ubuntu18`.

The following attributes are optional:
| Option              | Values Accepted      | Explanation                                                                                                                              |
|---------------------|----------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| **cpucount**        | Positive Integer     | Number of cores that a job using this type of pilot can get.  Default `1`; ignored if **whole\_node** is `True`                          |
| **ram\_mb**         | Positive Integer     | Maximum amount of memory (in MB) that a job using this type of pilot can get.  Default `2500`; ignored if **whole\_node** is `True`      |
| **whole\_node**     | `True`, `False`      | Whether this type of pilot can use all the resources on a node.  Default `False`; **cpucount** and **ram\_mb** are ignored if this is `True` |
| **gpucount**        | Non-negative Integer | The number of GPUs to request.  Default `0`                                                                                              |
| **max\_wall\_time** | Positive Integer     | Maximum wall-clock time, in minutes, that a job is allowed to run on this resource.  Default `1440`, i.e. 24 hours                       |
| **queue**           | String               | The queue or partition which jobs should be submitted to in order to run on this resource (see note).  Not set by default                |
| **send\_tests**     | `True`, `False`      | Send test pilots.  Default `False`; set it to `True` for testing job routes or pilot types                                               |

**Note:** **queue** is equivalent to the HTCondor grid universe classad attribute **remote\_queue**.




### 40-localsettings.ini / [Local Settings] ###

This section differs from other sections in that there are no set options in this section. Rather, the options set in this section will be placed in the `osg-local-job-environment.conf` verbatim. The options in this section are case sensitive and the case will be preserved when they are converted to environment variables. The `osg-local-job-environment.conf` file gets sourced by jobs run on your cluster so any variables set in this section will appear in the environment of jobs run on your system.

Adding a line such as `My_Setting = my_Value` would result in the an environment variable called `My_Setting` set to `my_Value` in the job's environment. `my_Value` can also be defined in terms of an environment variable (i.e `My_Setting = $my_Value`) that will be evaluated on the worker node. For example, to add a variable `MY_PATH` set to `/usr/local/myapp`, you'd have the following:

``` ini
[Local Settings]

MY_PATH = /usr/local/myapp
```

This section is contained in `/etc/osg/config.d/40-localsettings.ini` which is provided by the `osg-configure-ce` RPM.


### 40-siteinfo.ini / [Site Information] section ###

The settings found in the `Site Information` section are described below. This section is used to give information about a resource such as resource name, site sponsors, administrators, etc.

This section is contained in `/etc/osg/config.d/40-siteinfo.ini` which is provided by the `osg-configure-ce` RPM.

| Option              | Values Accepted   | Description                                                                                                                                  |
|---------------------|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **group**           | `OSG` , `OSG-ITB` | This should be set to either OSG or OSG-ITB.  "OSG" is for resources with "Production: True" in Topology, and "OSG-ITB" is for resources with "Production: False". Most sites should specify OSG |
| **host\_name**      | String            | This should be set to be hostname of the CE that is being configured                                                                         |
| **resource**        | String            | The resource name of this CE endpoint as registered in Topology.                                                                                  |
| **resource\_group** | String            | The resource\_group of this CE as registered in Topology.                                                                                         |
| **sponsor**         | String            | This should be set to the sponsor of the resource. See note.                                                                                 |
| **site\_policy**    | Url               | This should be a url pointing to the resource's usage policy                                                                                 |
| **contact**         | String            | This should be the name of the resource's admin contact                                                                                      |
| **email**           | Email address     | This should be the email address of the admin contact for the resource                                                                       |
| **city**            | String            | This should be the city that the resource is located in                                                                                      |
| **country**         | String            | This should be two letter country code for the country that the resource is located in.                                                      |
| **longitude**       | Number            | This should be the longitude of the resource. It should be a number between -180 and 180.                                                    |
| **latitude**        | Number            | This should be the latitude of the resource. It should be a number between -90 and 90.                                                       |

**Note for sponsor:**<br>
If your resource has multiple sponsors, you can separate them using commas or specify the percentage using the following format:
`osg, atlas, cms` or `osg:10, atlas:45, cms:45`.
The percentages must add up to 100 if multiple sponsors are used.
If you have a sponsor that is not an OSG VO, you can indicate this by using 'local' as the VO.
