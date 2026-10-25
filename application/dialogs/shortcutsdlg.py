'''
shortcutsdlg is the Help > Keyboard Shortcuts window: every key and mouse gesture SEBASTES reacts to, in groups.
The keys of actions and buttons are read from the actions themselves (shortcutGroups), so they follow a change of
the shortcut; the keys that the main window and the image viewers handle themselves (arrows, Delete, Esc, the mouse)
are written here, where they are handled: SEBASTES.__keyPressEvent, SEBASTES.imageClick, QViewerBase.
The colours come from the style sheet in theme.py (objects keyCap, shortcutGroup).
'''

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


def shortcutText(widget):
    #  the shortcut of an action or of a QShortcut as the user reads it, '' when it has none
    sequence = widget.key() if isinstance(widget, QShortcut) else widget.shortcut()
    return sequence.toString(QKeySequence.SequenceFormat.NativeText)


def shortcutGroups(window):
    '''
    shortcutGroups returns the shortcuts as [(group, [(keys, what it does), ...]), ...]. keys is text; a '+'
    joins the keys that are pressed together (Shift+Click).
    '''
    return [
        ('Navigation', [
            ('Left / Right', 'Previous / next sampled frame (the step is the Every box)'),
            ('Ctrl+Left / Right', 'Previous / next frame'),
            (shortcutText(window.playKey), 'Play or pause (not while recording)'),
            (shortcutText(window.actionLoad), 'Open a deployment'),
            ('Enter', 'In the Frame box: go to the frame typed there'),
            ('Click', 'Timeline: go to that frame. Measurements panel: go to the frame of a row and show its fish'),
        ]),
        ('View', [
            ('Wheel', 'Zoom in or out around the selected target, in both images'),
            ('Ctrl+Wheel', 'Zoom in or out around the pointer, in the image under it'),
            ('Alt+Drag', 'Move a zoomed image'),
            (shortcutText(window.labelCheck), 'Show or hide the labels'),
            (shortcutText(window.actionShortcuts), 'This window'),
            (shortcutText(window.actionExit), 'Exit SEBASTES'),
        ]),
        ('Marking (while recording)', [
            (shortcutText(window.recordBtn), 'Start or stop recording'),
            ('1 - 9', 'Select the species button with that number in the tab on screen, again to deselect it'),
            ('Click', 'Count mark of the selected species, in one image'),
            ('Shift+Click', 'Stereo target of the selected species: the head in the left image, then the same point in '
                            'the right image, then the tail in the same way. With Stereo Targets Only every click '
                            'marks a stereo target'),
            (shortcutText(window.measureBtn), 'Measure Target: draw the length of the selected target in both images'),
            ('Drag', 'With Measure Target: draw the length line in one image, then in the other'),
            ('A', 'Auto Match on or off: the matching point of the other image is found for you'),
            ('Z', 'With Auto Match: undo the last target'),
            ('Esc', 'Cancel the pair or the measurement being marked and reload the frame'),
        ]),
        ('Editing (while recording)', [
            ('Right-click', 'Select a mark and its pair in the other image'),
            ('Delete', 'Delete the selected mark and its data'),
            ('Home', 'Link the selected target to a target of the next frame'),
            ('Double-click', 'Species button: choose another species for the button'),
            ('Double-click / F2', 'Measurements panel: rename the measurement'),
        ]),
    ]


class ShortcutsDlg(QDialog):

    #  the groups that go in the left and in the right column
    COLUMNS = [['Navigation', 'View'], ['Marking (while recording)', 'Editing (while recording)']]

    def __init__(self, window, parent=None):
        super(ShortcutsDlg, self).__init__(parent or window)
        self.setWindowTitle('Keyboard Shortcuts')
        self.groups = dict(shortcutGroups(window))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 14)
        layout.setSpacing(12)
        columns = QHBoxLayout()
        columns.setSpacing(36)
        for names in self.COLUMNS:
            column = QVBoxLayout()
            column.setSpacing(6)
            for name in names:
                column.addWidget(self.groupHeading(name))
                for keys, what in self.groups[name]:
                    column.addLayout(self.row(keys, what))
                column.addSpacing(10)
            column.addStretch(1)
            columns.addLayout(column, 1)
        layout.addLayout(columns)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def groupHeading(self, name):
        heading = QLabel(name.upper())
        heading.setObjectName('shortcutGroup')
        return heading

    def row(self, keys, what):
        '''
        row is one shortcut: its keys drawn as key caps, and what it does.
        '''
        line = QHBoxLayout()
        line.setSpacing(12)
        capBox = QWidget()
        capBox.setFixedWidth(190)
        caps = QHBoxLayout(capBox)
        caps.setContentsMargins(0, 0, 0, 0)
        caps.setSpacing(4)
        #  alternatives are separated by ' / ', the keys pressed together by '+'
        for index, alternative in enumerate(keys.split(' / ')):
            if index > 0:
                caps.addWidget(QLabel('/'))
            for position, key in enumerate(alternative.split('+')):
                if position > 0:
                    caps.addWidget(QLabel('+'))
                cap = QLabel(key)
                cap.setObjectName('keyCap')
                caps.addWidget(cap)
        caps.addStretch(1)
        line.addWidget(capBox, 0, Qt.AlignmentFlag.AlignTop)
        text = QLabel(what)
        text.setWordWrap(True)
        text.setMinimumWidth(260)
        line.addWidget(text, 1)
        return line
