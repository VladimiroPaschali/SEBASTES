'''
measurementsdock is the Measurements panel: every measured line of the deployment with its name.
Names are edited in place (double-click); clicking a row goes to that frame and selects the fish.
'''

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from dbConnection import sqlQuote
import targetlinks

#  The columns the user reads first come first, so that the panel at its default width shows them: the name, the species
#  and the length, then where the fish is (frame and target) and the details.
COLUMNS = ['Name', 'Species', 'Length (cm)', 'Frame', 'Target', 'Measurement', 'Distance (cm)', 'e (px)', 'Linked from (frame / target)']
NAME, SPECIES, LENGTH, FRAME, TARGET = 0, 1, 2, 3, 4


class CompactHeader(QHeaderView):
    '''
    Qt makes every section of a header that shows a sort indicator wide enough for the arrow, although the arrow is
    drawn in one section only. In a panel of 380 px that is more than a column of numbers can spare, so here only the
    sorted section keeps the room (and the sections are measured again when the sort column changes).
    '''

    def __init__(self, parent=None):
        super(CompactHeader, self).__init__(Qt.Orientation.Horizontal, parent)
        self.sortIndicatorChanged.connect(lambda *args: self.resizeSections(QHeaderView.ResizeMode.ResizeToContents))

    def sectionSizeFromContents(self, logicalIndex):
        size = super(CompactHeader, self).sectionSizeFromContents(logicalIndex)
        if self.isSortIndicatorShown() and logicalIndex != self.sortIndicatorSection():
            margin = self.style().pixelMetric(QStyle.PixelMetric.PM_HeaderMargin, None, self)
            size.setWidth(size.width() - size.height() - margin)
        return size


