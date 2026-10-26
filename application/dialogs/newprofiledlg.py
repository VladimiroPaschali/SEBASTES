from PySide6 import QtSql
from PySide6.QtWidgets import QDialog, QMessageBox
from dialogs.ui import ui_ProfileSetupDlg
from dialogs import frameextracthelpdlg, timestampextracthelpdlg, subsamplemaskhelpdlg


class NewProfileDlg(QDialog, ui_ProfileSetupDlg.Ui_profileSetupDlg):
    """Create a profile using the existing profile form without changing other settings."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.appDB = parent.appDB
        self.profile = None
        self.setWindowTitle('Create a new profile')
        self.tabWidget.removeTab(2)
        self.tabWidget.removeTab(1)
        self.tabWidget.tabBar().hide()
        for widget in (self.newProfileBtn, self.selectProfileBtn, self.label_28, self.reloadBtn):
            widget.hide()

        self.timestampTypeBox.addItems(['in_file_name', 'EXIF', 'none'])
        self.timestampTypeBox.setCurrentIndex(-1)
        for box in (self.rotateLeftBox, self.rotateRightBox):
            box.addItems(['0', '90', '180', '270'])
        self.metadataNoBtn.setChecked(True)
        self.settingWidgets = {
            'LeftCameraImagePath': self.leftCamPathEdit,
            'RightCameraImagePath': self.rightCamPathEdit,
            'CalibrationFileName': self.calFilePathEdit,
            'FrameNumberIndices': self.stFrameIndEdit,
            'ImageTimestampType': self.timestampTypeBox,
            'ImageTimestampFormat': self.timestampFormatEdit,
            'ImageTimestampStart': self.timestampStartEdit,
            'ImageFileType': self.imageTypeEdit,
            'CollectMetadata': self.metadataYesBtn,
            'RotateLeftImage': self.rotateLeftBox,
            'RotateRightImage': self.rotateRightBox,
            'SubsampleMask': self.subsampleMaskEdit,
        }
        for setting, description in self.appDB.dbQuery('SELECT SETTING, DESCRIPTION FROM SETTING_DESCRIPTIONS'):
            if setting in self.settingWidgets:
                self.settingWidgets[setting].setToolTip(description)

        self.frameIndHelpBtn.clicked.connect(lambda: frameextracthelpdlg.FrameExtractHelpDlg(self).exec())
        self.timestampFormatBtn.clicked.connect(lambda: timestampextracthelpdlg.TimestampExtractHelpDlg(self).exec())
        self.subsampleMaskBtn.clicked.connect(lambda: subsamplemaskhelpdlg.SubsampleMaskHelpDlg(self).exec())
        self.cancelBtn.clicked.connect(self.reject)
        self.saveBtn.clicked.connect(self.saveProfile)
        self.profileNameEdit.setFocus()

    def execute(self, statement, values=()):
        query = QtSql.QSqlQuery(self.appDB.db)
        query.prepare(statement)
        for value in values:
            query.addBindValue(value)
        if not query.exec():
            raise RuntimeError(query.lastError().text())
        return query

    def saveProfile(self):
        name = self.profileNameEdit.text().strip()
        if not name:
            QMessageBox.warning(self, 'ERROR', 'Give the profile a name!')
            self.profileNameEdit.setFocus()
            return
        values = {
            'LeftCameraImagePath': self.leftCamPathEdit.text(),
            'RightCameraImagePath': self.rightCamPathEdit.text(),
            'CalibrationFileName': self.calFilePathEdit.text(),
            'FrameNumberIndices': self.stFrameIndEdit.text() + '-' + self.endFrameIndEdit.text(),
            'ImageTimestampType': self.timestampTypeBox.currentText(),
            'ImageTimestampFormat': self.timestampFormatEdit.text(),
            'ImageTimestampStart': self.timestampStartEdit.text(),
            'ImageFileType': self.imageTypeEdit.text().strip() or 'jpg',
            'CollectMetadata': 'Yes' if self.metadataYesBtn.isChecked() else 'No',
            'RotateLeftImage': self.rotateLeftBox.currentText(),
            'RotateRightImage': self.rotateRightBox.currentText(),
            'SubsampleMask': self.subsampleMaskEdit.text(),
        }
        try:
            query = self.execute('SELECT 1 FROM PROFILES WHERE PROFILE = ?', [name])
            if query.next():
                QMessageBox.warning(self, 'ERROR', 'There is a profile called ' + name + ' already!')
                return
            query.finish()
            # A savepoint also works when Settings already has an open transaction.
            self.execute('SAVEPOINT create_profile')
        except RuntimeError as error:
            QMessageBox.warning(self, 'ERROR', str(error))
            return
        try:
            self.execute('INSERT INTO PROFILES (PROFILE, ACTIVE, DESCRIPTION) VALUES (?, ?, ?)',
                         [name, 'Yes', self.profileDescriptionEdit.text()])
            for setting, value in values.items():
                self.execute('INSERT INTO PROFILE_SETTINGS (PROFILE, SETTING, VALUE) VALUES (?, ?, ?)',
                             [name, setting, value])
            self.execute('RELEASE SAVEPOINT create_profile')
        except RuntimeError as error:
            self.execute('ROLLBACK TO SAVEPOINT create_profile')
            self.execute('RELEASE SAVEPOINT create_profile')
            QMessageBox.warning(self, 'ERROR', 'Could not save the profile: ' + str(error))
            return
        self.profile = name
        self.accept()
