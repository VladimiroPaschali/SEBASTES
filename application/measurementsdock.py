'''
measurementsdock is the Measurements panel: every measured line of the deployment with its name.
Names are edited in place (double-click); clicking a row goes to that frame and selects the fish.
'''

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from dbConnection import sqlQuote

#  The columns the user reads first come first, so that the panel at its default width shows them: the name, the species
#  and the length, then where the fish is (frame and target) and the details.
COLUMNS = ['Name', 'Species', 'Length (cm)', 'Frame', 'Target', 'Measurement', 'Distance (cm)', 'e (px)']
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
    #  the table was reloaded from the data database
    refreshed = Signal()

    def __init__(self, parent=None):
        super(MeasurementsDock, self).__init__('Measurements', parent)
        self.setObjectName('measurementsDockWidget')
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.dataDB = None
        self.deployment = None
        self.filling = False

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeader(CompactHeader(self.table))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # a name is edited in its cell: keep it a size to type in
        self.table.horizontalHeader().setMinimumSectionSize(56)
        self.table.horizontalHeader().setStretchLastSection(True)
        #  sorted by frame until the user clicks another column header
        self.table.horizontalHeader().setSortIndicator(FRAME, Qt.SortOrder.AscendingOrder)
        self.table.itemChanged.connect(self.nameChanged)
        self.table.cellClicked.connect(self.rowClicked)
        self.setWidget(self.table)


    def setDeployment(self, dataDB, deployment):
        self.dataDB = dataDB
        self.deployment = deployment
        self.refresh()


    def refresh(self):
        '''
        refresh reloads the measurements from the data database.
        '''
        if self.dataDB is None:
            return
        self.filling = True
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        query = self.dataDB.dbQuery("SELECT l.rowid, l.name, l.frame_number, l.target_number, t.species_group, l.line_label, l.length, p.range, l.error "+
            "FROM lines l LEFT JOIN targets t ON t.deployment_id=l.deployment_id AND t.frame_number=l.frame_number AND t.target_number=l.target_number "+
            "LEFT JOIN points p ON p.deployment_id=l.deployment_id AND p.frame_number=l.frame_number AND p.target_number=l.target_number "+
            "AND p.point_label='range_to_target' WHERE l.deployment_id='"+sqlQuote(self.deployment)+"' ORDER BY l.frame_number, l.target_number")
        for rowid, name, frame, target, species, label, length, rng, error in query:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [name or '', species or '', self.number(length), int(frame), int(target), label or '',
                      self.number(rng), self.number(error)]
            for col, value in enumerate(values):
                item = QTableWidgetItem()
                #  numbers are stored as numbers so that the columns sort correctly
                item.setData(Qt.ItemDataRole.DisplayRole, value)
                if col == NAME:
                    item.setData(Qt.ItemDataRole.UserRole, rowid)
                    item.setToolTip('Double-click to rename')
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
        name = sqlQuote(str(item.text()).strip())
        rowid = item.data(Qt.ItemDataRole.UserRole)
        self.dataDB.dbExec("UPDATE lines SET name='"+name+"' WHERE rowid="+str(rowid))


    def rowClicked(self, row, column):
        frame = self.table.item(row, FRAME)
        target = self.table.item(row, TARGET)
        if frame is not None and target is not None:
            self.goToTarget.emit(int(frame.data(Qt.ItemDataRole.DisplayRole)), int(target.data(Qt.ItemDataRole.DisplayRole)))
