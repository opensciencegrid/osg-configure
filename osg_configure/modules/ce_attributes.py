# BATCH_SYSTEMS here is both the config sections for the batch systems
# and the values in the OSG_BatchSystems attribute since they are
# coincidentally the same. If they ever change, make a mapping.
from configparser import ConfigParser
from typing import Dict

from osg_configure.modules import utilities, subcluster
from osg_configure.modules.exceptions import SettingError

BATCH_SYSTEMS_CASE_MAP = {
    'condor': 'Condor',
    'lsf': 'LSF',
    'pbs': 'PBS',
    'sge': 'SGE',
    'slurm': 'SLURM',
}
BATCH_SYSTEMS = list(BATCH_SYSTEMS_CASE_MAP.values())


def empty_if_blank(value: str) -> str:
    return "" if utilities.blank(value) else value


def get_resource_from_config(config: ConfigParser) -> str:
    return utilities.classad_quote(
        empty_if_blank(
            config.get("Site Information", "resource", fallback="")
        )
    )


def get_resource_group_from_config(config: ConfigParser) -> str:
    return utilities.classad_quote(
        empty_if_blank(
            config.get("Site Information", "resource_group", fallback="")
        )
    )


def get_batch_systems_from_config(config: ConfigParser) -> str:
    batch_systems = []

    siteinfo_batch_systems = config.get("Site Information", "batch_systems", fallback=None)
    if siteinfo_batch_systems is not None:
        # Site Information.batch_systems specified -- this one wins
        split_batch_systems = utilities.split_comma_separated_list(siteinfo_batch_systems)
        for batch_system in split_batch_systems:
            try:
                batch_systems.append(BATCH_SYSTEMS_CASE_MAP[batch_system.lower()])
            except KeyError:
                raise SettingError("Unrecognized batch system %s" % batch_system)
    else:
        # Add each batch system that's enabled from the sections in the 20-*.ini files.
        for batch_system in BATCH_SYSTEMS:
            if batch_system in config:
                if config.getboolean(section=batch_system, option="enabled", fallback=None):
                    batch_systems.append(batch_system)

        # Special case: Bosco (see SOFTWARE-3720); use the Bosco.batch argument.
        if config.getboolean("Bosco", "enabled", fallback=False):
            bosco_batch = config.get("Bosco", "batch", fallback=None)
            if bosco_batch:
                try:
                    batch_systems.append(BATCH_SYSTEMS_CASE_MAP[bosco_batch.lower()])
                except KeyError:
                    raise SettingError("Unrecognized batch system %s in Bosco section" % bosco_batch)

    return utilities.classad_quote(",".join(batch_systems))


def get_resource_catalog_from_config(config: ConfigParser) -> str:
    return subcluster.resource_catalog_from_config(config, default_allowed_vos=[]).format_value()


def get_attributes(config: ConfigParser) -> Dict[str, str]:
    """Turn config from .ini files into a dict of condor settings.

    """
    attributes = {}

    resource = get_resource_from_config(config)
    if resource and resource != '""':
        attributes["OSG_Resource"] = resource

    resource_group = get_resource_group_from_config(config)
    if resource_group and resource_group != '""':
        attributes["OSG_ResourceGroup"] = resource_group

    batch_systems = get_batch_systems_from_config(config)
    if batch_systems and batch_systems != '""':
        attributes["OSG_BatchSystems"] = batch_systems

    resource_catalog = get_resource_catalog_from_config(config)
    if resource_catalog and resource_catalog != "{}":
        attributes["OSG_ResourceCatalog"] = resource_catalog

    return attributes


def get_ce_attributes_str(
        config: ConfigParser,
) -> str:
    attributes = get_attributes(config)
    attributes["SCHEDD_ATTRS"] = "$(SCHEDD_ATTRS), " + ", ".join(attributes.keys())
    return "\n".join(f"{key} = {value}" for key, value in attributes.items())
