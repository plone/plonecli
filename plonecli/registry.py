import pkg_resources
import os

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser


class SetupCfg(object):
    def __init__(self):
        self.template = None


def read_setup_cfg(root_folder):
    setup_cfg = SetupCfg()
    config = ConfigParser()
    path = root_folder + '/setup.cfg'
    config.read(path)
    if not config.has_section('tool:bobtemplates.plone'):
        return setup_cfg
    if not config.has_option('tool:bobtemplates.plone', 'template'):
        return setup_cfg
    setup_cfg.template = config.get('tool:bobtemplates.plone', 'template')
    return setup_cfg


def get_package_root_folder():
    file_name = 'setup.py'
    root_folder = None
    cur_dir = os.getcwd()
    while True:
        files = os.listdir(cur_dir)
        parent_dir = os.path.dirname(cur_dir)
        if file_name in files:
            root_folder = cur_dir
            break
        else:
            if cur_dir == parent_dir:
                break
            cur_dir = parent_dir
    return root_folder


class TemplateRegistry(object):

    def __init__(self):
        self.root_folder = get_package_root_folder()
        self.setup_cfg = read_setup_cfg(self.root_folder)
        self.templates = {}
        self.template_infos = {}
        for entry_point in pkg_resources.iter_entry_points('mrbob_templates'):
            template_info_method = entry_point.load()
            self.template_infos[entry_point.name] = template_info_method()

        for entry_point_name, tmpl_info in self.template_infos.items():
            if tmpl_info.depend_on:
                continue
            self.templates[entry_point_name] = {
                'template_name': tmpl_info.plonecli_alias or entry_point_name,
                'subtemplates': {},
            }

        for entry_point_name, tmpl_info in self.template_infos.items():
            if not tmpl_info.depend_on:
                continue
            if tmpl_info.depend_on not in self.templates:
                print('{Template dependency "{0}" not found!}'.format(
                    tmpl_info.depend_on))
                continue
            self.templates[tmpl_info.depend_on][
                'subtemplates'][entry_point_name] = tmpl_info.plonecli_alias \
                or entry_point_name

    def list_templates(self):
        templates_str = 'Templates:\n'
        for tmpl in self.templates.values():
            templates_str += " - {0}\n".format(tmpl['template_name'])
            subtemplates = tmpl.get('subtemplates', [])
            for subtmpl_name in subtemplates.values():
                templates_str += "  - {0}\n".format(subtmpl_name)
        return templates_str

    def get_templates(self):
        if self.root_folder:
            template = self.templates.get(self.setup_cfg.template)
            if not template:
                print("no subtemplates found for {0}!".format(
                    self.setup_cfg.template))
                return []
            return template['subtemplates'].values()
        return [tmpl['template_name'] for tmpl in self.templates.values()]

    def resolve_template_name(self, plonecli_alias):
        """ resolve template name from plonecli alias
        """
        template_name = None
        for entry_point, tmpl_info in self.template_infos.items():
            if tmpl_info.plonecli_alias == plonecli_alias:
                template_name = tmpl_info.template
        return template_name
