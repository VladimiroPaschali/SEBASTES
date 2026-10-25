
from PySide6.QtCore  import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from dialogs.ui import  ui_NewProjectDlg
from dbConnection import sqlQuote

class NewProjectDlg(QDialog, ui_NewProjectDlg.Ui_newProjectDlg):
    def __init__(self, parent):
        super(NewProjectDlg, self).__init__(parent)
        self.setupUi(self)
        self.appDB=parent.appDB
        self.okBtn.clicked.connect(self.exitCheck)
        self.cancelBtn.clicked.connect(self.cancel)
        self.populateBoxWidgets()
        
    def populateBoxWidgets(self):
        query=self.appDB.dbQuery("SELECT SPECIES_COLLECTION FROM SPECIES_COLLECTIONS")
        for val,  in query:
            self.speciesBox.addItem(val)
        self.speciesBox.setCurrentIndex(-1)
        query=self.appDB.dbQuery("SELECT METADATA_GROUP FROM METADATA_GROUPS")
        for val,  in query:
            self.metadataBox.addItem(val)
        self.metadataBox.setCurrentIndex(-1)
        self.yesRadio.setChecked(True)
        
        
    def insertProject(self):
        '''
        insertProject adds the project to the application db. It returns False, after telling the
        user why, when the project can't be created.
        '''
        name=self.projNameEdit.text().strip()
        if name=='':
            QMessageBox.warning(self, "ERROR", 'Give the project a name!')
            return False
        if self.speciesBox.currentIndex()<0 or self.metadataBox.currentIndex()<0:
            QMessageBox.warning(self, "ERROR", 'Select species and metadata!')
            return False
        query=self.appDB.dbQuery("SELECT PROJECT FROM PROJECTS WHERE PROJECT='"+sqlQuote(name)+"'")
        if query.first()[0]!=None:
            QMessageBox.warning(self, "ERROR", 'There is a project called '+name+' already!')
            return False
        desc=self.descEdit.toPlainText()
        if self.yesRadio.isChecked():
            active='Yes'
        else:
            active='No'
        query=self.appDB.dbExec("INSERT INTO PROJECTS (PROJECT, DESCRIPTION, DATABASE_PATH, SPECIES_COLLECTION,  METADATA_GROUP,  ACTIVE) VALUES("+
        "'"+sqlQuote(name)+"', '"+sqlQuote(desc)+"', 'NA', '"+sqlQuote(self.speciesBox.currentText())+"', '"+sqlQuote(self.metadataBox.currentText())+"', '"+active+"')")
        # make sure it happened and tell folks so
        query1=self.appDB.dbQuery("SELECT PROJECT FROM PROJECTS WHERE PROJECT='"+sqlQuote(name)+"'")
        if query1.first()[0]!=None:
            QMessageBox.information(self, "NOTE", 'Project has been created!')
            return True
        QMessageBox.warning(self, "ERROR", 'Something is wrong: '+query.lastError().text())
        return False

    @Slot()
    def cancel(self):
        self.reject()
        

    def exitCheck(self):
        if self.insertProject():
            self.exit()
            
    @Slot()        
    def exit(self):
        self.accept()
        
