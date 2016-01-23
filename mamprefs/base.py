"""
"""
import sys
import os
import ast
import logging
import traceback
import collections
from functools import partial

from maya import cmds, mel

from mamprefs import _config_paths, _config


logger = logging.getLogger(__name__)


def file_to_pyobject(file_):
    """
    Converts the contents of a file to a python object
    """
    with open(file_) as f:
        return ast.literal_eval(f.read())


def get_files(type_, paths=_config_paths):
    """
    Collect hotkey config files from given config paths.
    """
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
    Takes a list of names and tries to delete them.
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
        # Ui element names
        main_menu = _config['MENU_MAIN_NAME']
        menu_label = _config['MENU_MAIN_LABEL']

        if not cmds.menu(main_menu, exists=True):
            cmds.menu(
                main_menu,
                label=menu_label,
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

    def reset_settings(self):
        """
        """

    def itersubclasses(self, cls, _seen=None):
        if not isinstance(cls, type):
             raise TypeError('itersubclasses must be called with '
                             'new-style classes, not %.100r' % cls)
        if _seen is None: _seen = set()
        try:
            subs = cls.__subclasses__()
        except TypeError:  # fails only when cls is type
            subs = cls.__subclasses__(cls)
        for sub in subs:
            if sub not in _seen:
                _seen.add(sub)
                yield sub
                for sub in self.itersubclasses(sub, _seen):
                    yield sub

    def reset_all(self):
        """
        """
        for cls in self.itersubclasses(BaseManager):
            try:
                cls.instance.reset_settings()
            except AttributeError:
                traceback.print_exc(file=sys.stdout)


class BaseSettingManager(BaseManager):

    def _add_menu_items(self):
        cmds.menuItem(divider=True)
        for item in self.map:
            cmds.menuItem(
                l=item.title(),
                c=partial(self.make_file_active, item),
                )
            cmds.menuItem(ob=True, c=partial(self.edit, item))
        cmds.menuItem(divider=True)

    def parse_files(self):
        """
        Parse files in object files attribute.
        """
        for file_name, f in self.files.iteritems():
            self.map[file_name] = file_to_pyobject(f)

    def _parse_args(self, command, args):
        """
        Parse argument and unpack correctly in function.
        """
        for arg in args:
            try:
                if command == 'mel':
                    mel.eval(arg)
                    continue
                func = getattr(cmds, command)
                if isinstance(arg, list):
                    if isinstance(arg[-1], dict):
                        d = arg.pop()
                        func(*arg, **d)
                    else:
                        func(*arg)
                elif isinstance(arg, dict):
                    func(**arg)
            except (TypeError, RuntimeError):
                logger.warn('{}, flag: {}'.format(func.__name__, arg))

    def make_file_active(self, file_, *args):
        """
        Apply color file to Maya session.
        """
        for cmd_map in self.map[file_]:
            for command, args in cmd_map.iteritems():
                self._parse_args(command, args)

    def edit(self, key, *args):
        """
        Open file in default text editor.
        """
        os.system('{0}'.format(self.files[key]))
