"""
"""
import sys
import re
import keyword
import logging
import traceback
from functools import partial

from PySide import QtCore
from PySide.QtCore import QObject

from maya import cmds

from mampy.pyside.utils import get_qt_object

from mamprefs import config
from mamprefs.base import BaseManager, deleteUI, file_to_pyobject


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


ACTIVE_MENU = None


def get_parent_panel():
    """
    Return current panels parent.
    """
    panel = cmds.getPanel(up=True)
    if cmds.panel(panel, q=True, ex=True):
        panel_layout = cmds.layout(panel, q=True, p=True)
        while not cmds.paneLayout(panel_layout, q=True, ex=True):
            panel_layout = cmds.control(panel_layout, q=True, p=True)
        if cmds.paneLayout(panel_layout, q=True, ex=True):
            return panel_layout
        else:
            return 'viewPanes'


class MarkingMenuManager(BaseManager):
    """
    """
    def __init__(self):
        super(MarkingMenuManager, self).__init__('.markingmenu')

    def __getitem__(self, key):
        for menu_list in self.map.itervalues():
            for menu in menu_list:
                if menu.name == key:
                    return menu
        else:
            raise KeyError('"{}" is not in menu map.'.format(key))

    def add_menu_items(self):
        """
        Create menu items for every existing marking menu.
        """
        cmds.menuItem(divider=True)
        for file_name, menu_list in self.map.iteritems():
            for menu in menu_list:
                cmds.menuItem(
                    l=menu.name.title(),
                    c=partial(self.output, menu),
                )
                cmds.menuItem(ob=True, c=partial(self.edit, file_name))
        cmds.menuItem(divider=True)

    def initUI(self):
        """
        Creates the user interface, can be used to update it aswell.
        """
        super(MarkingMenuManager, self).initUI()

        # UI element names
        main_menu = config['MENU_MAIN_NAME']
        marking_menu = config['MENU_MARKING_NAME']
        layout_menu = config['MENU_LAYOUT_NAME']

        # Delete UI elements if they exists.
        deleteUI(marking_menu)

        # Create the UI
        cmds.menuItem(
            marking_menu,
            label='Marking Menus',
            subMenu=True,
            allowOptionBoxes=True,
            insertAfter=layout_menu,
            parent=main_menu,
            tearOff=True,
        )
        cmds.menuItem(l='Update', c=lambda *args: self.reload_marking_menus())
        if self.map:
            self.add_menu_items()
        else:
            cmds.menuItem(l='No Marking Menus', enable=False)
        cmds.menuItem(l='Clean Scene', c=lambda *args: self.clean_menu())

    def parse_files(self):
        for file_name, f in self.files.iteritems():
            file_map = file_to_pyobject(f)
            self.map[file_name] = [
                MarkingMenu(**menu)
                for menu in file_map
                # for name, item in menu.iteritems()
            ]

    def reload_marking_menus(self):
        """
        Rebuild menus and re-parse files. Then rebuild the UI.
        """
        self.reload()
        self.initUI()

    def clean_menu(self):
        """
        .. note:: Might be redundant.
        """
        deleteUI(config['MENU_MARKING_POPUP_NAME'])

    def output(self, menu, *args):
        """
        Outputs to script editor.
        """
        if not any('radialPosition' in item for item in menu.items):
            for item in menu.items:
                print item
        else:
            for radial in ["N", "NW", "W", "SW", "S", "SE", "E", "NE"]:
                for item in menu.items:
                    try:
                        if radial == item['radialPosition']:
                            print '{}: {}'.format(radial, item)
                    except KeyError:
                        pass


class MarkingMenu(object):
    """

    """
    def __init__(self, name, button, marking_menu, modifiers, items,
                 option_boxes=False):
        self.name = name
        self.marking_menu = marking_menu
        self.button = button
        self.option_boxes = option_boxes
        self.items = list()
        self.modifiers = {'{}Modifier'.format(i): True for i in modifiers}

        self.pane_widget = None

        self.closing_event = MarkingMenuEventFilter()
        self.parse_items(items)
        logger.debug([name, button, marking_menu, modifiers, items])

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    __repr__ = __str__

    def parse_items(self, items):
        logger.debug('New menu.')
        for item in items:
            logger.debug(item)
            if 'sub_menu' in item:
                logging.debug('building sub menu')
                sub_list = item.pop('sub_menu', [])
                sub_list.append({'set_parent': True})
                logging.debug(sub_list)

                item['subMenu'] = True
                self.items.append(MarkingMenuItem(**item))
                self.parse_items(sub_list)
            else:
                self.items.append(MarkingMenuItem(**item))

    def build_menu(self):
        """
        Creates menu items.
        """
        try:
            cmds.popupMenu(
                config['MENU_MARKING_POPUP_NAME'],
                button=self.button,
                allowOptionBoxes=self.option_boxes,
                markingMenu=self.marking_menu,
                parent=get_parent_panel(),
                **self.modifiers
            )
            logger.debug('building menu items:')
            for item in self.items:
                logger.debug(item)
                if 'set_parent' in item:
                    cmds.setParent('..', m=True)
                else:
                    cmds.menuItem(**item.unpack())
        except:
            traceback.print_exc(file=sys.stdout)

    def show(self):
        """
        Shows marking menu on hotkey press.
        """
        try:
            self.pane_widget.removeEventFilter(self.closing_event)
        except AttributeError:
            pass
        deleteUI(config['MENU_MARKING_POPUP_NAME'])

        self.build_menu()

        self.pane_widget = get_qt_object(get_parent_panel())
        self.pane_widget.installEventFilter(self.closing_event)

    def hide(self):
        try:
            self.pane_widget.removeEventFilter(self.closing_event)
        except AttributeError:
            pass
        deleteUI(config['MENU_MARKING_POPUP_NAME'])


