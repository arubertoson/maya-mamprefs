"""
"""
import os

# Paths
CURRENT_WORK_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
CONFIG_PATHS = [CURRENT_WORK_DIRECTORY]

_cwd_parent = os.path.abspath(os.path.join(CURRENT_WORK_DIRECTORY, os.pardir))
if os.path.isdir(os.path.join(_cwd_parent, 'prefs')):
    CONFIG_PATHS.append(os.path.join(_cwd_parent, 'prefs'))


# Menus
MAIN_MENU = 'MAM_MAIN_MENU'
MAIN_MENU_NAME = 'MAM Tools'
HOTKEY_MENU_NAME = 'MAM_HOTKEY_MENU_NAME'
MARKING_MENU_NAME = 'MAM_MARKING_MENU_NAME'
SETTINGS_MENU_NAME = 'MAM_SETTINGS_MENU_NAME'
LAYOUT_MENU_NAME = 'MAM_LAYOUT_MENU_NAME'

# Script dock
SCRIPT_OUTPUT_WINDOW = 'MAM_SCRIPT_OUTPUT_WINDOW'
SCRIPT_OUTPUT_DOCK = 'MAM_SCRIPT_OUTPUT_DOCK'

# Settings
CUSTOM_SETTING_STATE = 'MAM_CUSTOM_SETTING_STATE'
INIT_SHADER_OVERRIDE_STATUS = 'MAM_INIT_SHADER_OVERRIDE_STATUS'
INIT_SHADER_OVERRIDE_MATNAME = 'mam_blinn'
INIT_SHADER_OVERRIDE_JOBNUM = 'MAM_INIT_SHADER_OVERRIDE_JOBNUM'

# Hotkeys
HOTKEY_CURRENT_SET = 'MAM_HOTKEY_CURRENT_SET'

# Marking Menus
MARKING_MENU_POPUP_NAME = 'MAM_MARKING_MENU_POPUP_NAME'

# Layouts
ACTIVE_LAYOUT = 'MAM_ACTIVE_LAYOUT'
MAIN_WINDOW_DOCKS = [
    'Tool Settings',
    'NEXDockControl',
    'Attribute Editor',
    'Channel Box / Layer Editor'
    ]

# Docks for reset
RESET_WINDOW_DOCKS = [SCRIPT_OUTPUT_DOCK]

# Globals
USE_MEL, USE_PYTHON = 'mel', 'python'


