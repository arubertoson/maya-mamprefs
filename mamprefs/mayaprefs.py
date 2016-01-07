import os
import re
import ast
import logging

import collections
from functools import partial

from maya import cmds, mel

__title__ = 'mayaprefs'
__version__ = '0.1.3'
__author__ = 'Marcus Albertsson'
__email__ = 'marcus.arubertoson@gmail.com'
__url__ = 'http://github.com/arubertoson/maya-mayaprefs'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 Marcus Albertsson'


logger = logging.getLogger(__name__)


MAIN_MENU = 'MAM_MAIN_MENU'
MAIN_MENU_NAME = 'MAM Tools'
HOTKEY_MENU_NAME = 'MAM_HOTKEY_MENU_NAME'
MARKING_MENU_NAME = 'MAM_MARKING_MENU_NAME'
SETTINGS_MENU_NAME = 'MAM_SETTINGS_MENU_NAME'

HOTKEY_OPTVAR = 'MAM_HOTKEY_CURRENT_SET'
MARKINGMENU_TEMP_NAME = 'MAM_MARKING_MENU_TEMP_POPUP'
USE_MEL, USE_PYTHON = 'mel', 'python'
INIT_SHADER_OVERRIDE_STATUS = 'INIT_SHADER_OVERRIDE_STATUS'


# Paths
CWD = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATHS = [CWD]


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


