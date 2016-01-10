# -*- coding: UTF-8 -*-
"""
"""
import logging
import textwrap
from functools import partial

from maya import cmds, mel

from mamprefs import base
from mamprefs import _layout_docks
from mamprefs.constants import *

logger = logging.getLogger(__name__)


def reset_screen():
    """
    Hide all main window docks.
    """
    for name in RESET_WINDOW_DOCKS:
        try:
            cmds.dockControl(name, e=True, vis=False)
        except RuntimeError:
            pass


def docks(direction):
    """
    Dock Maya main window docks to the direction location.
    """
    for i in MAIN_WINDOW_DOCKS:
        name = mel.eval('getUIComponentDockControl("{}", false)'.format(i))
        if not name:
            name = 'NEXDockControl'

        if cmds.dockControl(name, q=True, a=True) == direction:
            continue

        if cmds.dockControl(name, q=True, fl=True):
            cmds.dockControl(name, e=True, fl=False)
        cmds.dockControl(name, e=True, a=direction)


class LayoutManager(base.BaseManager):
    """
    Layout manager class.

    Manages UI and layouts.
    """
    instance = None

    def __init__(self):
        super(LayoutManager, self).__init__('.layout')

    def _add_layout_item(self):
        if all(not l for k, v in self.map.iteritems() for l in v.itervalues()):
            cmds.menuItem(l='No Layaouts', enable=False)
        else:
            for f, d in self.map.iteritems():
                for layout in d.itervalues():
                    cmds.menuItem(
                        l=layout.visible_name,
                        c=partial(layout.load)
                        )
                    cmds.menuItem(ob=True, c=partial(self.edit, f))

    def initUI(self):
        """
        Creates the user interface, can be used to update it aswell.
        """
        super(LayoutManager, self).initUI()

        # UI element names
        layout_menu = LAYOUT_MENU_NAME
        layout_reload = LAYOUT_MENU_NAME+'_RELOAD'

        # Delete UI element if they exists.
        base.deleteUI(LAYOUT_MENU_NAME)

        # Create the UI
        cmds.menuItem(
            LAYOUT_MENU_NAME,
            label='Layouts',
            insertAfter=HOTKEY_MENU_NAME,
            parent=MAIN_MENU,
            subMenu=True,
            tearOff=True
            )
        cmds.menuItem(
            layout_reload,
            label='Update',
            c=lambda *args: self.reload_layouts(),
            )
        cmds.menuItem(divider=True)
        self._add_layout_item()

    def reload_layouts(self):
        self.reload()
        self.initUI()

    def parse_files(self):
        for file_name, f in self.files.iteritems():
            file_map = base.file_to_pyobject(f)

            self.map.setdefault(file_name, {})
            for d in file_map:
                for name, kw in d.iteritems():
                    self.map[file_name][name] = Layout(name, **kw)


class Layout(object):
    """
    Layout class

    Container for different layout arguments.
    """
    def __init__(self, name, **kwargs):
        self.name = name
        self.visible_name = name.replace('_', ' ').title()
        self.layout_string = textwrap.dedent(kwargs.get('layout'))

        # Args
        self.docks = kwargs.get('docks', None)
        if self.docks is not None:
            self.main_docks_direction = self.docks.pop("main_docks")
        self.other_docks = self.docks
        self.commands = kwargs.get('commands', '')

        # Format layout_string
        self.layout = str(self.layout_string).format(
            self.visible_name,
            ';'.join(self.commands)
            )

    def load(self, *args):
        """
        Load current layout.
        """
        reset_screen()

        if cmds.getPanel(cwl=self.visible_name) is None:
            mel.eval(self.layout)

        if self.docks is not None:
            docks(self.main_docks_direction)

        if self.other_docks:
            for func, arg in self.other_docks.iteritems():
                getattr(_layout_docks, func)(arg)

        mel.eval('setNamedPanelLayout( "{}" );'.format(self.visible_name))


def init():
    if LayoutManager.instance is None:
        LayoutManager.instance = LayoutManager()

    LayoutManager.instance.initUI()


if __name__ == '__main__':
    script_output('bottom')
