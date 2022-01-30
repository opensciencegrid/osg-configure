# BATCH_SYSTEMS here is both the config sections for the batch systems
# and the values in the OSG_BatchSystems attribute since they are
# coincidentally the same. If they ever change, make a mapping.
BATCH_SYSTEMS_CASE_MAP = {
    'condor': 'Condor',
    'lsf': 'LSF',
    'pbs': 'PBS',
    'sge': 'SGE',
    'slurm': 'SLURM',
}
BATCH_SYSTEMS = list(BATCH_SYSTEMS_CASE_MAP.values())
