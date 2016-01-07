import os
import ast
import collections

from maya import cmds, mel


from mamprefs.constants import *


def file_to_pyobject(file_):
    with open(file_) as f:
        return ast.literal_eval(f.read())


def get_files(type_, paths=CONFIG_PATHS):
    """Collect hotkey config files from given config paths."""
    hfiles = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        for f in os.listdir(p):
            if not f.endswith(type_):
                continue
            hfiles[os.path.splitext(f)[0]] = os.path.join(p, f)
    return hfiles


def deleteUI(*args):
    """
    """
    for i in args:
        try:
            cmds.deleteUI(i)
        except RuntimeError:
            pass


class BaseManager(collections.Mapping):
    """
    Base class for setting manager.
    """
    def __init__(self, ext=''):
        # self._childclass = childclass
        self.ext = ext
        self.files = {}
        self.map = {}
        self.reload()

    def __getitem__(self, key):
        return self.map[key]

    def __iter__(self):
        return iter(self.map)

    def __len__(self):
        return len(self.map)

    def initUI(self):
        """
        Checks if base menu exists, if not create it.
        """
        if not cmds.menu(MAIN_MENU, exists=True):
            cmds.menu(
                MAIN_MENU,
                label=MAIN_MENU_NAME,
                parent=mel.eval('$tmpvar = $gMainWindow'),
            )

    def parse_files(self):
        """
        Iterates through available files and set object map to valid python
        dict.

        Override
        """

    def edit(self, key, *args):
        """
        Open file in default text editor.
        """
        os.system('{0}'.format(self.files[key]))

    def clean(self):
        """
        Exists in case subclass needs to clean up somehow.
        """

    def reload(self):
        """
        Looks for new files and rereads existing ones.
        """
        self.clean()
        self.files = get_files(self.ext)
        self.map = {}
        self.parse_files()