class MarkingMenuEventFilter(QObject):
    """
    Filter to handle events when building and hiding marking menus.
    """

    key_release = False
    is_child = False
    destroy = False

    def eventFilter(self, obj, event):
        """Make marking menus behave like other maya marking menus."""
        # Destroy the menu in a new event cycle. If we don't do this we will
        # delete the menu before the commands or sub menus are shown and crash
        # maya.
        if self.destroy:
            self.destroy = False
            hide_menu()

        etype = event.type()
        if etype == QtCore.QEvent.ChildRemoved:
            self.is_child = False
            if self.key_release:
                self.destroy = True

        if etype == QtCore.QEvent.ChildAdded:
            self.is_child = True

        else:
            if etype == QtCore.QEvent.ShortcutOverride:
                if event.isAutoRepeat():
                    self.key_release = False
                    return True
            elif etype == QtCore.QEvent.KeyRelease:
                if not self.is_child:
                    hide_menu()
                self.key_release = True
        return super(MarkingMenuEventFilter, self).eventFilter(obj, event)


class MarkingMenuItem(object):
    """

    """
    default_menu = {
        # Requiered
        # 'label': None,
        # 'command': None,
        # 'radialPosition': None,

        # Optional
        'divider': False,
        'subMenu': False,
        'tearOff': False,
        'altModifier': False,
        'ctrlModifier': False,
        'shiftModifier': False,
        'optionModifier': False,
        'commandModifier': False,
        'optionBox': False,
        'enable': True,
        'data': False,
        'allowOptionBoxes': True,
        'postMenuCommandOnce': False,
        'enableCommandRepeat': True,
        'echoCommand': False,
        'italicized': False,
        'boldFont': True,
        'sourceType': 'python',
    }

    def __init__(self, **kwargs):
        self.menu_kwargs = {}
        if 'divider' in kwargs:
            self.menu_kwargs = {'divider': True}
        elif 'set_parent' in kwargs:
            self.menu_kwargs['set_parent'] = '..'
            # self.menu_kwargs['label'] = 'set_parent'
        else:
            self.menu_kwargs = self.default_menu.copy()
            if 'position' in kwargs:
                kwargs['radialPosition'] = kwargs.pop('position', None)

            if 'command' in kwargs:
                kwargs['command'] = str(Command(kwargs['command']))

            self.menu_kwargs.update(kwargs)

    def __str__(self):
        if 'label' not in self.menu_kwargs:
            return '{}()'.format(self.__class__.__name__)
        return '{}({})'.format(self.__class__.__name__, self.menu_kwargs['label'])

    def __getitem__(self, key):
        return self.menu_kwargs[key]

    def __contains__(self, key):
        return key in self.menu_kwargs

    __repr__ = __str__

    def unpack(self):
        return self.menu_kwargs


class Command(object):

    regex = re.compile(ur'^\w+')

    def __init__(self, command_string):
        self.command_string = command_string
        self._module = None
        self._parsed_command = None

    def __str__(self):
        return '{}'.format(self.parsed_command)

    @property
    def module(self):
        if self._module is None:
            try:
                _module = re.findall(self.regex, self.command_string)[0]
            except IndexError:
                _module = None
        return _module

    @property
    def is_module_keyword(self):
        return keyword.iskeyword(self.module)

    @property
    def is_maya_keyword(self):
        return self.module in ['cmds', 'mel']

    @property
    def parsed_command(self):
        if self._parsed_command is None:
            self._parsed_command = self.parse()
        return self._parsed_command

    def parse(self):
        tmpcommand = ''
        if self.module is None:
            return 'null'

        if self.is_module_keyword or self.is_maya_keyword:
            tmpcommand = self.command_string
        else:
            tmpcommand = 'import {0.module}; {0.command_string}'.format(self)

        logger.debug('parsed command to: {}'.format(tmpcommand))
        return tmpcommand


MARKING_MENU_MANAGER = MarkingMenuManager()


def init():
    MARKING_MENU_MANAGER.initUI()


def show_menu(menu):
    global ACTIVE_MENU
    ACTIVE_MENU = menu

    logger.debug(MARKING_MENU_MANAGER[menu])
    try:
        MARKING_MENU_MANAGER[menu].show()
    except KeyError:
        logger.exception(traceback.format_exc())


def hide_menu():
    logger.debug(MARKING_MENU_MANAGER[ACTIVE_MENU])
    try:
        MARKING_MENU_MANAGER[ACTIVE_MENU].hide()
    except KeyError:
        logger.exception(traceback.format_exc())


if __name__ == '__main__':
    pass
