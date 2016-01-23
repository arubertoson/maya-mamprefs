"""
"""
from maya import cmds

from mamprefs import _config


__all__ = ['script_output']


def script_output(direction):
    """
    Script output dock for layouts.
    """
    dock_control = _config['WINDOW_SCRIPT_OUTPUT_DOCK']
    dock_window = _config['WINDOW_SCRIPT_OUTPUT']
    if cmds.dockControl(dock_control, ex=True):
        return cmds.dockControl(dock_control, e=True, vis=True, fl=False)

    if cmds.window(dock_window, ex=True):
        main_win = dock_window
    else:
        main_win = cmds.window(dock_window, title='Output Window')

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
        dock_control,
        content=main_win,
        label='Output Window',
        area=direction,
        height=500,
        floating=False,
        allowedArea=['left', 'right']
        )


if __name__ == '__main__':
    pass
