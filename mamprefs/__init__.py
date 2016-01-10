"""
"""

__title__ = 'mayaprefs'
__version__ = '0.1.3'
__author__ = 'Marcus Albertsson'
__email__ = 'marcus.arubertoson@gmail.com'
__url__ = 'http://github.com/arubertoson/maya-mayaprefs'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015 Marcus Albertsson'


# Module imports
import logging

from mamprefs import (base, settings, hotkeys, markingmenus, constants,
                      layouts)

logger = logging.getLogger(__name__)


def init(*args):
    """
    Initilizes the mampref package.

    Init takes one or several paths
    """
    if args:
        for i in args:
            constants.CONFIG_PATHS.append(i)

    # Init scripts
    settings.init()
    hotkeys.init()
    markingmenus.init()
    layouts.init()


def show_menu(menu):
    MM = markingmenus.MarkingMenuManager
    if MM.instance is None:
        MM.instance = MM()

    try:
        MM.instance[menu].show()
    except KeyError:
        logger.error('{} is not in manager.'.format(menu))


def hide_menu():
    base.deleteUI(constants.MARKING_MENU_POPUP_NAME)


if __name__ == '__main__':
    init()
