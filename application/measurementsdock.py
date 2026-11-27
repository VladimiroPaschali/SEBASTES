'''
measurementsdock is the Measurements panel: every measured line of the deployment with its name.
Names are edited in place (double-click); clicking a row goes to that frame and selects the fish.
'''

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from dbConnection import sqlQuote
import targetlinks

COLUMNS = ['obs_id', 'Species', 'Length (cm)', 'Frame']
NAME, SPECIES, LENGTH, FRAME = range(len(COLUMNS))
ROW_ID_ROLE = Qt.ItemDataRole.UserRole
TARGET_ROLE = ROW_ID_ROLE + 1
MEASUREMENT_ROLE = ROW_ID_ROLE + 2


def speciesKey(value):
    return ' '.join(value.split()).casefold()


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
        self.projectSpecies = ()
        self.knownSpecies = {}
        self.filling = False
        self.deletionEnabled = False

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setObjectName('measurementsTable')
        self.table.setHorizontalHeader(CompactHeader(self.table))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeaderItem(NAME).setToolTip('Observation ID')
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
        filters = QHBoxLayout()
        filters.setContentsMargins(4, 4, 4, 0)
        self.columnFilters = []
        for column, placeholder in enumerate(('Filter ID', 'Species', 'Length', 'Frame')):
            field = QLineEdit()
            field.setAccessibleName('Filter ' + COLUMNS[column])
            field.setPlaceholderText(placeholder)
            field.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            field.setClearButtonEnabled(True)
            if column in (LENGTH, FRAME):
                field.setToolTip('Enter an exact value or a range such as 10-20.')
            else:
                field.setToolTip('Enter part of the ' + COLUMNS[column] + ' to filter rows.')
            field.textChanged.connect(self.applyFilters)
            self.columnFilters.append(field)
            filters.addWidget(field, 1)
        layout.addLayout(filters)
        layout.addWidget(self.table)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.linkButton = QToolButton()
        self.linkButton.setDefaultAction(self.linkAction)
        buttons.addWidget(self.linkButton)
        buttons.addWidget(self.deleteButton)
        layout.addLayout(buttons)
        self.setWidget(content)
        self.table.model().layoutChanged.connect(self.applyFilters)
        self.updateDeleteAction()


    def setDeletionEnabled(self, enabled):
        self.deletionEnabled = enabled
        self.updateDeleteAction()


    def updateDeleteAction(self):
        count = len(self.visibleSelectedRows())
        enabled = self.deletionEnabled and self.dataDB is not None
        self.deleteAction.setEnabled(enabled and count > 0)
        self.deleteAction.setText('Delete measurements' if count > 1 else 'Delete measurement')
        self.linkAction.setEnabled(enabled and count == 1)

    def requestLink(self):
        if self.linkAction.isEnabled():
            index, = self.visibleSelectedRows()
            self.linkRequested.emit(*self.observationAt(index.row()))


    def requestDelete(self):
        if self.deleteAction.isEnabled():
            self.deleteRequested.emit([int(index.data(ROW_ID_ROLE)) for index in self.visibleSelectedRows()])

    def visibleSelectedRows(self):
        return [index for index in self.table.selectionModel().selectedRows(NAME)
                if not self.table.isRowHidden(index.row())]

    def observationAt(self, row):
        return (int(self.table.item(row, FRAME).data(Qt.ItemDataRole.DisplayRole)),
                int(self.table.item(row, NAME).data(TARGET_ROLE)))

    def selectTarget(self, frame, target):
        """Select a visible measurement for the marker without navigating back to it."""
        matching = None
        if target is not None:
            for row in range(self.table.rowCount()):
                if self.table.isRowHidden(row) or self.observationAt(row) != (frame, target):
                    continue
                item = self.table.item(row, NAME)
                if matching is None:
                    matching = item
                if item.data(MEASUREMENT_ROLE) == 'length':
                    matching = item
                    break
        selection = self.table.selectionModel()
        if matching is None:
            selection.clear()
        else:
            flags = QItemSelectionModel.SelectionFlag
            selection.setCurrentIndex(self.table.indexFromItem(matching), flags.ClearAndSelect | flags.Rows)
            self.table.scrollToItem(matching)

    def applyFilters(self):
        if self.filling:
            return
        text = [field.text().strip().casefold() for field in self.columnFilters]
        numericBounds = {}
        for column in (LENGTH, FRAME):
            if text[column]:
                values = text[column].replace(',', '.').split('-', 1)
                try:
                    numericBounds[column] = (float(values[0]), float(values[-1]))
                except ValueError:
                    numericBounds[column] = (float('inf'), float('-inf'))

        selection = self.table.selectionModel()
        selected = {index.row(): index for index in selection.selectedRows(NAME)}
        flags = QItemSelectionModel.SelectionFlag
        for row in range(self.table.rowCount()):
            matches = all(not text[column] or text[column] in self.table.item(row, column).text().casefold()
                          for column in (NAME, SPECIES))
            for column, (low, high) in numericBounds.items():
                value = self.table.item(row, column).data(Qt.ItemDataRole.DisplayRole)
                matches = matches and isinstance(value, (int, float)) and low <= value <= high
            self.table.setRowHidden(row, not matches)
            if not matches and row in selected:
                selection.select(selected[row], flags.Deselect | flags.Rows)
        current = selection.currentIndex()
        if current.isValid() and self.table.isRowHidden(current.row()):
            selection.clearCurrentIndex()
        self.updateDeleteAction()


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


    def setDeployment(self, dataDB, deployment, projectSpecies=()):
        if dataDB is not self.dataDB or deployment != self.deployment:
            for field in self.columnFilters:
                with QSignalBlocker(field):
                    field.clear()
        self.dataDB = dataDB
        self.deployment = deployment
        self.projectSpecies = tuple(projectSpecies)
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
        deployment = sqlQuote(self.deployment)
        speciesRows = self.dataDB.dbQuery("SELECT DISTINCT species_group FROM targets WHERE deployment_id='"
                                         +deployment+"' AND species_group IS NOT NULL")
        self.knownSpecies = {speciesKey(species): species for species in self.projectSpecies if species}
        for species, in speciesRows:
            if species:
                self.knownSpecies.setdefault(speciesKey(species), species)
        query = self.dataDB.dbQuery("SELECT l.rowid, l.name, l.frame_number, l.target_number, t.species_group, l.line_label, l.length "+
            "FROM lines l LEFT JOIN targets t ON t.deployment_id=l.deployment_id AND t.frame_number=l.frame_number AND t.target_number=l.target_number "+
            "WHERE l.deployment_id='"+deployment+"' ORDER BY l.frame_number, l.target_number")
        for rowid, name, frame, target, species, label, length in query:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [name or '', species or '', self.number(length), int(frame)]
            for col, value in enumerate(values):
                item = QTableWidgetItem()
                #  numbers are stored as numbers so that the columns sort correctly
                item.setData(Qt.ItemDataRole.DisplayRole, value)
                if col == NAME:
                    item.setData(ROW_ID_ROLE, rowid)
                    item.setData(TARGET_ROLE, int(target))
                    item.setData(MEASUREMENT_ROLE, label)
                    item.setToolTip('Double-click to edit the observation ID. Linked observations share the same ID.')
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)
            self.updateSpeciesWarning(row)
        self.table.setSortingEnabled(True)
        self.filling = False
        self.applyFilters()
        self.table.scrollToBottom()
        self.refreshed.emit()


    def preferredWidth(self):
        # width that shows every column
        return (self.table.horizontalHeader().length() + 2 * self.table.frameWidth() +
                self.table.verticalScrollBar().sizeHint().width())


    def number(self, value):
        if value is None:
            return ''
        return round(float(value), 2)

    def updateSpeciesWarning(self, row):
        obs_id = self.table.item(row, NAME).text()
        speciesItem = self.table.item(row, SPECIES)
        species = speciesItem.text()
        idKey = speciesKey(obs_id)
        prefix, _, suffix = idKey.rpartition(' ')
        impliedSpecies = self.knownSpecies.get(idKey) or (self.knownSpecies.get(prefix) if suffix.isdecimal() else None)
        if species and impliedSpecies and speciesKey(species) != speciesKey(impliedSpecies):
            message = f'Species mismatch. The recorded species is {species}, but obs_id “{obs_id}” indicates {impliedSpecies}. Check the annotation or link.'
            speciesItem.setIcon(self.table.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning))
            speciesItem.setToolTip(message)
            speciesItem.setData(Qt.ItemDataRole.AccessibleDescriptionRole, message)
        else:
            speciesItem.setIcon(QIcon())
            speciesItem.setToolTip('')
            speciesItem.setData(Qt.ItemDataRole.AccessibleDescriptionRole, None)


    def nameChanged(self, item):
        '''
        nameChanged saves a name edited in the table.
        '''
        if self.filling or item.column() != NAME:
            return
        name = item.text().strip()
        observation = self.observationAt(item.row())
        if targetlinks.has_identity(self.dataDB.db, self.deployment, observation):
            if name:
                targetlinks.rename(self.dataDB.db, self.deployment, observation, name)
            self.refresh()
        else:
            self.dataDB.dbExec("UPDATE lines SET name='"+sqlQuote(name)+"' WHERE rowid="+str(int(item.data(ROW_ID_ROLE))))
            self.updateSpeciesWarning(item.row())
            self.applyFilters()
        self.fishRenamed.emit()


    def rowClicked(self, row, column):
        if (QApplication.keyboardModifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
                or len(self.visibleSelectedRows()) > 1):
            return
        if self.table.item(row, NAME) is not None and not self.table.isRowHidden(row):
            self.goToTarget.emit(*self.observationAt(row))
