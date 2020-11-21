import classad
import re
from collections import namedtuple
from . import utilities


def _noop(x):
    return x


def _munge_extra_transforms(extra_transforms):
    """Ensure extra_transforms is surrounded by exactly one pair of brackets
    so it can be parsed as a classad
    """
    return '[' + extra_transforms.lstrip('[ \t').rstrip('] \t') + ']'


def _to_classad_list(a_list):
    return "{ " + ", ".join([utilities.classad_quote(it) for it in a_list if it]) + " }"


def _str_to_classad_list(a_str):
    return _to_classad_list(utilities.split_comma_separated_list(a_str))


class RCAttribute(namedtuple("RCAttribute", "rce_field classad_attr transform")):
    """The mapping of an RCEntry field to a classad attribute, with a transform function"""


ATTRIBUTE_MAPPINGS = [
    RCAttribute("name", "Name", utilities.classad_quote),
    RCAttribute("cpus", "CPUs", int),
    RCAttribute("memory", "Memory", int),
    RCAttribute("allowed_vos", "AllowedVOs", _to_classad_list),
    RCAttribute("max_wall_time", "MaxWallTime", int),
    # queue is special
    RCAttribute("subclusters", "Subclusters", _to_classad_list),
    RCAttribute("vo_tag", "VOTag", utilities.classad_quote),
    # extra_requirements is special
    # extra_transforms is special
    RCAttribute("gpus", "GPUs", int),
    RCAttribute("max_pilots", "MaxPilots", int),
    RCAttribute("whole_node", "WholeNode", bool),
    RCAttribute("require_singularity", "RequireSingularity", bool),
    RCAttribute("os", "OS", utilities.classad_quote),
    RCAttribute("send_tests", "SendTests", bool),
]


class RCEntry(object):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.cpus = kwargs.get('cpus', 0)
        self.memory = kwargs.get('memory', 0)
        self.allowed_vos = kwargs.get('allowed_vos', None)
        self.max_wall_time = kwargs.get('max_wall_time', None)
        self.queue = kwargs.get('queue', '')
        self.subclusters = kwargs.get('subclusters', None)
        self.vo_tag = kwargs.get('vo_tag', None)
        self.extra_requirements = kwargs.get('extra_requirements', '')
        self.extra_transforms = kwargs.get('extra_transforms', '')
        self.gpus = kwargs.get('gpus', None)
        self.max_pilots = kwargs.get('max_pilots', None)
        self.whole_node = kwargs.get('whole_node', None)
        self.require_singularity = kwargs.get('require_singularity', None)
        self.os = kwargs.get('os', None)
        self.send_tests = kwargs.get('send_tests', None)

    def as_attributes(self):
        """Return this entry as a list of classad attributes"""
        attributes = {}

        for rce_field, classad_attr, transform in ATTRIBUTE_MAPPINGS:
            try:
                val = self.__getattribute__(rce_field)
                if val is not None:
                    attributes[classad_attr] = transform(val)
            except AttributeError:
                continue

        requirements_clauses = ['TARGET.RequestCPUs <= CPUs', 'TARGET.RequestMemory <= Memory']
        if self.gpus is not None:
            requirements_clauses.append('(TARGET.RequestGPUs ?: 0) <= GPUs')

        if self.extra_requirements:
            requirements_clauses.append(self.extra_requirements)

        if self.allowed_vos:
            requirements_clauses.append("member(TARGET.VO, AllowedVOs)")

        transform_classad = classad.parseOne('[set_xcount = RequestCPUs; set_MaxMemory = RequestMemory]')

        if attributes.get("VOTag"):
            requirements_clauses.append("TARGET.VOTag == " + attributes["VOTag"])
            transform_classad['set_VOTag'] = attributes["VOTag"]

        if self.queue:
            transform_classad['set_remote_queue'] = utilities.classad_quote(self.queue)
        if self.extra_transforms:
            try:
                extra_transforms_classad = classad.parseOne(_munge_extra_transforms(self.extra_transforms))
            except SyntaxError as e:
                raise ValueError("Unable to parse 'extra_transforms': %s" % e)
            transform_classad.update(extra_transforms_classad)
        attributes['Transform'] = '['
        for key in sorted(transform_classad.keys()):
            attributes['Transform'] += " %s = %s;" % (key, transform_classad[key])
        attributes['Transform'] += ' ]'

        attributes['Requirements'] = ' && '.join(requirements_clauses)

        return attributes



class ResourceCatalog(object):
    """Class for building an OSG_ResourceCatalog attribute in condor-ce configs for the ce-collector"""

    def __init__(self):
        self.entries = {}

    def add_rcentry(self, rcentry):
        self.entries[rcentry.name] = rcentry.as_attributes()

        return self

    def compose_text(self):
        """Return the OSG_ResourceCatalog classad attribute made of all the entries in this object"""
        if not self.entries:
            catalog = '{}'
        else:
            entry_texts = []
            for entrykey in sorted(self.entries):
                entry = self.entries[entrykey]
                entry_text = '  [ \\\n'
                for attribkey in sorted(entry):
                    entry_text += '    %s = %s; \\\n' % (attribkey, entry[attribkey])
                entry_text += '  ]'
                entry_texts.append(entry_text)
            catalog = ('{ \\\n'
                       + ', \\\n'.join(entry_texts)
                       + ' \\\n}')

        return 'OSG_ResourceCatalog = ' + catalog
