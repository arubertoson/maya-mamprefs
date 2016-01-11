"""
"""
from maya import cmds

from mamprefs.constants import *

__all__ = ['script_output']


def script_output(direction):
    """
    """
    if cmds.dockControl(SCRIPT_OUTPUT_DOCK, ex=True):
        return cmds.dockControl(SCRIPT_OUTPUT_DOCK, e=True, vis=True, fl=False)

    if cmds.window(SCRIPT_OUTPUT_WINDOW, ex=True):
        main_win = SCRIPT_OUTPUT_WINDOW
    else:
        main_win = cmds.window(SCRIPT_OUTPUT_WINDOW, title='Output Window')

    cmds.paneLayout(parent=main_win)

    # context menu
    output_win = cmds.cmdScrollFieldReporter(fst="")
    cmds.popupMenu(parent=output_win)
    cmds.menuItem(
        label='Clear Output',
        command=lambda c: cmds.cmdScrollFieldReporter(
            output_win, e=True, clear=True),
    )
    # Echo all commands toggle
    cmds.menuItem(
        label='Toggle Echo Commands',
        command=lambda c: cmds.commandEcho(
            state=not(cmds.commandEcho(q=True, state=True))),
    )
    # Go to python reference
    cmds.menuItem(
        label='Python Command Reference',
        command=lambda c: cmds.showHelp('DocsPythonCommands'),
    )

    cmds.dockControl(
        SCRIPT_OUTPUT_DOCK,
        content=main_win,
        label='Output Window',
        area=direction,
        height=500,
        floating=False,
        allowedArea=['left', 'right']
        )


if __name__ == '__main__':
    pass
