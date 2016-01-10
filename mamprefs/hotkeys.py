"""
.. todo:: indicator that a double name exists in file.
"""
import re
import logging
from functools import partial

from maya import cmds

from mamprefs import base
from mamprefs.constants import *

logger = logging.getLogger(__name__)


class HotkeyManager(base.BaseManager):
    """
    Main hotkey switcher class.

    Manages existing hotkey bindings and able to switch between them.
    """
    instance = None

    def __init__(self):
        current_set = cmds.optionVar(q=HOTKEY_CURRENT_SET)
        self.active = current_set if current_set else ''
        super(HotkeyManager, self).__init__('.hotkey')

    def _add_menu_items(self):
        for item in self.map:
            cmds.menuItem(l=item.title(), c=partial(self.read_and_set_hotkeys,
                                                    item))
            cmds.menuItem(ob=True, c=partial(self.edit, item))

    def initUI(self):
        """
        Creates the user interface, can be used to update it aswell.
        """
        super(HotkeyManager, self).initUI()

        # Delete UI element if they exists.
        base.deleteUI(HOTKEY_MENU_NAME)

        # Create the UI
        cmds.menuItem(
            HOTKEY_MENU_NAME,
            label='Hotkey Set',
            subMenu=True,
            allowOptionBoxes=True,
            insertAfter='',
            parent=MAIN_MENU,
            tearOff=True
            )
        cmds.menuItem(l='Update', c=lambda *args: self.reload_hotkeys())
        cmds.menuItem(divider=True)
        self._add_menu_items()
        cmds.menuItem(divider=True)
        cmds.menuItem(l='Maya Default', c=lambda *args:
                      self.reset_hotkeys_to_factory())
        cmds.menuItem(l='Print Current', c=lambda *args: self.output())

    def parse_files(self):
        for file_name, f in self.files.iteritems():
            file_map = base.file_to_pyobject(f)
            self.map[file_name] = [Hotkey(file_name, **i) for i in file_map]

    def clean(self):
        """
        Removes existing hotkey runTimeCommand and empties hotkey map
        dictionary.
        """
        for m, hotkeys in self.map.iteritems():
            for i in hotkeys:
                try:
                    cmds.runTimeCommand(i.name, e=True, delete=True)
                except RuntimeError:
                    pass

    def reload_hotkeys(self, *args):
        self.reload()
        if self.active:
            cmds.hotkey(factorySettings=True)
            self.read_and_set_hotkeys(self.active)
        self.initUI()

    def reset_hotkeys_to_factory(self):
        """
        Set hotkeys back to Maya factory.
        """
        self.active = ''; cmds.hotkey(factorySettings=True)

    def read_and_set_hotkeys(self, keyset, *args):
        """
        Set hotkeys to given key set under given category.
        """
        self.active = keyset
        cmds.optionVar(sv=(HOTKEY_CURRENT_SET, keyset))
        for key in self.map[keyset]:
            cmds.hotkey(**key.keyargs)

    def output(self):
        """
        Outputs current hotkey bindings to script editor in readable format.
        """
        if not self.active:
            logging.info('Maya Default')
            return
        for key in self.map[self.active]:
            name = '{0: >26}'.format(
                re.sub(ur'{}_'.format(self.active), '', key.name)
                )
            key_stroke = '{0: >14}'.format(key.keys[0])
            logging.info(
                '{0} :: {1} :: {2}'.format(name, key_stroke, key.command)
                )


class Hotkey(object):
    """
    A class holding the necessary information for creating a hotkey in
    maya.

    """
    def __init__(self, category, name, keys, command, release=None,
                 script_type=None):
        self.category = category
        self.name = '{}_{}'.format(category, name)
        self.keys = list(keys)
        self.keyargs = self.parse_hotkey(keys)
        self.script_type = script_type or USE_PYTHON

        # Commands
        self.command = self.parse_command(command)
        self._create_command(self.command)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    def _create_command(self, command, mode=None):
        """
        Creates the runtime command and bind a name command to it.
        """
        if not cmds.runTimeCommand(self.name, q=True, exists=True):
            cmds.runTimeCommand(
                self.name,
                annotation=self.name,
                command=command,
                category=MAIN_MENU_NAME,
                commandLanguage=self.script_type,
            )

        cmds.nameCommand(
            self.name,
            ann=self.name,
            c=self.name,
            sourceType=self.script_type,
        )

    def parse_command(self, command):
        """
        Parse command string for maya hotkey.
        """
        if 'import' in command:
            return command
        module = command.split('.')[0]
        return 'import {0}; {1}'.format(module, command)

    def parse_hotkey(self, key):
        """
        Parse keyboard input string for maya hotkey.
        """
        kwargs = {}
        key_list = re.sub(ur'(\+(?!$))', ' ', key[0]).split()

        # Add modifiers to kwargs
        for i in ['alt', 'ctrl', 'super']:
            if i not in key_list:
                continue
            kwargs[{
                'alt': 'alt',
                'ctrl': 'ctl',
                'super': 'cmd',
            }[i]] = True
        kwargs['k'] = key_list.pop()

        # Add named commands to kwargs
        if ('release' not in key and 'press' not in key) or 'press' in key:
            kwargs['name'] = self.name

        if 'release' in key:
            kwargs['releaseName'] = self.name

        return kwargs


def init():
    if HotkeyManager.instance is None:
        HotkeyManager.instance = HotkeyManager()

    HotkeyManager.instance.initUI()


if __name__ == '__main__':
    init()
