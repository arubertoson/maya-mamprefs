"""
"""
import logging

from maya import cmds, mel

from mamprefs import config
from mamprefs.base import BaseSettingManager, deleteUI


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def toggle_inital_shader_group(state=None):
    """
    Toggles initial shader item between custom and default.
    """
    if state is not None:
        _state = state
    else:
        _state = not(config['STATE_INIT_SHADER_OVERRIDE'])

    config['STATE_INIT_SHADER_OVERRIDE'] = _state
    override_inital_shading_group()
    return _state


def override_inital_shading_group():
    """
    Create a custom material for the initial shading group.
    """
    # states
    state = config['STATE_INIT_SHADER_OVERRIDE']
    mat_name = config['CURRENT_INIT_SHADER_OVERRIDE_MATNAME']

    if state and not cmds.objExists(mat_name):
        blinn = cmds.shadingNode('blinn', asShader=True, n=mat_name)
        cmds.setAttr(blinn + '.color', 0.8, 0.8, 0.8)
        cmds.setAttr(blinn + '.specularColor', 1, 1, 1)
        cmds.setAttr(blinn + '.eccentricity', 0.2)
        cmds.setAttr(blinn + '.specularRollOff', 0.2)
        cmds.connectAttr(
            blinn + '.outColor',
            'initialShadingGroup.surfaceShader',
            force=True
        )
        cmds.select(cl=True)
    elif not state:
        if cmds.objExists(mat_name):
            cmds.connectAttr(
                'lambert1.outColor',
                'initialShadingGroup.surfaceShader',
                force=True,
            )
            cmds.delete(mat_name)


class ColorManager(BaseSettingManager):
    """
    """
    instance = None

    def __init__(self):
        self.active = config['CURRENT_MAYA_COLOR_OVERRIDE_NAME']
        super(ColorManager, self).__init__('.color')

    def initUI(self):
        """
        Creates the user interface, can be used to update it aswell.
        """
        super(ColorManager, self).initUI()

        # UI element names
        main_menu = config['MENU_MAIN_NAME']
        marking_menu = config['MENU_MARKING_NAME']
        override_color_menu = config['MENU_MAYA_COLOR_OVERRIDE_NAME']

        # Delete UI element if they exists.
        deleteUI(override_color_menu)

        # Create the UI
        cmds.menuItem(
            override_color_menu,
            label='Maya Colors',
            insertAfter=marking_menu,
            subMenu=True,
            tearOff=True,
            parent=main_menu,
        )
        cmds.menuItem(
            label='Update',
            command=lambda *args: self.reload_settings(),
        )
        self._add_menu_items()
        cmds.menuItem(
            label='Maya Defaults',
            c=lambda *args: self.reset_settings(),
        )

    # PUBLIC

    def reload_settings(self):
        """
        """
        self.reload()
        if self.active is not None:
            self.make_file_active(self.active)

        self.initUI()

    def make_file_active(self, file_, *args):
        super(ColorManager, self).make_file_active(file_)
        config['CURRENT_MAYA_COLOR_OVERRIDE_NAME'] = self.active = file_

    def reset_settings(self):
        """
        Reset color settings.
        """
        self.reset_custom()
        mel.eval('displayColor -rf; colorIndex -rf; displayRGBColor -rf;')
        config['CURRENT_MAYA_COLOR_OVERRIDE_NAME'] = None

    def reset_custom(self):
        reset_list = [
            # Grid
            'optionVar -fv displayGridAxes $gGridDisplayAxesDefault',
            'optionVar -iv displayDivisionLines $gGridDisplayDivisionLinesDefault;',
            'optionVar -iv displayGridAxesAccented $gGridDisplayAxesAccentedDefault;',
            'GridOptions; performGridOptions 0; hideOptionBox;',
            # Gradient
            'displayPref -displayGradient 1'
        ]
        for i in reset_list:
            mel.eval(i)


