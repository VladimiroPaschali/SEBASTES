from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFormLayout, QHBoxLayout, QHeaderView,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)
from PySide6 import QtSql
from dialogs import insertspcdlg


class NewSpeciesCollectionDlg(QDialog):
    """Collect species in memory and save the complete collection atomically."""

    def __init__(self, parent):
        super().__init__(parent)
        self.appDB = parent.appDB
        self.speciesCollection = None
        self.species = []
        self.setWindowTitle('Create a new species collection')
        self.resize(700, 420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.nameEdit = QLineEdit(self)
        self.descriptionEdit = QPlainTextEdit(self)
        self.descriptionEdit.setMaximumHeight(90)
        form.addRow('Collection Name', self.nameEdit)
        form.addRow('Description', self.descriptionEdit)
        layout.addLayout(form)

        self.speciesView = QTableWidget(0, 4, self)
        self.speciesView.setHorizontalHeaderLabels(['Species', 'Description', 'Button Color', 'Sort Order'])
        self.speciesView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.speciesView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.speciesView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.speciesView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.speciesView)

        actions = QHBoxLayout()
        self.insertBtn = QPushButton('Insert', self)
        self.editBtn = QPushButton('Edit', self)
        self.deleteBtn = QPushButton('Delete', self)
        for button in (self.insertBtn, self.editBtn, self.deleteBtn):
            button.setAutoDefault(False)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancelBtn = QPushButton('Cancel', self)
        self.saveBtn = QPushButton('Save changes', self)
        buttons.addWidget(self.cancelBtn)
        buttons.addWidget(self.saveBtn)
        layout.addLayout(buttons)
        self.saveBtn.setDefault(True)

        self.insertBtn.clicked.connect(self.insertSpecies)
        self.editBtn.clicked.connect(self.editSpecies)
        self.deleteBtn.clicked.connect(self.deleteSpecies)
        self.speciesView.itemSelectionChanged.connect(self.updateActions)
        self.speciesView.doubleClicked.connect(self.editSpecies)
        self.cancelBtn.clicked.connect(self.reject)
        self.saveBtn.clicked.connect(self.saveCollection)
        self.updateActions()

    def updateActions(self):
        selected = self.speciesView.currentRow() >= 0
        self.editBtn.setEnabled(selected)
        self.deleteBtn.setEnabled(selected)
        self.insertBtn.setEnabled(len(self.species) < 30)

    def editSpecies(self):
        row = self.speciesView.currentRow()
        if row >= 0:
            self.speciesDialog(row)

    def insertSpecies(self):
        if len(self.species) < 30:
            self.speciesDialog()

    def speciesDialog(self, row=None):
        dlg = insertspcdlg.InsertSpcDlg(self)
        if row is not None:
            species = self.species[row]
            dlg.speciesEdit.setText(species['name'])
            dlg.descEdit.setPlainText(species['description'])
            dlg.col = QColor(species['color'])
            dlg.btnColLabel.setStyleSheet('QLabel { background-color: %s; }' % dlg.col.name())
            dlg.sortEdit.setText(species['order'])
        else:
            dlg.sortEdit.setText(str(len(self.species) + 1))

        # Keep the existing species editor open when a value needs correcting.
        while dlg.exec() == QDialog.Accepted:
            name = dlg.speciesEdit.text().strip()
            order = dlg.sortEdit.text().strip()
            if not name:
                QMessageBox.warning(self, 'ERROR', 'Give the species a name!')
                continue
            if any(item['name'] == name for index, item in enumerate(self.species) if index != row):
                QMessageBox.warning(self, 'ERROR', 'This collection already contains a species called ' + name + '.')
                continue
            try:
                if order:
                    int(order)
            except ValueError:
                QMessageBox.warning(self, 'ERROR', 'Sort order must be a whole number or left empty.')
                continue
            if not dlg.col.isValid():
                QMessageBox.warning(self, 'ERROR', 'Select a valid button color.')
                continue
            species = dict(name=name, description=dlg.descEdit.toPlainText(),
                           color=dlg.col.name(), order=order)
            if row is None:
                self.species.append(species)
                row = len(self.species) - 1
            else:
                self.species[row] = species
            self.refreshSpecies(row)
            break

    def refreshSpecies(self, selectedRow=None):
        self.speciesView.setRowCount(len(self.species))
        for row, species in enumerate(self.species):
            color = QColor(species['color'])
            values = (species['name'], species['description'],
                      '%d,%d,%d' % (color.red(), color.green(), color.blue()), species['order'])
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 2:
                    item.setIcon(self.colorIcon(color))
                self.speciesView.setItem(row, column, item)
        if selectedRow is not None:
            self.speciesView.selectRow(selectedRow)
        self.updateActions()

    @staticmethod
    def colorIcon(color):
        from PySide6.QtGui import QIcon, QPixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)
        return QIcon(pixmap)

    def deleteSpecies(self):
        row = self.speciesView.currentRow()
        if row >= 0:
            del self.species[row]
            self.refreshSpecies(min(row, len(self.species) - 1) if self.species else None)

    def execute(self, statement, values):
        query = QtSql.QSqlQuery(self.appDB.db)
        query.prepare(statement)
        for value in values:
            query.addBindValue(value)
        if not query.exec():
            raise RuntimeError(query.lastError().text())
        return query

    def saveCollection(self):
        name = self.nameEdit.text().strip()
        if not name:
            QMessageBox.warning(self, 'ERROR', 'Give the species collection a name!')
            self.nameEdit.setFocus()
            return
        if not self.species:
            QMessageBox.warning(self, 'ERROR', 'Insert at least one species before saving the collection.')
            return
        try:
            query = self.execute('SELECT 1 FROM SPECIES_COLLECTIONS WHERE SPECIES_COLLECTION = ?', [name])
            if query.next():
                QMessageBox.warning(self, 'ERROR', 'There is a species collection called ' + name + ' already!')
                return
            query.finish()
        except RuntimeError as error:
            QMessageBox.warning(self, 'ERROR', str(error))
            return
        if not self.appDB.db.transaction():
            QMessageBox.warning(self, 'ERROR', self.appDB.db.lastError().text())
            return
        try:
            self.execute('INSERT INTO SPECIES_COLLECTIONS (SPECIES_COLLECTION, DESCRIPTION) VALUES (?, ?)',
                         [name, self.descriptionEdit.toPlainText()])
            for species in self.species:
                color = QColor(species['color'])
                self.execute('INSERT INTO SPECIES_SETUP '
                             '(SPECIES_COLLECTION, SPECIES_GROUP, DESCRIPTION, BUTTON_COLOR, SORT_ORDER) '
                             'VALUES (?, ?, ?, ?, ?)',
                             [name, species['name'], species['description'],
                              '%d,%d,%d' % (color.red(), color.green(), color.blue()),
                              int(species['order']) if species['order'] else None])
            if not self.appDB.db.commit():
                raise RuntimeError(self.appDB.db.lastError().text())
        except RuntimeError as error:
            self.appDB.db.rollback()
            QMessageBox.warning(self, 'ERROR', 'Could not save the species collection: ' + str(error))
            return
        self.speciesCollection = name
        self.accept()