class BaseManager(collections.Mapping):
    """
    Base class for setting manager.
    """
    def __init__(self, ext='', childclass=None):
        self._childclass = childclass
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
        """
        for file_name, f in self.files.iteritems():
            file_map = file_to_pyobject(f)
            if self._childclass is Hotkey:
                self.map[file_name] = [self._childclass(file_name, **i)
                                       for i in file_map]
            elif self._childclass is MarkingMenu:
                self.map[file_name] = [
                    self._childclass(name, item)
                    for menu in file_map
                    for name, item in menu.iteritems()
                ]
            else:
                self.map[file_name] = file_map

    def edit(self, key, *args):
        """
        Open file in default text editor.
        """
        os.system('{0}'.format(self.files[key]))

    def reload(self):
        """
        Looks for new files and rereads existing ones.
        """
        self.clean()
        self.files = get_files(self.ext)
        self.map = {}
        self.parse_files()
        self.initUI()

    def clean(self):
        """
        Exists in case subclass needs to clean up somehow.
        """


class SettingManager(BaseManager):

    instance = None

    def __init__(self):
        super(SettingManager, self).__init__('.maya-prefs')

    def initUI(self):
        super(SettingManager, self).initUI()
        try:
            cmds.deleteUI(SETTINGS_MENU_NAME)
            cmds.deleteUI(SETTINGS_MENU_NAME+'_RESET')
            cmds.deleteUI(INIT_SHADER_OVERRIDE_STATUS+'_MENU'),
        except RuntimeError:
            pass

        cmds.menuItem(
            SETTINGS_MENU_NAME,
            label='Reload Maya Settings',
            insertAfter=MARKING_MENU_NAME,
            parent=MAIN_MENU,
            command=lambda *args: self.reload(),
        )
        cmds.menuItem(
            SETTINGS_MENU_NAME+'_RESET',
            label='Reset to Factory',
            insertAfter=SETTINGS_MENU_NAME,
            parent=MAIN_MENU,
            command=lambda *args: self.reset_all(),
        )
        cmds.menuItem(
            INIT_SHADER_OVERRIDE_STATUS+'_MENU',
            label='Override Inital Shading',
            checkBox=cmds.optionVar(q=INIT_SHADER_OVERRIDE_STATUS),
            insertAfter=SETTINGS_MENU_NAME+'_RESET',
            parent=MAIN_MENU,
            c=lambda *args: toggle_inital_shader_status(),
        )

    def reload(self):
        super(SettingManager, self).reload()
        self.read_settings()

    def read_settings(self):
        """
        Apply setting files to Maya session.
        """
        for file_name, cmds_list in self.map.iteritems():
            for cmd_map in cmds_list:
                for command, args in cmd_map.iteritems():
                    self._parse_args(command, args)

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

    def reset_color_settings(self):
        """
        Reset color settings.
        """
        mel.eval('displayColor -rf; colorIndex -rf; displayRGBColor -rf;')

    def reset_settings(self):
        """
        Reset preferences found in Window -> Settings -> Preferences.
        """
        mel.eval('PreferencesWindow;')
        mel.eval('revertToFactoryPrefs')
        mel.eval('setFocus prefsSaveBtn; savePrefsChanges;')

    def reset_custom(self):
        """
        Reset custom settings outside of preferece windwos.
        """
        reset_list = [
            'optionVar -fv gridSpacing $gGridSpacingDefault;',
            'optionVar -fv gridDivisions $gGridDivisionsDefault;',
            'optionVar -fv gridSize $gGridSizeDefault',
            'optionVar -intValue displayDivisionLines $gGridDisplayDivisionLinesDefault;',
            'optionVar -intValue displayGridAxesAccented $gGridDisplayAxesAccentedDefault;',
            'GridOptions; performGridOptions 0; hideOptionBox;',
        ]
        for i in reset_list:
            print i
            mel.eval(i)
        cmds.optionVar(iv=[INIT_SHADER_OVERRIDE_STATUS, 0])
        override_inital_shading_group()

    def reset_all(self):
        """
        Reset to factory Settings.
        """
        self.reset_color_settings()
        self.reset_settings()
        self.reset_custom()


class HotkeyManager(BaseManager):
    """
    Main hotkey switcher class.

    Manages existing hotkey bindings and able to switch between them.
    """
    instance = None

    def __init__(self):
        optvar = cmds.optionVar(q=HOTKEY_OPTVAR)
        self.active = optvar if optvar else ''
        super(HotkeyManager, self).__init__('.maya-hotkey', Hotkey)

    def _add_menu_items(self):
        for item in self.map:
            cmds.menuItem(l=item.title(), c=partial(self.read_and_set_hotkeys,
                                                    item))
            cmds.menuItem(ob=True, c=partial(self.edit, item))

    def initUI(self):
        super(HotkeyManager, self).initUI()
        try:
            cmds.deleteUI(HOTKEY_MENU_NAME, menuItem=True)
        except RuntimeError:
            pass

        cmds.menuItem(
            HOTKEY_MENU_NAME,
            label='Hotkey Set',
            subMenu=True,
            allowOptionBoxes=True,
            insertAfter='',
            parent=MAIN_MENU,
            )
        cmds.menuItem(l='Maya Default', c=lambda *args:
                      self.reset_hotkeys_to_factory())
        cmds.menuItem(divider=True)
        self._add_menu_items()
        cmds.menuItem(divider=True)
        cmds.menuItem(l='Update', c=lambda *args: self.reload())
        cmds.menuItem(l='Print Current', c=lambda *args: self.output())


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

    def reload(self, *args):
        super(HotkeyManager, self).reload()
        if self.active:
            cmds.hotkey(factorySettings=True)
            self.read_and_set_hotkeys(self.active)

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
        cmds.optionVar(sv=(HOTKEY_OPTVAR, keyset))
        for key in self.map[keyset]:
            cmds.hotkey(**key.keyargs)

    def output(self):
        """
        Outputs current hotkey bindings to script editor in readable format.
        """
        if not self.active:
            print('Maya Default')
            return
        for key in self.map[self.active]:
            name = '{0: >32}'.format(re.sub(ur'{}_'.format(self.active), '', key.name))
            key_stroke = '{0: >18}'.format(key.keys[0])
            print('{0} :: {1} :: {2}'.format(name, key_stroke, key.command))


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
        """Parse keyboard input string for maya hotkey."""
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


class MarkingMenuManager(BaseManager):

    instance = None

    def __init__(self):
        super(MarkingMenuManager, self).__init__('.maya-markingmenu',
                                                 MarkingMenu)

    def __getitem__(self, key):
        for menu_list in self.map.itervalues():
            for menu in menu_list:
                if menu.name == key:
                    return menu

    def add_menu_items(self):
        cmds.menuItem(divider=True)
        cmds.menuItem(l='Marking Menus:', enable=False)
        for file_name, menu_list in self.map.iteritems():
            for menu in menu_list:
                cmds.menuItem(l=menu.name.title(),
                              c=partial(self.output, menu))
                cmds.menuItem(ob=True, c=partial(self.edit, file_name))
        cmds.menuItem(divider=True)

    def initUI(self):
        super(MarkingMenuManager, self).initUI()
        try:
            cmds.deleteUI(MARKING_MENU_NAME, menuItem=True)
        except RuntimeError:
            pass

        cmds.menuItem(
            MARKING_MENU_NAME,
            label='Marking Menu',
            subMenu=True,
            allowOptionBoxes=True,
            insertAfter=HOTKEY_MENU_NAME,
            parent=MAIN_MENU,
            )
        cmds.menuItem(l='Update', c=lambda *args: self.reload())
        if self.map:
            self.add_menu_items()
        else:
            cmds.menuItem(l='No Marking Menus', enable=False)
        cmds.menuItem(divider=True)
        cmds.menuItem(l='Clean Scene', c=lambda *args: self.clean_menu())

    def clean_menu(self):
        """
        .. note:: Might be redundant.
        """
        try:
            cmds.deleteUI(MARKING_MENU_NAME)
        except RuntimeError:
            pass

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
    def __init__(self, name, items):
        self.name = name
        self.items = [MarkingMenuItem(**i) for i in items]

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    __repr__ = __str__

    def build_menu(self):
        """
        Creates menu items.
        """
        cmds.popupMenu(MARKINGMENU_TEMP_NAME, b=1, mm=True,
                       parent=get_parent_panel())
        for item in self.items:
            if 'set_parent' in item:
                cmds.setParent('..', m=True)
            else:
                cmds.menuItem(**item.unpack())

    def show(self):
        """
        Shows marking menu on hotkey press.
        """
        try:
            cmds.deleteUI(MARKINGMENU_TEMP_NAME)
        except RuntimeError:
            pass
        self.build_menu()


class MarkingMenuItem(object):

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
        else:
            self.menu_kwargs = self.default_menu.copy()
            if 'position' in kwargs:
                kwargs['radialPosition'] = kwargs.pop('position', None)

            if 'sub_menu' in kwargs:
                self.menu_kwargs['subMenu'] = kwargs.pop('sub_menu', None)

            # kwargs['command'] = kwargs['command']+'; maya_prefs.hide_menu()'
            self.menu_kwargs.update(kwargs)

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.menu_kwargs['label'])

    def __getitem__(self, key):
        return self.menu_kwargs[key]

    def __contains__(self, key):
        return key in self.menu_kwargs

    __repr__ = __str__

    def unpack(self):
        return self.menu_kwargs


def show_menu(menu):
    if MarkingMenuManager.instance is None:
        MarkingMenuManager.instance = MarkingMenuManager()

    try:
        MarkingMenuManager.instance[menu].show()
    except KeyError:
        logger.error('{} is not in manager.'.format(menu))


def hide_menu():
    """
    Hide and delete menu.
    """
    try:
        cmds.deleteUI(MARKINGMENU_TEMP_NAME)
    except RuntimeError:
        pass


def init_marking_menu():
    if MarkingMenuManager.instance is None:
        MarkingMenuManager.instance = MarkingMenuManager()


def init_settings():
    if SettingManager.instance is None:
        SettingManager.instance = SettingManager()


def init_hotkeys():
    if HotkeyManager.instance is None:
        HotkeyManager.instance = HotkeyManager()


def toggle_inital_shader_status():

    status = not(cmds.optionVar(q=INIT_SHADER_OVERRIDE_STATUS))
    cmds.optionVar(iv=[INIT_SHADER_OVERRIDE_STATUS, status])
    override_inital_shading_group()
    return status


def override_inital_shading_group():
    if (cmds.optionVar(q=INIT_SHADER_OVERRIDE_STATUS) and not
            cmds.objExists('sh_blinn')):
        blinn = cmds.shadingNode('blinn', asShader=True, n='sh_blinn')
        cmds.setAttr(blinn+'.color', 0.8, 0.8, 0.8)
        cmds.setAttr(blinn+'.specularColor', 1, 1, 1)
        cmds.setAttr(blinn+'.eccentricity', 0.2)
        cmds.setAttr(blinn+'.specularRollOff', 0.2)
        cmds.connectAttr(blinn+'.outColor',
                         'initialShadingGroup.surfaceShader', force=True)
        cmds.select(cl=True)
    else:
        if cmds.objExists('sh_blinn'):
            cmds.connectAttr('lambert1.outColor',
                             'initialShadingGroup.surfaceShader', force=True)
            cmds.delete('sh_blinn')


def load():
    print 'loading settings from maya...'
    init_hotkeys()
    init_settings()
    init_marking_menu()

    # cmds.optionVar(iv=[INIT_SHADER_OVERRIDE_STATUS, 1])
    # override_inital_shading_group()
    # cmds.savePrefs()


if __name__ == '__main__':
    load()
