import re
import utilities


class ResourceCatalog(object):
  def __init__(self):
    self.entries = []

  def add_entry(self, name, cpus, memory, allowed_vos=None):
    if not name:
      raise ValueError("Required parameter 'name' must be specified")
    # These statements can raise TypeError or ValueError but that's ok
    cpus = int(cpus)
    memory = int(memory)
    if not cpus > 0:
      raise ValueError("Parameter 'cpus' out of range at %r; must be > 0" % cpus)
    if not memory > 0:
      raise ValueError("Parameter 'memory' out of range at %r; must be > 0" % memory)

    if isinstance(allowed_vos, str):
      allowed_vos = re.split('[ ,]+', allowed_vos)

    lines = ['  [',
             '    Name = %s;' % utilities.classad_quote(name),
             '    CPUs = %d;' % cpus,
             '    Memory = %d;' % memory]

    requirements_clauses = ['RequestCPUs <= CPUs', 'RequestMemory <= Memory']

    if allowed_vos:
      vo_clauses = ['VO == %s' % utilities.classad_quote(vo) for vo in allowed_vos if vo]
      requirements_clauses.append("(%s)" % " || ".join(vo_clauses))

    if requirements_clauses:
      lines.append('    Requirements = %s;' % ' && '.join(requirements_clauses))

    lines.append('  ]')

    self.entries.append(' \\\n'.join(lines))

    return self

  def compose_text(self):
    if not self.entries:
      catalog = '{}'
    else:
      catalog = ( '{ \\\n'
                + ', \\\n'.join(self.entries)
                + ' \\\n}' )

    return 'OSG_ResourceCatalog = ' + catalog
