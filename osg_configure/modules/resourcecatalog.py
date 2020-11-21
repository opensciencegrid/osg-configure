import classad
import logging
from collections import namedtuple
from . import utilities

log = logging.getLogger(__name__)


def _noop(x):
    return x


def _extra_transforms_to_classad(extra_transforms):
    """Ensure extra_transforms is surrounded by exactly one pair of brackets
    so it can be parsed as a classad
    """
    return classad.parseOne('[' + extra_transforms.lstrip('[ \t').rstrip('] \t') + ']')


def _to_classad_list(a_list):
    return "{ " + ", ".join([utilities.classad_quote(it) for it in a_list if it]) + " }"


def _str_to_classad_list(a_str):
    return _to_classad_list(utilities.split_comma_separated_list(a_str))


class RCAttribute(namedtuple("RCAttribute", "rce_field classad_attr format_fn")):
    """The mapping of an RCEntry field to a classad attribute, with a format function"""


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

    def get_requirements(self, attributes):
        requirements_clauses = []
        if "CPUs" in attributes:
            requirements_clauses.append("TARGET.RequestCPUs <= CPUs")
        if "Memory" in attributes:
            requirements_clauses.append("TARGET.RequestMemory <= Memory")
        if "GPUs" in attributes:
            requirements_clauses.append('(TARGET.RequestGPUs ?: 0) <= GPUs')
        if "AllowedVOs" in attributes:
            requirements_clauses.append("member(TARGET.VO, AllowedVOs)")
        if "VOTag" in attributes:
            requirements_clauses.append(f"TARGET.VOTag == {attributes['VOTag']}")
        if self.extra_requirements:
            requirements_clauses.append(self.extra_requirements)

        if requirements_clauses:
            return ' && '.join(requirements_clauses)
        return None

    def get_transform(self, attributes):
        transform_classad = classad.ClassAd()
        if "CPUs" in attributes:
            transform_classad["set_xcount"] = "RequestCPUs"
        if "Memory" in attributes:
            transform_classad["set_MaxMemory"] = "RequestMemory"
        if "VOTag" in attributes:
            transform_classad["set_VOTag"] = attributes["VOTag"]
        if self.queue:
            transform_classad['set_remote_queue'] = utilities.classad_quote(self.queue)
        if self.extra_transforms:
            try:
                transform_classad.update(_extra_transforms_to_classad(self.extra_transforms))
            except SyntaxError as e:
                raise ValueError("Unable to parse 'extra_transforms': %s" % e)

        if transform_classad:
            transform = "["
            for key in sorted(transform_classad.keys()):
                transform += f" {key} = {transform_classad[key]};"
            transform += " ]"

            return transform
        return None

    def as_attributes(self):
        """Return this entry as a list of classad attributes"""
        attributes = {}

        for rce_field, classad_attr, format_fn in ATTRIBUTE_MAPPINGS:
            try:
                val = self.__getattribute__(rce_field)
                if val is not None:
                    attributes[classad_attr] = format_fn(val)
            except AttributeError:
                continue

        requirements = self.get_requirements(attributes)
        if requirements:
            attributes['Requirements'] = requirements
        transform = self.get_transform(attributes)
        if transform:
            attributes['Transform'] = transform

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