class MeasurementsDock(QDockWidget):

    #  frame and target number of the clicked row
    goToTarget = Signal(int, int)
    deleteRequested = Signal(list)
    linkRequested = Signal(int, int)
    fishRenamed = Signal()
    #  the table was reloaded from the data database
    refreshed = Signal()

    def __init__(self, parent=None):
        super(MeasurementsDock, self).__init__('Measurements', parent)
        self.setObjectName('measurementsDockWidget')
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.dataDB = None
        self.deployment = None
        self.filling = False
        self.deletionEnabled = False

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeader(CompactHeader(self.table))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # a name is edited in its cell: keep it a size to type in
        self.table.horizontalHeader().setMinimumSectionSize(56)
        self.table.horizontalHeader().setStretchLastSection(True)
        #  sorted by frame until the user clicks another column header
        self.table.horizontalHeader().setSortIndicator(FRAME, Qt.SortOrder.AscendingOrder)
        self.table.itemChanged.connect(self.nameChanged)
        self.table.cellClicked.connect(self.rowClicked)
        self.table.itemSelectionChanged.connect(self.updateDeleteAction)
        self.deleteAction = QAction('Delete measurement', self)
        self.deleteAction.setToolTip('Delete the selected measurements (Record only)')
        self.deleteAction.triggered.connect(self.requestDelete)
        self.linkAction = QAction('Link fish…', self)
        self.linkAction.triggered.connect(self.requestLink)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)
        self.deleteButton = QToolButton()
        self.deleteButton.setDefaultAction(self.deleteAction)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.linkButton = QToolButton()
        self.linkButton.setDefaultAction(self.linkAction)
        buttons.addWidget(self.linkButton)
        buttons.addWidget(self.deleteButton)
        layout.addLayout(buttons)
        self.setWidget(content)
        self.updateDeleteAction()


    def setDeletionEnabled(self, enabled):
        self.deletionEnabled = enabled
        self.updateDeleteAction()


    def updateDeleteAction(self):
        count = len(self.table.selectionModel().selectedRows())
        enabled = self.deletionEnabled and self.dataDB is not None
        self.deleteAction.setEnabled(enabled and count > 0)
        self.deleteAction.setText('Delete measurements' if count > 1 else 'Delete measurement')
        self.linkAction.setEnabled(enabled and count == 1)

    def requestLink(self):
        if self.linkAction.isEnabled():
            row = self.table.selectionModel().selectedRows()[0].row()
            self.linkRequested.emit(int(self.table.item(row, FRAME).text()), int(self.table.item(row, TARGET).text()))


    def requestDelete(self):
        if self.deleteAction.isEnabled():
            rows = self.table.selectionModel().selectedRows(NAME)
            self.deleteRequested.emit([int(index.data(Qt.ItemDataRole.UserRole)) for index in rows])


    def showContextMenu(self, position):
        item = self.table.itemAt(position)
        if item is None:
            return
        selection = self.table.selectionModel()
        index = self.table.indexFromItem(item)
        if not selection.isSelected(index):
            selection.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)
        menu = QMenu(self.table)
        menu.addAction(self.linkAction)
        menu.addAction(self.deleteAction)
        menu.exec(self.table.viewport().mapToGlobal(position))


    def setDeployment(self, dataDB, deployment):
        self.dataDB = dataDB
        self.deployment = deployment
        self.refresh()


    def refresh(self):
        '''
        refresh reloads the measurements from the data database.
        '''
        if self.dataDB is None:
            #  no deployment: nothing to show
            self.table.setRowCount(0)
            return
        self.filling = True
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        query = self.dataDB.dbQuery("SELECT l.rowid, l.name, l.frame_number, l.target_number, t.species_group, l.line_label, l.length, p.range, l.error, t.target_link_frame, t.target_link "+
            "FROM lines l LEFT JOIN targets t ON t.deployment_id=l.deployment_id AND t.frame_number=l.frame_number AND t.target_number=l.target_number "+
            "LEFT JOIN points p ON p.deployment_id=l.deployment_id AND p.frame_number=l.frame_number AND p.target_number=l.target_number "+
            "AND p.point_label='range_to_target' WHERE l.deployment_id='"+sqlQuote(self.deployment)+"' ORDER BY l.frame_number, l.target_number")
        for rowid, name, frame, target, species, label, length, rng, error, sourceFrame, sourceTarget in query:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [name or '', species or '', self.number(length), int(frame), int(target), label or '',
                      self.number(rng), self.number(error), f'{sourceFrame} / {sourceTarget}' if sourceFrame is not None else '']
            for col, value in enumerate(values):
                item = QTableWidgetItem()
                #  numbers are stored as numbers so that the columns sort correctly
                item.setData(Qt.ItemDataRole.DisplayRole, value)
                if col == NAME:
                    item.setData(Qt.ItemDataRole.UserRole, rowid)
                    item.setToolTip('Double-click to rename this fish across its linked observations')
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.table.scrollToBottom()
        self.filling = False
        self.refreshed.emit()


    def preferredWidth(self):
        # width that shows every column
        return (self.table.horizontalHeader().length() + 2 * self.table.frameWidth() +
                self.table.verticalScrollBar().sizeHint().width())


    def number(self, value):
        if value is None:
            return ''
        return round(float(value), 2)


    def nameChanged(self, item):
        '''
        nameChanged saves a name edited in the table.
        '''
        if self.filling or item.column() != NAME:
            return
        name = item.text().strip()
        observation = (int(self.table.item(item.row(), FRAME).text()), int(self.table.item(item.row(), TARGET).text()))
        if targetlinks.has_identity(self.dataDB.db, self.deployment, observation):
            if name:
                targetlinks.rename(self.dataDB.db, self.deployment, observation, name)
            self.refresh()
        else:
            self.dataDB.dbExec("UPDATE lines SET name='"+sqlQuote(name)+"' WHERE rowid="+str(int(item.data(Qt.ItemDataRole.UserRole))))
        self.fishRenamed.emit()


    def rowClicked(self, row, column):
        if (QApplication.keyboardModifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
                or len(self.table.selectionModel().selectedRows()) > 1):
            return
        frame = self.table.item(row, FRAME)
        target = self.table.item(row, TARGET)
        if frame is not None and target is not None:
            self.goToTarget.emit(int(frame.data(Qt.ItemDataRole.DisplayRole)), int(target.data(Qt.ItemDataRole.DisplayRole)))