class SettingManager(BaseSettingManager):
    """

    """
    instance = None

    def __init__(self):
        self.shading_group_job = None
        self.active = config['CURRENT_MAYA_SETTINGS_OVERRIDE_NAME']
        super(SettingManager, self).__init__('.prefs')

    def initUI(self):
        """
        Creates the user interface, can be used to update it aswell.
        """
        super(SettingManager, self).initUI()

        # UI element names
        main_menu = config['MENU_MAIN_NAME']
        setting_menu = config['MENU_MAYA_SETTINGS_OVERRIDE_NAME']
        color_menu = config['MENU_MAYA_COLOR_OVERRIDE_NAME']
        override_mat_menu = config['MENU_INIT_SHADER_OVERRIDE_NAME']
        reset_all = config['MENU_RESET_ALL_NAME']
        div1 = setting_menu + '_DIV1'
        div2 = setting_menu + '_DIV2'

        # Delete UI element if they exists.
        deleteUI(setting_menu, override_mat_menu, div1, div2, reset_all)

        # Create the UI
        cmds.menuItem(
            setting_menu,
            label='Maya Settings',
            insertAfter=color_menu,
            parent=main_menu,
            subMenu=True,
            tearOff=True,
        )
        cmds.menuItem(
            label='Update',
            command=lambda *args: self.reload_settings(),
        )
        self._add_menu_items()
        cmds.menuItem(
            label='Maya Defaults',
            c=lambda *args: self.reset_settings(),
        )
        cmds.menuItem(
            div1,
            divider=True,
            insertAfter=setting_menu,
            parent=main_menu
        )
        cmds.menuItem(
            override_mat_menu,
            label='Override Inital Shading',
            insertAfter=div1,
            parent=main_menu,
            checkBox=config['STATE_INIT_SHADER_OVERRIDE'],
            c=lambda *args: toggle_inital_shader_group(),
        )
        cmds.menuItem(div2, divider=True, parent=main_menu)
        cmds.menuItem(
            reset_all,
            label='Reset to factory settings',
            parent=main_menu,
            c=lambda *args: self.reset_all(),
        )

    # PUBLIC

    def make_file_active(self, file_, *args):
        super(SettingManager, self).make_file_active(file_)
        config['CURRENT_MAYA_SETTINGS_OVERRIDE_NAME'] = self.active = file_

    def reload_settings(self):
        """
        """
        self.reload()
        self.initUI()

        if self.active is not None:
            self.make_file_active(self.active)

        if config['STATE_INIT_SHADER_OVERRIDE']:
            toggle_inital_shader_group(True)

    def reset_settings(self):
        """
        Reset preferences found in Window -> Settings -> Preferences.
        """
        self.reset_custom()
        mel.eval('PreferencesWindow; revertToFactoryPrefs; setFocus '
                 'prefsSaveBtn; savePrefsChanges;')
        config['CURRENT_MAYA_SETTINGS_OVERRIDE_NAME'] = self.active = None
        self.reset_override_initial_saving_group()

    def reset_custom(self):
        """
        Reset grid with mel commands.

        .. todo: I don't really want to convert these to python. But it's
                 a bit annoying to have to show and hide window.
        """
        reset_list = [
            # Grid
            'optionVar -fv gridSpacing $gGridSpacingDefault;',
            'optionVar -fv gridDivisions $gGridDivisionsDefault;',
            'optionVar -fv gridSize $gGridSizeDefault',
            'GridOptions; performGridOptions 0; hideOptionBox;',
            # HUD
            'setPolyCountVisibility(0);',
            # Display
            'PolyDisplayReset;',
        ]
        for i in reset_list:
            mel.eval(i)

    def reset_override_initial_saving_group(self):
        """
        Turn off override_initail_shading_group if it's on
        """
        toggle_inital_shader_group(False)
        self.initUI()


def init():
    for each in [ColorManager, SettingManager]:
        if each.instance is None:
            each.instance = each()

        each.instance.reload_settings()

if __name__ == '__main__':
    init()
