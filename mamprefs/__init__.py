"""
"""
import os
import json
import logging


__title__ = 'mayaprefs'
__version__ = '0.1.3'
__author__ = 'Marcus Albertsson <marcus.arubertoson@gmail.com>'
__url__ = 'http://github.com/arubertoson/maya-mayaprefs'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Marcus Albertsson'


logger = logging.getLogger(__name__)

# Constants
_current_work_dir = ''
_config_paths = []
_config = {}


def set_cwd_and_cfg_paths():
    """
    Set current work dir and check if prefs exists in parent dir.
    """
    global _current_work_dir, _config_paths
    _current_work_dir = os.path.abspath(os.path.dirname(__file__))
    _cwd_parent = os.path.abspath(os.path.join(_current_work_dir, os.pardir))
    _config_paths = [_current_work_dir]

    if os.path.isdir(os.path.join(_cwd_parent, 'prefs')):
        _config_paths.append(os.path.join(_cwd_parent, 'prefs'))


class Config(dict):
    """
    Config dict object.

    Written to make mamprefs isolated from the userPref file.
    """
    def __init__(self, file_=None):
        _config_file = file_ or os.path.join(_current_work_dir, '.mamprefs')
        with open(_config_file, 'rb') as f:
            data = json.loads(f.read())

        self._config_file = _config_file
        super(Config, self).__init__(data)

    def __setitem__(self, key, value):
        super(Config, self).__setitem__(key, value)
        self.dump()

    def dump(self):
        with open(self._config_file, 'wb') as f:
            json.dump(self, f, indent=4, sort_keys=True)


def init(*args):
    """
    Initilizes the mampref package.

    Init takes one or several paths
    """
    global _config

    # init config
    set_cwd_and_cfg_paths()
    _config = Config()

    # add custom path for setting.
    if args:
        for i in args:
            _config_paths.append(i)

    # Import package files and init them.
    from mamprefs import settings, hotkeys, markingmenus, layouts

    hotkeys.init()
    layouts.init()
    markingmenus.init()
    settings.init()


if __name__ == '__main__':
    pass
