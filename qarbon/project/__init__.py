from __future__ import with_statement

import shutil
import os.path

from qarbon.util import isString

__init_template = """\
# -----------------------------------------------------------------------------
# This file is part of {project.project_name}
# {project.copyright}
# {project.license}
# -----------------------------------------------------------------------------

\"\"\"The package file. This is part of {project.project_name}\"\"\"
"""


def makeDirectory(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)


def createPackageTree(base_dir, tree, init_text=None):
    makeDirectory(base_dir)
    if init_text is not None:
        init_file_name = os.path.join(base_dir, "__init__.py")
        with open(init_file_name, 'w') as init_file:
            init_file.write(init_text)
    for node_info in tree:
        node_name, childs = node_info[0], node_info[1:]
        node_directory = os.path.join(base_dir, node_name)
        createPackageTree(node_directory, childs)


def clearName(name):
    for c in " \n\t":
        name = name.replace(c, "_")
    return name


class Project(object):

    def __init__(self, project_name, package_name=None, base_directory=None):
        self.project_name = project_name
        if package_name is None:
            package_name = clearName(project_name.lower())
        self.package_name = package_name
        self.base_directory = base_directory
        self.copyright = "World"
        self.license = "LGPL"

    @property
    def project_directory(self):
        return os.path.join(self.base_directory, clearName(self.project_name))

    @property
    def copyright(self):
        return self.__copyright

    @copyright.setter
    def copyright(self, value):
        self.__copyright = value

    @property
    def license(self):
        return self.__license

    @license.setter
    def license(self, value):
        self.__license = value

    def create(self):
        try:
            return self._create()
        except:
            # rollback in case of error
            if os.path.isdir(self.project_directory):
                shutil.rmtree(self.project_directory)
            raise

    def _create(self):
        project_directory = self.project_directory
        os.makedirs(project_directory)
        package_name = self.package_name
        sub_dirs = "doc", "scripts",
        for sub_dir in sub_dirs:
            d = os.path.join(project_directory, sub_dir)
            os.makedirs(d)

        package_tree = (("gui", ("widgets",))), ("resources",)

        init_text = __init_template.format(self)
        package_dir = os.path.join(project_directory, package_name)
        createPackageTree(package_dir, package_tree, init_text=init_text)


def main(name="Bla Ble Bli"):
    p = Project(name, base_directory="/tmp")
    p.create()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(name=sys.argv[1])
    else:
        main()
