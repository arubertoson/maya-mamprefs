"""
"""
import os
import json
import logging

from maya import cmds

__title__ = 'mayaprefs'
__version__ = '0.1.4'
__author__ = 'Marcus Albertsson <marcus.arubertoson@gmail.com>'
__url__ = 'http://github.com/arubertoson/maya-mayaprefs'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Marcus Albertsson'


logger = logging.getLogger(__name__)

# Constants
cwd = ''
cfg_paths = []
config = {}


def set_cwd_and_cfg_paths():
    """
    Set current work dir and check if prefs exists in parent dir.
    """
    global cwd, cfg_paths
    cwd = os.path.abspath(os.path.dirname(__file__))
    _cwd_parent = os.path.abspath(os.path.join(cwd, os.pardir))
    cfg_paths = [cwd]

    if os.path.isdir(os.path.join(_cwd_parent, 'prefs')):
        cfg_paths.append(os.path.join(_cwd_parent, 'prefs'))


class Config(dict):
    """
    Config dict object.

    Written to make mamprefs isolated from the userPref file.
    """
    def __init__(self, file_=None):
        config_file = file_ or os.path.join(cwd, '.mamprefs')
        with open(config_file, 'rb') as f:
            data = json.loads(f.read())

        self.config_file = config_file
        super(Config, self).__init__(data)

    def __setitem__(self, key, value):
        super(Config, self).__setitem__(key, value)
        self.dump()

    def dump(self):
        with open(self.config_file, 'wb') as f:
            json.dump(self, f, indent=4, sort_keys=True)


def init(*args):
    """
    Initilizes the mampref package.

    Init takes one or several paths
    """
    global config

    # init config
    set_cwd_and_cfg_paths()
    config = Config()

    # add custom path for setting.
    if args:
        for i in args:
            cfg_paths.append(i)
    initialize_settings()

    job = cmds.scriptJob(e=['NewSceneOpened', initialize_settings])
    config['CURRENT_MAYA_SESSION_SCRIPTJOB_NUMBER'] = job


def initialize_settings():
    # Import package files and init them.
    from mamprefs import settings, markingmenus, layouts

    layouts.init()
    markingmenus.init()
    settings.init()


if __name__ == '__main__':
    pass
