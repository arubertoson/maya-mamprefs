"""
"""
import logging

from maya import cmds, mel


from mamprefs import base
from mamprefs.constants import *

logger = logging.getLogger(__name__)


def toggle_inital_shader_group(state=None):
    """
    Toggles initial shader item between custom and default.
    """
    if state is not None:
        status = state
    else:
        status = not(cmds.optionVar(q=INIT_SHADER_OVERRIDE_STATUS))
    cmds.optionVar(iv=[INIT_SHADER_OVERRIDE_STATUS, status])
    override_inital_shading_group()
    return status


def script_job_exists(jobnum, event):
    if not cmds.scriptJob(exists=jobnum):
        return False
    for i in cmds.scriptJob(lj=True):
        if i.startswith(str(jobnum)) and str(event) in i:
            return True
    return False


def override_inital_shading_group():
    """
    Create a custom material for the initial shading group.
    """
    def create_script_job():
        jobnum = cmds.optionVar(q=INIT_SHADER_OVERRIDE_JOBNUM)
        event = (
            'NewSceneOpened',
            '{}; {}'.format(
                'import mamprefs',
                'mamprefs.settings.toggle_inital_shader_group(True)'),
            )
        if not script_job_exists(jobnum, event):
            jobnum = cmds.scriptJob(protected=True, event=event)
            cmds.optionVar(iv=(INIT_SHADER_OVERRIDE_JOBNUM, jobnum))
            print('Creating {}'.format(jobnum))

    def kill_script_job():
        jobnum = cmds.optionVar(q=INIT_SHADER_OVERRIDE_JOBNUM)
        if jobnum:
            cmds.scriptJob(kill=jobnum, f=True)
            cmds.optionVar(iv=(INIT_SHADER_OVERRIDE_JOBNUM, -1))
            print('Killing {}'.format(jobnum))

    if (cmds.optionVar(q=INIT_SHADER_OVERRIDE_STATUS) and not
            cmds.objExists(INIT_SHADER_OVERRIDE_MATNAME)):
        blinn = cmds.shadingNode('blinn', asShader=True,
                                 n=INIT_SHADER_OVERRIDE_MATNAME)
        cmds.setAttr(blinn+'.color', 0.8, 0.8, 0.8)
        cmds.setAttr(blinn+'.specularColor', 1, 1, 1)
        cmds.setAttr(blinn+'.eccentricity', 0.2)
        cmds.setAttr(blinn+'.specularRollOff', 0.2)
        cmds.connectAttr(blinn+'.outColor',
                         'initialShadingGroup.surfaceShader', force=True)
        cmds.select(cl=True)
        create_script_job()
    else:
        if cmds.objExists(INIT_SHADER_OVERRIDE_MATNAME):
            cmds.connectAttr('lambert1.outColor',
                             'initialShadingGroup.surfaceShader',
                             force=True,
                             )
            cmds.delete(INIT_SHADER_OVERRIDE_MATNAME)
            kill_script_job()


class SettingManager(base.BaseManager):
    """

    """
    instance = None

    def __init__(self):
        self.shading_group_job = None
        super(SettingManager, self).__init__('.prefs')

    def initUI(self):
        """
        Creates the user interface, can be used to update it aswell.
        """
        super(SettingManager, self).initUI()

        # UI element names
        reload_menu = SETTINGS_MENU_NAME
        reset_menu = SETTINGS_MENU_NAME+'_RESET'
        override_menu = INIT_SHADER_OVERRIDE_STATUS+'_MENU'
        div1 = SETTINGS_MENU_NAME+'_DIV1'
        div2 = SETTINGS_MENU_NAME+'_DIV2'

        # Delete UI element if they exists.
        base.deleteUI(reload_menu, reset_menu, override_menu, div1, div2)

        # Create the UI
        cmds.menuItem(div1, divider=True, parent=MAIN_MENU)
        cmds.menuItem(
            override_menu,
            label='Override Inital Shading',
            insertAfter=div1,
            parent=MAIN_MENU,
            checkBox=cmds.optionVar(q=INIT_SHADER_OVERRIDE_STATUS),
            c=lambda *args: toggle_inital_shader_group(),
        )
        cmds.menuItem(div2, divider=True, parent=MAIN_MENU)
        cmds.menuItem(
            reload_menu,
            label='Reload Maya Settings',
            insertAfter=div2,
            parent=MAIN_MENU,
            command=lambda *args: self.reload_settings(),
        )
        cmds.menuItem(
            reset_menu,
            label='Reset to Factory',
            insertAfter=reload_menu,
            parent=MAIN_MENU,
            command=lambda *args: self.reset_all(),
        )

    def parse_files(self):
        """
        Parse files in object files attribute.
        """
        for file_name, f in self.files.iteritems():
            self.map[file_name] = base.file_to_pyobject(f)

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

    # PUBLIC

    def reload_settings(self):
        self.reload()
        self.read_settings()
        toggle_inital_shader_group(True)
        self.initUI()

        # Save prefs.
        cmds.optionVar(iv=[CUSTOM_SETTING_STATE, True])
        cmds.savePrefs()

    def read_settings(self):
        """
        Apply setting files to Maya session.
        """
        for file_name, cmds_list in self.map.iteritems():
            for cmd_map in cmds_list:
                for command, args in cmd_map.iteritems():
                    self._parse_args(command, args)

    def reset_color_settings(self):
        """
        Reset color settings.
        """
        mel.eval('displayColor -rf; colorIndex -rf; displayRGBColor -rf;')

    def reset_settings(self):
        """
        Reset preferences found in Window -> Settings -> Preferences.
        """
        mel.eval('PreferencesWindow; revertToFactoryPrefs; setFocus '
                 'prefsSaveBtn; savePrefsChanges;')

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
            ('optionVar -iv displayDivisionLines '
             '$gGridDisplayDivisionLinesDefault;'),
            ('optionVar -iv displayGridAxesAccented '
             '$gGridDisplayAxesAccentedDefault;'),
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

    def reset_all(self):
        """
        Reset to factory Settings.
        """
        cmds.optionVar(iv=[CUSTOM_SETTING_STATE, False])
        self.reset_color_settings()
        self.reset_settings()
        self.reset_custom()
        self.reset_override_initial_saving_group()


def init():
    if SettingManager.instance is None:
        SettingManager.instance = SettingManager()

    if cmds.optionVar(q=CUSTOM_SETTING_STATE):
        SettingManager.instance.reload_settings()
    else:
        SettingManager.instance.initUI()


if __name__ == '__main__':
    init()
