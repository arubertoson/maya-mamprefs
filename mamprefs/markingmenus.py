"""
"""
from functools import partial
from maya import cmds

from mamprefs import base
from mamprefs.constants import *


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


class MarkingMenuManager(base.BaseManager):
    """
    """
    instance = None

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
                cmds.menuItem(l=menu.name.title(), c=partial(self.output, menu))
                cmds.menuItem(ob=True, c=partial(self.edit, file_name))
        cmds.menuItem(divider=True)

    def initUI(self):
        """
        Creates the user interface, can be used to update it aswell.
        """
        super(MarkingMenuManager, self).initUI()

        # Delete UI elements if they exists.
        base.deleteUI(MARKING_MENU_NAME)

        # Create the UI
        cmds.menuItem(
            MARKING_MENU_NAME,
            label='Marking Menu',
            subMenu=True,
            allowOptionBoxes=True,
            insertAfter=HOTKEY_MENU_NAME,
            parent=MAIN_MENU,
            tearOff=True,
            )
        cmds.menuItem(l='Update', c=lambda *args: self.reload_marking_menus())
        if self.map:
            self.add_menu_items()
        else:
            cmds.menuItem(l='No Marking Menus', enable=False)
        cmds.menuItem(divider=True)
        cmds.menuItem(l='Clean Scene', c=lambda *args: self.clean_menu())

    def parse_files(self):
        for file_name, f in self.files.iteritems():
            file_map = base.file_to_pyobject(f)
            self.map[file_name] = [
                MarkingMenu(name, item)
                for menu in file_map
                for name, item in menu.iteritems()
            ]

    def reload_marking_menus(self):
        """
        Rebuild menus and re-parse files. Then rebuild the UI.
        """
        self.reload(); self.initUI()

    def clean_menu(self):
        """
        .. note:: Might be redundant.
        """
        base.deleteUI(MARKING_MENU_POPUP_NAME)

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
        cmds.popupMenu(MARKING_MENU_POPUP_NAME, b=1, mm=True,
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
        base.deleteUI(MARKING_MENU_POPUP_NAME); self.build_menu()


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


def init():
    if MarkingMenuManager.instance is None:
        MarkingMenuManager.instance = MarkingMenuManager()

    MarkingMenuManager.instance.initUI()

if __name__ == '__main__':
    init()
