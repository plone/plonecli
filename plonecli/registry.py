import pkg_resources

from .utils import get_package_root_folder

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
    if not config.sections():
        return
    setup_cfg.version = config.get('tool:bobtemplates.plone', 'template')
    return setup_cfg


class TemplateRegistry(object):

    def __init__(self):
        self.templates = {}
        self.template_infos = {}
        for entry_point in pkg_resources.iter_entry_points('mrbob_templates'):
            template_info_method = entry_point.load()
            self.template_infos[entry_point.name] = template_info_method()

        for entry_point_name, tmpl_info in self.template_infos.items():
            if tmpl_info.depend_on:
                continue
            self.templates[entry_point_name] = {
                'template_name': entry_point_name,
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
                'subtemplates'][entry_point_name] = entry_point_name

    def list_templates(self):
        templates_str = 'Templates:\n'
        for tmpl in self.templates.values():
            templates_str += " - {0}\n".format(tmpl['template_name'])
            subtemplates = tmpl.get('subtemplates', [])
            for subtmpl_name in subtemplates:
                templates_str += "  - {0}\n".format(subtmpl_name)
        return templates_str

    def get_templates(self):
        root_folder = get_package_root_folder()
        if root_folder:
            setup_cfg = read_setup_cfg(root_folder)
            template = self.templates.get(setup_cfg.template)
            if not template:
                print("no subtemplates found for {0}!".format(
                    setup_cfg.template))
                return []
            return template['subtemplates']

        # read template name
        # lookup templates or subtemplates if setup.cfg was found
