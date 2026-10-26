"""Exercise deployment setup with real Qt dialogs and an isolated SQLite database."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'application'))

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QWidget
from dbConnection import dbConnection
from dialogs import insertspcdlg
from dialogs.newspeciescollectiondlg import NewSpeciesCollectionDlg
from dialogs.newprojectdlg import NewProjectDlg
from dialogs.selectprojectdlg import SelectProjectDlg
from dialogs.makeseldlg import MakeSelDlg
from dialogs.newprofiledlg import NewProfileDlg


class ProjectSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.parent = QWidget()
        self.parent.appDB = dbConnection(':memory:', '', '', label=uuid4().hex, driver='QSQLITE')
        self.parent.appDB.dbOpen()
        schema = (ROOT / 'application/schema/Application.db.sql').read_text()
        schema = '\n'.join(line for line in schema.splitlines() if not line.lstrip().startswith('--'))
        for statement in schema.split(';'):
            if statement.strip():
                self.parent.appDB.dbExec(statement)
        self.warning = patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok).start()
        patch.object(QMessageBox, 'information', return_value=QMessageBox.Ok).start()

    def tearDown(self):
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog):
                widget.reject()
                widget.deleteLater()
        self.app.processEvents()
        self.parent.appDB.dbClose()
        self.parent.deleteLater()
        patch.stopall()

    def newCollection(self, name="Diver's collection"):
        dlg = NewSpeciesCollectionDlg(self.parent)
        dlg.nameEdit.setText(name)
        dlg.descriptionEdit.setPlainText("Today's species")
        dlg.species = [dict(name="Diver's fish", description="Fish's description", color='#12ab34', order='')]
        dlg.refreshSpecies(0)
        return dlg

    def count(self, table):
        return int(self.parent.appDB.dbQuery('SELECT COUNT(*) FROM ' + table).first()[0])

    def test_save_species_and_create_select_project(self):
        collection = self.newCollection()
        collection.saveBtn.click()
        self.assertEqual(collection.result(), QDialog.Accepted)
        query = self.parent.appDB.dbQuery('SELECT SPECIES_GROUP, DESCRIPTION, BUTTON_COLOR, SORT_ORDER FROM SPECIES_SETUP')
        self.assertEqual(query.first(), ["Diver's fish", "Fish's description", '18,171,52', None])
        selection = SelectProjectDlg(self.parent)
        self.assertEqual(selection.projModel.rowCount(), 0)

        def createProject(dlg):
            dlg.projNameEdit.setText("Diver's project")
            dlg.speciesBox.setCurrentText(collection.speciesCollection)
            dlg.metadataBox.setCurrentText('NoMetadata')
            dlg.okBtn.click()
            return dlg.result()

        with patch.object(NewProjectDlg, 'exec_', createProject):
            selection.createNewProjBtn.click()
        self.assertEqual(selection.selectedProjectDict['project'], "Diver's project")
        self.assertEqual(selection.selectedProjectDict['species_collection'], "Diver's collection")
        selection.okBtn.click()
        self.assertEqual(selection.result(), QDialog.Accepted)

    def test_project_dialog_selects_created_collection(self):
        def saveCollection(dlg):
            dlg.nameEdit.setText('New collection ' + str(self.count('SPECIES_COLLECTIONS')))
            dlg.species = [dict(name='Fish', description='', color='#ff0000', order='1')]
            dlg.saveCollection()
            return dlg.result()

        selection = SelectProjectDlg(self.parent)
        self.assertFalse(hasattr(selection, 'createSpeciesCollectionBtn'))
        project = NewProjectDlg(self.parent)
        project.projNameEdit.setText('Keep this draft')
        with patch.object(NewSpeciesCollectionDlg, 'exec', saveCollection):
            project.createSpeciesCollectionBtn.click()
        self.assertEqual(project.speciesBox.currentText(), 'New collection 0')
        self.assertEqual(project.speciesBox.count(), 1)
        self.assertEqual(project.projNameEdit.text(), 'Keep this draft')

    def test_cancel_leaves_no_collection_or_species(self):
        dlg = self.newCollection()
        dlg.cancelBtn.click()
        self.assertEqual(self.count('SPECIES_COLLECTIONS'), 0)
        self.assertEqual(self.count('SPECIES_SETUP'), 0)

    def test_validation_blocks_blank_empty_and_duplicate_collections(self):
        dlg = self.newCollection('  ')
        dlg.saveCollection()
        self.assertEqual(self.count('SPECIES_COLLECTIONS'), 0)
        dlg.nameEdit.setText('Valid')
        dlg.species.clear()
        dlg.saveCollection()
        self.assertEqual(self.count('SPECIES_COLLECTIONS'), 0)
        first = self.newCollection('Valid')
        first.saveCollection()
        duplicate = self.newCollection('Valid')
        duplicate.saveCollection()
        self.assertEqual(duplicate.result(), QDialog.Rejected)
        self.assertEqual(self.count('SPECIES_COLLECTIONS'), 1)
        self.assertEqual(self.count('SPECIES_SETUP'), 1)

    def test_failed_species_insert_rolls_back_whole_collection(self):
        dlg = self.newCollection()
        original = dlg.execute

        def failInsert(statement, values):
            if statement.startswith('INSERT INTO SPECIES_SETUP'):
                raise RuntimeError('Simulated write failure')
            return original(statement, values)

        with patch.object(dlg, 'execute', side_effect=failInsert):
            dlg.saveCollection()
        self.assertEqual(self.count('SPECIES_COLLECTIONS'), 0)
        self.assertEqual(self.count('SPECIES_SETUP'), 0)
        self.assertEqual(dlg.result(), QDialog.Rejected)

    def test_species_editor_insert_edit_delete_and_limit(self):
        dlg = NewSpeciesCollectionDlg(self.parent)

        def enterSpecies(editor):
            editor.speciesEdit.setText('Fish')
            editor.descEdit.setPlainText('A fish')
            return QDialog.Accepted

        with patch.object(insertspcdlg.InsertSpcDlg, 'exec', enterSpecies):
            dlg.insertBtn.click()
        self.assertEqual(dlg.species[0]['name'], 'Fish')

        def editSpecies(editor):
            editor.speciesEdit.setText('Updated fish')
            editor.sortEdit.setText('2')
            return QDialog.Accepted

        with patch.object(insertspcdlg.InsertSpcDlg, 'exec', editSpecies):
            dlg.editBtn.click()
        self.assertEqual(dlg.species[0]['name'], 'Updated fish')
        self.assertEqual(dlg.species[0]['order'], '2')
        dlg.deleteBtn.click()
        self.assertEqual(dlg.species, [])
        self.assertFalse(dlg.editBtn.isEnabled())
        dlg.species = [dict(name=str(i), description='', color='#ff0000', order='') for i in range(30)]
        dlg.refreshSpecies(0)
        self.assertFalse(dlg.insertBtn.isEnabled())

    def test_species_validation_preserves_existing_rows(self):
        dlg = self.newCollection()
        for name, order in [("Diver's fish", '1'), ('Another fish', 'invalid'), ('  ', '1')]:
            results = iter([QDialog.Accepted, QDialog.Rejected])

            def invalidSpecies(editor):
                editor.speciesEdit.setText(name)
                editor.sortEdit.setText(order)
                return next(results)

            with patch.object(insertspcdlg.InsertSpcDlg, 'exec', invalidSpecies):
                dlg.insertBtn.click()
            self.assertEqual(len(dlg.species), 1)
        self.assertEqual(self.warning.call_count, 3)

    def newProfile(self, name="Diver's profile"):
        dlg = NewProfileDlg(self.parent)
        dlg.profileNameEdit.setText(name)
        dlg.profileDescriptionEdit.setText("Diver's video profile")
        dlg.leftCamPathEdit.setText("left's camera")
        dlg.rightCamPathEdit.setText('right')
        dlg.imageTypeEdit.setText('mp4')
        return dlg

    def test_profile_creation_refreshes_and_selects_profile(self):
        selection = MakeSelDlg(self.parent, 'profile', 'active')
        self.assertEqual(selection.windowTitle(), 'Select Profile')
        self.assertFalse(selection.createProfileBtn.isHidden())

        def saveProfile(dlg):
            dlg.profileNameEdit.setText("Diver's profile")
            dlg.leftCamPathEdit.setText('left')
            dlg.rightCamPathEdit.setText('right')
            dlg.imageTypeEdit.setText('mp4')
            dlg.saveBtn.click()
            return dlg.result()

        with patch.object(NewProfileDlg, 'exec', saveProfile):
            selection.createProfileBtn.click()
        self.assertEqual(selection.value, "Diver's profile")
        self.assertEqual(selection.viewModel.rowCount(), 1)
        self.assertEqual(self.count('PROFILE_SETTINGS'), 12)
        selection.selectBtn.click()
        self.assertEqual(selection.result(), QDialog.Accepted)
        for mode in ('species', 'metadata'):
            other = MakeSelDlg(self.parent, mode)
            self.assertTrue(other.createProfileBtn.isHidden())
            self.assertNotEqual(other.windowTitle(), 'Select Profile')

    def test_profile_fields_defaults_and_cancel(self):
        dlg = self.newProfile()
        self.assertEqual(dlg.tabWidget.count(), 1)
        self.assertTrue(dlg.reloadBtn.isHidden())
        dlg.imageTypeEdit.clear()
        dlg.saveBtn.click()
        self.assertEqual(dlg.result(), QDialog.Accepted)
        values = dict(self.parent.appDB.dbQuery('SELECT SETTING, VALUE FROM PROFILE_SETTINGS'))
        self.assertEqual(values['ImageFileType'], 'jpg')
        self.assertEqual(values['LeftCameraImagePath'], "left's camera")
        self.assertEqual(values['RotateLeftImage'], '0')
        self.assertEqual(values['CollectMetadata'], 'No')
        cancelled = self.newProfile('Discard this profile')
        cancelled.cancelBtn.click()
        self.assertEqual(self.count('PROFILES'), 1)
        self.assertEqual(self.count('PROFILE_SETTINGS'), 12)

    def test_profile_rejects_blank_and_duplicate_names(self):
        blank = self.newProfile('   ')
        blank.saveProfile()
        self.assertEqual(self.count('PROFILES'), 0)
        first = self.newProfile()
        first.saveProfile()
        duplicate = self.newProfile()
        duplicate.saveProfile()
        self.assertEqual(duplicate.result(), QDialog.Rejected)
        self.assertEqual(self.count('PROFILES'), 1)
        self.assertEqual(self.count('PROFILE_SETTINGS'), 12)

    def test_profile_savepoint_preserves_settings_transaction(self):
        self.parent.appDB.startTransaction()
        dlg = self.newProfile()
        dlg.saveProfile()
        self.assertEqual(dlg.result(), QDialog.Accepted)
        self.assertEqual(self.count('PROFILES'), 1)
        self.parent.appDB.rollback()
        self.assertEqual(self.count('PROFILES'), 0)
        self.assertEqual(self.count('PROFILE_SETTINGS'), 0)

    def test_profile_failed_setting_insert_rolls_back(self):
        dlg = self.newProfile()
        original = dlg.execute

        def failInsert(statement, values=()):
            if statement.startswith('INSERT INTO PROFILE_SETTINGS'):
                raise RuntimeError('Simulated write failure')
            return original(statement, values)

        with patch.object(dlg, 'execute', side_effect=failInsert):
            dlg.saveProfile()
        self.assertEqual(self.count('PROFILES'), 0)
        self.assertEqual(self.count('PROFILE_SETTINGS'), 0)
        self.assertEqual(dlg.result(), QDialog.Rejected)


if __name__ == '__main__':
    unittest.main()
