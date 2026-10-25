
 #!/usr/bin/env python

import sys
import os
from PySide6.QtCore  import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from ui import ui_SEBASTES_dockable
import pyStereoComp, dbConnection, videoSource, measurementsdock, theme, epipolar
from dbConnection import sqlQuote
import numpy as ny
import cv2
from math import *
import traceback
import glob
import getpass
import pathlib
import re
import json
import bisect
import random
import sqlite3
from datetime import datetime,  timezone
from dialogs import speciesgroupdlg, closeupdlg, dataviewdlg, commentdlg, editspeciesdlg, framecommentdlg,  makeseldlg,  profilesetupdlg,  guisettingdlg,  selectprojectdlg, annotatorDlg, viewapplicationdbdlg,  directeditDBdlg
from exif import Image

#  The version of the layout of the window that closeEvent saves with the geometry and the places of the docks. Raise it when
#  the layout changes, so that the layouts saved before are not restored over the new one.
LAYOUT_VERSION = 1

#  the width of the Measurements panel when no layout was saved
MEASUREMENTS_WIDTH = 380

#  how many deployments the welcome page lists as the ones opened last
RECENT_DEPLOYMENTS = 8


def strtobool(val):
    # replaces distutils.util.strtobool - distutils was removed in Python 3.12
    return str(val).lower() in ('y', 'yes', 't', 'true', 'on', '1')


class SEBASTES(QMainWindow, ui_SEBASTES_dockable.Ui_SEBASTES):

    def __init__(self, parent=None):
        super(SEBASTES, self).__init__(parent)
        self.setupUi(self)
        self.setupToolBar()
        self.setupStatusBar()

        self.__leftDirScanned = False
        self.__rightDirScanned = False
        self.__leftDateTime = None
        self.__rightDateTime = None
        self.noLoad=True
        self.matchMode=False
        self.pairPoints=[]
        self.linkData=[]
        self.garbage=[]
        self.datadlg = None
        self.activeProfile = None
        self.speciesCollection = None
        self.metadataGroup = None
        self.frameComment=''
        self.defaultMonoCamera=None
        self.activeGV='Both'
        self.defaultMetadataGroup='CamTrawl_metadata'
        self.randomCellBounds=None
        self.annotator=None
        self.timestamp_format='%Y-%m-%d %H:%M:%S'

#        self.keystrokeMap={}

        self.key=None
        self.dataDB=None
        self.appDB=None
        self.deployment=None
        self.pairedTarget=False
        self.Habitat1=None
        self.Habitat2=None
        self.selColor=[0, 255, 0]
        self.selThickness=4
        self.textOffset = QPointF(-4,-4)
        
        # the Auto Match threshold is a line edit that is never shown: Annotate > Match Threshold sets it
        self.matchThresholdEdit=QLineEdit(self)
        self.matchThresholdEdit.hide()

        # dont mess with this code
        self.spcButtons=[self.btn1, self.btn2, self.btn3, self.btn4, self.btn5, self.btn6, self.btn7, self.btn8, self.btn9, self.btn10,
            self.btn11, self.btn12, self.btn13, self.btn14, self.btn15, self.btn16, self.btn17, self.btn18, self.btn19, self.btn20, 
            self.btn21, self.btn22, self.btn23, self.btn24, self.btn25, self.btn26, self.btn27, self.btn28, self.btn29, self.btn30]
        self.optionsBoxes=[self.labelCheck, self.showDataCheck, self.closeupCheck, self.metadataCheckBox]
        self.metadataLineEdits=[self.lineEdit1_1, self.lineEdit1_2, self.lineEdit1_3, self.lineEdit1_4, self.lineEdit1_5]
        self.metadataLineEditLabels=[self.label1_1, self.label1_2, self.label1_3, self.label1_4, self.label1_5]
        self.metadataCheckBoxes=[self.checkBox1_1, self.checkBox1_2, self.checkBox1_3, self.checkBox1_4, self.checkBox1_5]
        self.radioBtnTags1=[self.radioButton1_1, self.radioButton1_2, self.radioButton1_3, self.radioButton1_4, self.radioButton1_5, self.radioButton1_6,
                           self.radioButton1_7, self.radioButton1_8, self.radioButton1_9, self.radioButton1_10]
        self.radioBtnTags2=[self.radioButton2_1, self.radioButton2_2, self.radioButton2_3, self.radioButton2_4, self.radioButton2_5, self.radioButton2_6,
                           self.radioButton2_7, self.radioButton2_8, self.radioButton2_9, self.radioButton2_10]
        self.radioBtnTags3=[self.radioButton3_1, self.radioButton3_2]
        self.metadataStickyBox.setEnabled(False)
        self.metadataWidgets=[self.exclusiveRadioBox1, self.exclusiveRadioBox2, self.exclusiveRadioBox3, self.metadataStickyBox, self.extraMetadataFrame]
        self.metadataTypesDict={}
        self.recordEnableWidgets=[self.recomputeBtn,self.trainBtn,self.measureBtn, self.measurementBox, self.linkBtn , self.targetCommentBtn, self.frameCommentBtn,
                            self.computeMatchBox, self.actionMatchThreshold, self.stereoOnlyCheckBox, self.showDataCheck, self.editSpeciesBtn, self.gridCheck,  self.clearGridBtn,  self.delLinkBtn, self.lastFrameBtn]
        self.bboxEnableWidgets=[self.recomputeBtn,self.measureBtn, self.linkBtn,
                            self.computeMatchBox, self.actionMatchThreshold, self.stereoOnlyCheckBox, self.showDataCheck]
        # Measure Target and its measurement list are shown only while Measure Target is enabled
        self.measureWidgets=[self.measureBtn, self.measurementBox]
        self.measureBtn.changed.connect(self.updateMeasureWidgets)
        # the target link and species tools only work while recording, so they are shown only then
        self.recordOnlyWidgets=[self.linkBtn, self.editSpeciesBtn, self.targetBox, self.delLinkBtn]
        self.showTools(self.recordOnlyWidgets, False)
        # buttons that move through the frames: they work once a deployment is loaded
        self.navWidgets=[self.firstBtn, self.prevSampleBtn, self.prevFrameBtn, self.nextFrameBtn, self.nextSampleBtn, self.lastBtn]
        self.setNavEnabled(False)
        self.copyBtn.setEnabled(False)
        # the time of the frame is shown for video deployments only; the room for all its digits is kept so the controls don't move
        self.timeLabel.setContentsMargins(14, 0, 0, 0)
        self.timeLabel.setMinimumWidth(self.timeLabel.fontMetrics().horizontalAdvance('00:00:00.00')+14)
        self.timeLabel.hide()

        self.playBtn.setEnabled(False)
        #  set the base directory path - this is the full path to this application
        import functools
        self.baseDir = functools.reduce(lambda l,r: l + os.path.sep + r,
                              os.path.dirname(os.path.realpath(__file__)).split(os.path.sep))
        try:
            self.setWindowIcon(QIcon(self.baseDir + '/'  + 'resources' + '/' + 'rockfish.png'))
        except:
            pass

        self.gotData = False
        self.first=True
        self.__selectedItems=[]
        self.targetComment=''

        self.rubberBanding = False
        self.pointMarks = {}
        self.lineMarks = {}
        self.boxMarks = {}
        self.makeBoxes = False
        self.activeMark = {self.gvLeft:None, self.gvRight:None}
        self.activeLine = {self.gvLeft:None, self.gvRight:None}
        # guided fish marking: 0 head left, 1 head right, 2 tail left, 3 tail right
        self.fishStep = 0
        self.fishTarget = None
        self.fishHead = None
        self.fishHeadMarks = None
        self.fishLines = {}
        # the epipolar curves drawn in each image while a stereo pair is half done (updateEpipolar)
        self.epipolarItems = {self.gvLeft:[], self.gvRight:[]}
        self.previousLineName = None
        # (frame, target) chosen in the Measurements panel, shown over the other fish when not recording
        self.annotationFocus = None
        self.gridLines = {self.gvLeft:[], self.gvRight:[]}
        self.randomCellLines = {self.gvLeft:[], self.gvRight:[]}
        self.speciesInGrid=set()
        self.gridCount=0
        self.flip= {self.gvLeft:False, self.gvRight:False}
        self.rubberBanding = False
        self.mousebits=[None, None, None]
        self.lastItem=[]
        self.matchThresholdEdit.setText('30')
        self.frameBox.returnPressed.connect(self.getFrame)
        self.stereoOnlyCheckBox.setChecked(False)
        self.lockfile=None
        self.lockPath=None
        self.leftPB=None
        self.rightPB=None
        self.camtrawlMetadataFlag=False
        self.videoMode=False
        self.videoSources={}
        
        
        cnt=0
        for btn in self.spcButtons:
            btn.setCheckable(True)
            btn.setAutoExclusive(False)
            btn.pressed.connect(self.btnPress)
            btn.released.connect(self.btnRelease)
            cnt+=1
        self.pressTime=QElapsedTimer()
        self.pressTime.start()
        
        self.recomputeBtn.triggered.connect(self.recompute3D)
        self.recordBtn.triggered.connect(self.toggleRecord)
        self.measureBtn.triggered.connect(self.toggleMeasure)
        self.trainBtn.triggered.connect(self.toggleTraining)
        self.copyBtn.triggered.connect(self.copyImg)
        self.playBtn.clicked.connect(self.play)
        self.linkBtn.triggered.connect(self.toggleLink)
        self.delLinkBtn.triggered.connect(self.deleteLink)
        self.targetCommentBtn.triggered.connect(self.getTargetComment)
        self.frameCommentBtn.triggered.connect(self.getFrameComment)
        self.clearGridBtn.triggered.connect(self.clearGridData)
        self.editSpeciesBtn.triggered.connect(self.editSpecies)
        self.actionMatchThreshold.triggered.connect(self.setMatchThreshold)
        self.actionAbout.triggered.connect(self.showAbout)
        self.lastFrameBtn.clicked.connect(self.goToLastFrame)
        # the navigation buttons do what the arrow keys do
        self.firstBtn.clicked.connect(lambda: self.goToIndex(self.imageSlider.minimum()))
        self.prevSampleBtn.clicked.connect(lambda: self.stepFrame(-1, False))
        self.prevFrameBtn.clicked.connect(lambda: self.stepFrame(-1, True))
        self.nextFrameBtn.clicked.connect(lambda: self.stepFrame(1, True))
        self.nextSampleBtn.clicked.connect(lambda: self.stepFrame(1, False))
        self.lastBtn.clicked.connect(lambda: self.goToIndex(self.imageSlider.maximum()))
        
        # docking widgets
        # the docks can be closed: the View menu opens them again (its entries are disabled for docks that can't be closed)
        dockFeatures=QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable
        self.metadataDockWidget.setFeatures(dockFeatures)
        self.metadataDockWidget.hide()
        self.speciesDockWidget.setFeatures(dockFeatures)
        self.speciesDockWidget.hide()
        # species buttons next to the left image, Measurements panel next to the right one
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.speciesDockWidget)
        self.measurementsDock=measurementsdock.MeasurementsDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.measurementsDock)
        self.measurementsDock.setFeatures(dockFeatures)
        self.measurementsDock.goToTarget.connect(self.showMeasurement)
        # the ticks of the timeline follow the measurements
        self.measurementsDock.refreshed.connect(self.updateTimelineMarks)
        self.measurementsDock.hide()
        # the species buttons keep their size at the top of their tab: the ones without a species are hidden (setupSpcBtns)
        self.verticalLayout_3.addStretch(1)
        self.verticalLayout_7.addStretch(1)
        self.showSpeciesButtons(0)
        # View menu: show or hide the docks
        self.menuView.addSeparator()
        for dock in [self.speciesDockWidget, self.metadataDockWidget, self.measurementsDock]:
            self.menuView.addAction(dock.toggleViewAction())

        for action in [self.labelCheck, self.showDataCheck, self.closeupCheck]:
            action.toggled.connect(self.checkBoxAction)
        self.metadataCheckBox.stateChanged.connect(self.checkBoxAction)

        self.metadataStickyBox.stateChanged.connect(self.clearMetadataSelections)
        # camera view: Mono and Stereo are an exclusive pair of actions
        self.stereoRadio.setChecked(True)# default state - remeber?
        self.monoRadio.triggered.connect(self.cameraViewAction)
        self.stereoRadio.triggered.connect(self.cameraViewAction)
        # the guided fish marking follows these buttons
        for btn in [self.recordBtn, self.measureBtn, self.trainBtn, self.stereoRadio]:
            btn.toggled.connect(self.updateFishGuide)
        for btn in [self.recordBtn, self.stereoRadio]:
            btn.toggled.connect(self.updateEpipolar)
        # while recording nothing plays: the speed gives way to the sample step in a narrow navigation bar
        self.recordBtn.toggled.connect(self.fitNavBar)

        # grid cehckbox
        self.gridCheck.toggled.connect(self.gridBoxAction)
        
        #  connect the GUI signals and slots
        self.actionExit.triggered.connect(self.close)
        # the triggered signal passes its checked state: loadDeployment's argument is a folder
        self.actionLoad.triggered.connect(lambda: self.loadDeployment())
        self.actionProfiles.triggered.connect(self.setupProfiles)
        self.actionGUI_settings.triggered.connect(self.getGuiSettings)
        self.actionGrid_setup.triggered.connect(self.getGridSetup)
        self.actionSet_Active_Profiles.triggered.connect(self.setActiveProfiles)
        self.actionImport_Export_Profiles.triggered.connect(self.importExportProfiles)
        self.actionCreate_New_Project.triggered.connect(self.createNewProject)
        self.actionviewApplicationDB.triggered.connect(self.viewApplicationDB)
        self.actionedit_DB_tables.triggered.connect(self.directEditDBTables)
        self.playSpeedSlider.valueChanged.connect(self.speedSet)
        # the fps box and the slider follow each other
        self.playSpeedSlider.valueChanged.connect(self.playSpeedBox.setValue)
        self.playSpeedBox.valueChanged.connect(self.playSpeedSlider.setValue)
        self.imageSlider.valueChanged.connect( self.__changeImage)
        

        self.adjLeftBtn.clicked.connect(self.showAdjustmentsDialog)
        self.adjRightBtn.clicked.connect(self.showAdjustmentsDialog)

        for obj in [self.gvLeft, self.gvRight]:
            #signals
            obj.mousePress.connect(self.imageClick)
            obj.mouseRelease.connect(self.imageUnClick)
            obj.mouseWheel.connect(self.myWheelEvent)
            obj.mouseMove.connect(self.mouseInWidget)
            obj.keyPress.connect(self.__keyPressEvent)
            obj.keyRelease.connect(self.__keyReleaseEvent)
            # settings
            obj.setSelectionRadius(8)
            obj.autoWheelZoom=False
            obj.doSelections=False
            obj.selectAddKey=None
            #obj.panKey = None
            obj.rubberBandKey=None
            obj.image.keepEnhanced=True
            # no scroll bars: Alt+drag pans a zoomed image and zooming centres on the mark, so the empty tracks only take room
            obj.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            obj.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # the welcome page opens a deployment, from its button or from the list of the last ones
        self.welcomePage.openRequested.connect(self.actionLoad.trigger)
        self.welcomePage.recentRequested.connect(self.loadDeployment)

        #  restore the application state
        self.appSettings = QSettings('afsc.noaa.gov', 'Sebastes')
        # View > Epipolar Hints is remembered
        self.epipolarCheck.setChecked(strtobool(self.appSettings.value('epipolarhints', 'true')))
        self.epipolarCheck.toggled.connect(self.epipolarToggled)
        #  The window geometry and the places of the docks are saved when SEBASTES closes (closeEvent), together with
        #  LAYOUT_VERSION: a layout saved by a version of the window that is laid out differently is ignored.
        self.layoutRestored=False
        try:
            savedVersion=int(self.appSettings.value('layoutVersion', 0))
        except (TypeError, ValueError):
            savedVersion=0
        geometry=self.appSettings.value('geometry') if savedVersion==LAYOUT_VERSION else None
        if geometry is None or not self.restoreGeometry(geometry):
            position = self.appSettings.value('winposition', QPoint(10,10))
            size = self.appSettings.value('winsize', QSize(940,646))
            self.move(position)
            self.resize(size)
        #  The monitor the window was on may be gone, or the screen smaller: keep the window on a screen.
        self.keepOnScreen()
        state=self.appSettings.value('windowState') if savedVersion==LAYOUT_VERSION else None
        if state is not None:
            self.layoutRestored=self.restoreState(state, LAYOUT_VERSION)
        # the docks open when they are needed (a deployment is loaded, Record is pressed) and the toolbar can't be closed
        for dock in [self.speciesDockWidget, self.metadataDockWidget, self.measurementsDock]:
            dock.hide()
        self.mainToolBar.show()

        self.__dataDir = self.appSettings.value('self.dataPath', QDir.home().path())
        self.__copyImageDir = self.appSettings.value('copyimagedir', QDir.home().path())
        try:
            sample_rate=int(self.appSettings.value('samplerate', 10))
            sample_rate=str(sample_rate)
        except:
            sample_rate='1'
        self.sampleRateEdit.setText(sample_rate)
        self.closeupWinSize= int(self.appSettings.value('closeupwinsize', '50'))
        # other gui settings
        self.guiSettings={}
        self.guiSettings.update({'MeasureLineWidth':int(self.appSettings.value('MeasureLineWidth', 1))})
        self.guiSettings.update({'MeasureLineTailLength':int(self.appSettings.value('MeasureLineTailLength', 40))})
        self.guiSettings.update({'TargetLineColor':self.rgbStr2Lists(self.appSettings.value('TargetLineColor', '255,255,0'))})
        self.guiSettings.update({'SceneColor':self.rgbStr2Lists(self.appSettings.value('SceneColor', '255,0,0'))})
        self.guiSettings.update({'BoxLineThickness':int(self.appSettings.value('BoxLineThickness', 1))})
        self.guiSettings.update({'LabelTextSize':int(self.appSettings.value('LabelTextSize', 12))})
        self.guiSettings.update({'LabelSpeciesParam':int(self.appSettings.value('LabelSpeciesParam', 0))})
        self.guiSettings.update({'ShowClassOnLabel':self.appSettings.value('ShowClassOnLabel', 'false')})
        self.guiSettings.update({'DefaultMetadataSelection':self.appSettings.value('DefaultMetadataSelection','clear')})
        self.guiSettings.update({'RetainSpeciesSelection':self.appSettings.value('RetainSpeciesSelection','clear')})
        self.guiSettings.update({'PlaybackSpeedAdjust':self.appSettings.value('PlaybackSpeedAdjust',1.)})
        self.gridSetup={}
        self.gridSetup.update({'GridLineThickness':int(self.appSettings.value('GridLineThickness', 1))})
        self.gridSetup.update({'MeasureLineTailLength':int(self.appSettings.value('MeasureLineTailLength', 40))})
        self.gridSetup.update({'GridLineColor':self.rgbStr2Lists(self.appSettings.value('GridLineColor', '255,255,0'))})
        self.gridSetup.update({'CellLineColor':self.rgbStr2Lists(self.appSettings.value('CellLineColor', '255,0,0'))})
        self.gridSetup.update({'RandomizeCell':strtobool(self.appSettings.value('RandomizeCell', 'True'))})
        self.gridSetup.update({'PersistentGrid':strtobool(self.appSettings.value('PersistentGrid', 'False'))})
        self.gridSetup.update({'CellBoundary':strtobool(self.appSettings.value('CellBoundary', 'False'))})
        self.gridSetup.update({'GridSize':self.appSettings.value('GridSize', '2x2')})
        self.gridSetup.update({'GridLineStyle':self.appSettings.value('GridLineStyle','_')})
        
        #reoccuring dialogs
        
        self.stereoComp=pyStereoComp.pyStereoComp()
        self.closeup=closeupdlg.CloseupDlg()
        self.closeup.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.closeup.closeWindowEvent.connect(self.uncheckCloseupWindowBox)
        position = self.appSettings.value('zoomwinposition', QPoint(10,10))
        self.spcSelDlg=speciesgroupdlg.SpeciesGroupDlg(self)
        


        # first run: create the db folder files from the templates in schema/
        self.createMissingDBFiles()
        # open and load up prfile db
        if not QFile('../db/Application.db').exists():
            QMessageBox.warning(self, "ERROR", 'The "Application.db" file is not in its expected location (SEBASTES/db folder).  Something is not right with the file setup.')
        else:
            self.appDB = dbConnection.dbConnection('../db/Application.db', '', '', label='appDB', driver="QSQLITE")
            try:
                self.appDB.dbOpen()
            except:
                self.showError()
        # do some stuff to gv viewer
        self.gvLeft.disableContextMenu()
        self.gvRight.disableContextMenu()
        # disable buttons at start
        for widget in self.recordEnableWidgets:
            widget.setEnabled(False)
            self.recordBtn.setEnabled(False)
            
        # setup measurement box
        self.measurementBox.addItems(['length', 'width', 'chela_width'])
        self.measurementBox.setCurrentIndex(0)
        #  start a timer event to load the help image
        self.__helpTimer = QTimer(self)
        self.__helpTimer.setSingleShot(True)
        self.__helpTimer.start(500)
        self.__helpTimer.timeout.connect(self.showHelpImage)

        self.playTimer = QTimer(self)
        self.playTimer.timeout.connect(self.moveSlider)
        self.playClock=QElapsedTimer()
        self.playLastIndex=None
        self.speedSet()

        # the icons and the style sheets of the Record and Play buttons follow the light / dark theme
        theme.notifier.changed.connect(self.refreshTheme)
        self.refreshTheme()
        self.updateDeploymentLabel()
        self.updateMeasureWidgets()
        # the second row of the navigation bar gives up controls when the window is narrow: see fitNavBar
        self.navBar.installEventFilter(self)
        self.showWelcome()

    ######################0. WINDOW LAYOUT################################

    def keepOnScreen(self):
        '''
        keepOnScreen moves and shrinks the window so that it is inside the screen it is on. Valid positions on secondary
        monitors, including negative coordinates, are kept. If that monitor was disconnected, the primary screen is used.
        '''
        if self.isMaximized() or self.isFullScreen():
            return
        position = self.pos()
        size = self.size()
        screenObj = QGuiApplication.screenAt(position) or QGuiApplication.primaryScreen()
        screenGeometry = screenObj.availableGeometry()
        #  Leave room for the window frame and title bar, and exclude the taskbar.
        size.setWidth(max(1, min(size.width(), screenGeometry.width() - 50)))
        size.setHeight(max(1, min(size.height(), screenGeometry.height() - 50)))
        position.setX(max(screenGeometry.left(), min(position.x(),
            screenGeometry.right() - size.width() - 49)))
        position.setY(max(screenGeometry.top(), min(position.y(),
            screenGeometry.bottom() - size.height() - 49)))
        #  now move and resize the window
        self.move(position)
        self.resize(size)

    def setupToolBar(self):
        '''
        setupToolBar builds the main toolbar. Most buttons are tool buttons on the actions of the menus, so a menu item
        and its button share text, icon, enabled and checked state. A button is hidden through the toolbar action that
        addWidget returns (self.toolbarAction), not through the menu action: the menu item stays, disabled.
        '''
        bar=QToolBar('Main toolbar', self)
        bar.setObjectName('mainToolBar')
        bar.setMovable(False)
        bar.setFloatable(False)
        bar.setIconSize(QSize(20, 20))
        bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, bar)
        self.mainToolBar=bar
        self.toolbarAction={}

        def toolButton(action, parent):
            button=QToolButton(parent)
            button.setDefaultAction(action)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setIconSize(bar.iconSize())
            button.setAutoRaise(True)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            return button

        def addTool(action):
            self.toolbarAction[action]=bar.addWidget(toolButton(action, bar))

        bar.addAction(self.actionLoad)
        bar.addSeparator()
        # Record has an action of its own in the toolbar, kept in step with the menu action: while recording the
        # button is filled red and needs a white icon, which would be invisible in the menu
        self.recordToolAction=QAction(self)
        self.recordToolAction.setCheckable(True)
        self.recordToolAction.setText(self.recordBtn.text())
        self.recordToolAction.setToolTip(self.recordBtn.toolTip())
        self.recordBtn.toggled.connect(self.recordToolAction.setChecked)
        self.recordBtn.changed.connect(lambda: self.recordToolAction.setEnabled(self.recordBtn.isEnabled()))
        self.recordToolAction.triggered.connect(self.recordBtn.trigger)
        bar.addAction(self.recordToolAction)
        bar.addSeparator()
        # Mono and Stereo are one exclusive choice, drawn as two joined buttons
        modeGroup=QActionGroup(self)
        modeGroup.addAction(self.monoRadio)
        modeGroup.addAction(self.stereoRadio)
        modeBox=QWidget(bar)
        row=QHBoxLayout(modeBox)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        for action, position in [(self.monoRadio, 'first'), (self.stereoRadio, 'last')]:
            button=toolButton(action, modeBox)
            button.setProperty('segment', position)
            row.addWidget(button)
        bar.addWidget(modeBox)
        bar.addSeparator()
        addTool(self.measureBtn)
        self.measurementBox=QComboBox(bar)
        self.measurementBox.setToolTip('Measurement type')
        self.measurementBox.setMinimumWidth(110)
        self.toolbarAction[self.measurementBox]=bar.addWidget(self.measurementBox)
        bar.addSeparator()
        addTool(self.linkBtn)
        addTool(self.delLinkBtn)
        addTool(self.editSpeciesBtn)
        # the selected target: "Target: 3"
        self.targetBox=QWidget(bar)
        self.targetBox.setToolTip('The selected target')
        row=QHBoxLayout(self.targetBox)
        row.setContentsMargins(8, 0, 8, 0)
        row.setSpacing(4)
        self.label_4=QLabel('Target:', self.targetBox)
        self.targetLinkLabel=QLabel('', self.targetBox)
        self.targetLinkLabel.setMinimumWidth(24)
        boldFont=self.targetLinkLabel.font()
        boldFont.setBold(True)
        self.targetLinkLabel.setFont(boldFont)
        row.addWidget(self.label_4)
        row.addWidget(self.targetLinkLabel)
        self.toolbarAction[self.targetBox]=bar.addWidget(self.targetBox)
        bar.addSeparator()
        bar.addAction(self.targetCommentBtn)
        bar.addAction(self.frameCommentBtn)
        bar.addSeparator()
        bar.addAction(self.labelCheck)
        bar.addAction(self.closeupCheck)
        bar.addAction(self.showDataCheck)

    def setupStatusBar(self):
        '''
        setupStatusBar puts the mode, the annotator and the deployment at the right of the status bar. Messages
        (the guided fish marking uses them) stay at the left. A measurement quality chip (QLabel#measureChip) goes
        in front of the mode label: self.statusBar.insertPermanentWidget(0, chip).
        '''
        bar=self.statusBar
        self.modeLabel=QLabel()
        self.modeLabel.setContentsMargins(10, 0, 10, 0)
        # the annotator's name is read back by writeFrameData, so it has a label of its own
        self.annotatorBox=QWidget()
        row=QHBoxLayout(self.annotatorBox)
        row.setContentsMargins(10, 0, 10, 0)
        row.setSpacing(4)
        row.addWidget(QLabel('Annotator:'))
        self.annotatorLabel=QLabel()
        self.annotatorLabel.setObjectName('annotatorLabel')
        self.annotatorLabel.setStyleSheet('color: palette(window-text);')
        row.addWidget(self.annotatorLabel)
        self.deploymentBox=QLabel()
        self.deploymentBox.setObjectName('deploymentBox')
        self.deploymentBox.setContentsMargins(10, 0, 10, 0)
        self.deploymentBox.setStyleSheet('color: palette(window-text);')
        for widget in [self.modeLabel, self.annotatorBox, self.deploymentBox]:
            bar.addPermanentWidget(widget)
        self.recordBtn.toggled.connect(self.updateStatusMode)
        self.trainBtn.toggled.connect(self.updateStatusMode)

    def updateStatusMode(self, *args):
        '''
        updateStatusMode shows in the status bar whether we are viewing or recording.
        '''
        recording=self.recordBtn.isChecked()
        if recording:
            text='\u25cf Recording'
            if self.trainBtn.isChecked():
                text+=' (training set)'
            self.modeLabel.setStyleSheet('color: '+theme.colors()['record']+'; font-weight: 600;')
        else:
            text='Viewing'
            self.modeLabel.setStyleSheet('')
        self.modeLabel.setText(text)
        self.annotatorBox.setVisible(recording)

    def updateDeploymentLabel(self):
        '''
        updateDeploymentLabel shows the project and deployment in the window title and in the status bar.
        '''
        if self.deployment:
            name=self.activeProject+': '+self.deployment
            self.deploymentBox.setText(name)
            self.deploymentBox.setToolTip(getattr(self, 'deploymentPath', ''))
            self.setWindowTitle('SEBASTES \u2014 '+name)
        else:
            self.deploymentBox.setText('No deployment loaded')
            self.deploymentBox.setToolTip('')
            self.setWindowTitle('SEBASTES')

    def refreshTheme(self):
        '''
        refreshTheme sets the icons and the style sheets of the Record and Play buttons for the light or dark
        theme. It runs at start-up and whenever the system theme changes.
        '''
        icon=theme.icon
        for action, name in [(self.actionLoad, 'open-folder'), (self.copyBtn, 'copy-images'), (self.labelCheck, 'labels'),
                (self.showDataCheck, 'data-table'), (self.closeupCheck, 'closeup'), (self.gridCheck, 'grid'),
                (self.measureBtn, 'measure'), (self.linkBtn, 'link'), (self.delLinkBtn, 'unlink'), (self.editSpeciesBtn, 'species'),
                (self.targetCommentBtn, 'target-comment'), (self.frameCommentBtn, 'frame-comment'), (self.computeMatchBox, 'auto-match'),
                (self.recomputeBtn, 'recompute'), (self.trainBtn, 'training-set'), (self.clearGridBtn, 'delete'),
                (self.monoRadio, 'mono'), (self.stereoRadio, 'stereo'), (self.epipolarCheck, 'epipolar'),
                (self.speciesDockWidget.toggleViewAction(), 'species'), (self.metadataDockWidget.toggleViewAction(), 'metadata'),
                (self.measurementsDock.toggleViewAction(), 'measurements')]:
            action.setIcon(icon(name))
        self.recordBtn.setIcon(icon('record', color='record', onColor='record'))
        self.recordToolAction.setIcon(icon('record', color='record', onColor='#ffffff'))
        for button, name in [(self.firstBtn, 'first'), (self.prevSampleBtn, 'prev-sample'), (self.prevFrameBtn, 'prev-frame'),
                (self.nextFrameBtn, 'next-frame'), (self.nextSampleBtn, 'next-sample'), (self.lastBtn, 'last'),
                (self.lastFrameBtn, 'go-to-last'), (self.adjLeftBtn, 'adjust-image'), (self.adjRightBtn, 'adjust-image')]:
            button.setIcon(icon(name))
        self.mainToolBar.widgetForAction(self.recordToolAction).setStyleSheet(theme.recordButtonStyle())
        self.playBtn.setStyleSheet(theme.playButtonStyle())
        colors=theme.colors()
        self.imageSlider.setMarkColors(colors['warning'], colors['text'], colors['surface'])
        # the epipolar curves are in the accent colour
        self.updateEpipolar()
        self.updatePlayButton()
        self.updateStatusMode()

    def showTools(self, tools, visible):
        '''
        showTools shows or hides the toolbar buttons of actions and widgets that were put in the toolbar. An action
        hidden here keeps its menu item.
        '''
        for tool in tools:
            self.toolbarAction[tool].setVisible(visible)
        self.updateToolbarSeparators()

    def updateToolbarSeparators(self):
        '''
        updateToolbarSeparators shows a separator only between two groups of visible buttons.
        '''
        haveButton=False
        pending=None
        for action in self.mainToolBar.actions():
            if action.isSeparator():
                action.setVisible(False)
                if haveButton:
                    pending=action
            elif action.isVisible():
                if pending is not None:
                    pending.setVisible(True)
                    pending=None
                haveButton=True

    def updateMeasureWidgets(self):
        # Measure Target and its measurement list are shown only while Measure Target is enabled
        self.showTools(self.measureWidgets, self.measureBtn.isEnabled())

    def setNavEnabled(self, enabled):
        for button in self.navWidgets:
            button.setEnabled(enabled)

    def eventFilter(self, obj, event):
        # the sample and speed controls give way when the navigation bar gets narrow
        if obj is self.navBar and event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.fitNavBar()
        return QMainWindow.eventFilter(self, obj, event)

    def fitNavBar(self):
        '''
        fitNavBar makes the second row of the navigation bar fit its width. When it is too narrow it gives up controls,
        the least needed first, until the rest fits: the speed slider (the speed stays in its box), the time of the
        frame, the offset of the sample step and then the sample step, or the speed while recording (nothing plays
        then, and the sample step is what the arrow keys use). The controls come back when the bar is wide enough
        again. Their minimum width is 1 in the layout, so the window can be made narrow.
        '''
        margins=self.navLayout.contentsMargins()
        room=self.navBar.width()-margins.left()-margins.right()
        row=[self.firstBtn, self.prevSampleBtn, self.prevFrameBtn, self.playBtn, self.nextFrameBtn, self.nextSampleBtn, self.lastBtn,
             self.lastFrameBtn, self.frameInfo, self.sampleBox, self.speedBox]
        for stage in range(5):
            self.playSpeedSlider.setVisible(stage<1)
            self.timeLabel.setVisible(stage<2 and self.videoMode)
            self.rateOffsetEdit.setVisible(stage<3)
            self.offsetLabel.setText('frames, offset' if stage<3 else 'frames')
            recording=self.recordBtn.isChecked()
            self.sampleBox.setVisible(stage<4 or recording)
            self.speedBox.setVisible(stage<4 or not recording)
            shown=[widget for widget in row if not widget.isHidden()]
            # the widgets and the two stretches that centre the frame number, one spacing between neighbours
            needed=sum(widget.sizeHint().width() for widget in shown)+self.navRow.spacing()*(len(shown)+1)+4
            if needed<=room:
                break

    def updateTimeLabel(self, frame=None):
        '''
        updateTimeLabel shows the time of the frame in the video: hours, minutes, seconds and hundredths of a second.
        Still images have no time.
        '''
        video=self.videoSources.get(getattr(self, 'LPath', None)) if self.videoMode else None
        if video is None or not video.fps or frame is None or self.noLoad:
            self.timeLabel.setText('')
            return
        hundredths=int(frame*100/video.fps)
        seconds, hundredths=divmod(hundredths, 100)
        minutes, seconds=divmod(seconds, 60)
        hours, minutes=divmod(minutes, 60)
        self.timeLabel.setText('%02d:%02d:%02d.%02d' % (hours, minutes, seconds, hundredths))

    def updateTimelineMarks(self):
        '''
        updateTimelineMarks puts the ticks on the timeline: a tall one at each frame with a measurement, a short one at
        the frames that have targets only. It only reads the data database.
        '''
        measured=[]
        counted=[]
        if self.dataDB is not None and self.deployment is not None and not self.noLoad:
            frames=self.leftImageFrames
            for table, marks in [('lines', measured), ('targets', counted)]:
                query=self.dataDB.dbQuery("SELECT DISTINCT frame_number FROM "+table+" WHERE deployment_id='"+sqlQuote(self.deployment)+"'")
                for frame, in query:
                    # the frames are sorted: the position of a frame number is its slider position
                    index=bisect.bisect_left(frames, int(frame)) if frame is not None else len(frames)
                    if index<len(frames) and frames[index]==int(frame):
                        marks.append(index)
        self.imageSlider.setMarks(measured, counted)

    def showWelcome(self):
        '''
        showWelcome shows the welcome page in place of the images and the playback bar. It is what SEBASTES looks like
        until a deployment is loaded.
        '''
        self.welcomePage.setRecent(self.recentDeployments())
        self.imageStack.setCurrentWidget(self.welcomePage)
        self.navBar.hide()

    def showViews(self):
        '''
        showViews shows the two images and the playback bar, in the size they have to fill, in place of the welcome page.
        '''
        self.imageStack.setCurrentWidget(self.viewPage)
        self.navBar.show()
        self.centralWidget().layout().activate()

    def recentDeployments(self):
        '''
        recentDeployments returns the folders of the deployments opened last, the newest first. Folders that are not
        there any more are left out (they stay in the settings: a disk that is not connected now may be next time).
        '''
        return [folder for folder in self.storedRecentDeployments() if os.path.isdir(folder)]

    def storedRecentDeployments(self):
        try:
            folders=json.loads(self.appSettings.value('recentdeployments', '[]'))
        except (TypeError, ValueError):
            return []
        return [folder for folder in folders if isinstance(folder, str)] if isinstance(folders, list) else []

    def addRecentDeployment(self, folder):
        '''
        addRecentDeployment puts a deployment that was opened first in the list of the last ones (at most RECENT_DEPLOYMENTS).
        '''
        same=lambda a, b: os.path.normcase(os.path.normpath(a))==os.path.normcase(os.path.normpath(b))
        folders=[folder]+[other for other in self.storedRecentDeployments() if not same(other, folder)]
        self.appSettings.setValue('recentdeployments', json.dumps(folders[:RECENT_DEPLOYMENTS]))

    def updatePlayButton(self):
        # the button says what it does next
        if self.playBtn.isChecked():
            self.playBtn.setText('Pause')
            self.playBtn.setIcon(theme.icon('pause'))
        else:
            self.playBtn.setText('Play')
            self.playBtn.setIcon(theme.icon('play', color='accentText'))

    def setMatchThreshold(self):
        # the threshold is kept in a line edit that is never shown: the Auto Match code reads its text
        try:
            current=float(self.matchThresholdEdit.text())
        except ValueError:
            current=30.0
        value, ok=QInputDialog.getDouble(self, 'Match Threshold', 'Largest error (px) accepted for an Auto Match:', current, 0.1, 1000, 1)
        if ok:
            self.matchThresholdEdit.setText('%g' % value)

    def showAbout(self):
        version=''
        try:
            with open(os.path.join(self.baseDir, 'version.txt')) as f:
                match=re.search(r'filevers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)', f.read())
            if match:
                parts=list(match.groups())
                while len(parts)>2 and parts[-1]=='0':
                    parts.pop()
                version='Version '+'.'.join(parts)+'<br>'
        except OSError:
            pass
        QMessageBox.about(self, 'About SEBASTES', '<h3>SEBASTES</h3>'+version+
            '<p>Underwater stereo camera analysis: view and annotate left and right images or videos, mark and measure fish, '
            'assign species and frame metadata, and get 3D range and length by stereo triangulation.</p>'
            '<p>Developed by NOAA Fisheries employees Kresimir Williams and Rick Towler. Not an official government product.</p>')



    ######################1b. HINTS, MEASUREMENT CHIP, SHORTCUTS################################

    def epipolarEnabled(self):
        '''
        epipolarEnabled says whether the epipolar hints can be drawn: they are on in the View menu, a deployment is
        recording in stereo and it has a calibration. (stereoAvailable is not used: it opens a message box.)
        '''
        return (self.epipolarCheck.isChecked() and not self.noLoad and self.recordBtn.isChecked() and self.stereoRadio.isChecked()
                and getattr(self, 'mode', None)=='stereo' and bool(self.stereoComp.calData))

    def epipolarToggled(self, checked):
        self.appSettings.setValue('epipolarhints', 'true' if checked else 'false')
        self.updateEpipolar()

    def pendingStereoPoints(self):
        '''
        pendingStereoPoints returns (the image the points were clicked in, the points) for a stereo pair that is
        waiting for the other image: the first point of a target, the tail of a fish in the left image, or the ends
        of the line drawn in one image with Measure Target. None when no pair is half done.
        '''
        if len(self.pairPoints)==1:
            imageObj, x, y=self.pairPoints[0]
            return imageObj, [QPointF(x, y)]
        if self.fishGuideActive() and self.fishStep==3 and self.gvLeft in self.fishLines:
            # the line runs from the head to the tail
            return self.gvLeft, [self.fishLines[self.gvLeft].p2()]
        if self.measureBtn.isChecked():
            drawn=[imageObj for imageObj in [self.gvLeft, self.gvRight] if self.activeLine[imageObj] is not None]
            if len(drawn)==1:
                line=self.activeLine[drawn[0]].getLine()
                return drawn[0], [line.p1(), line.p2()]
        return None

    def clearEpipolar(self):
        '''
        clearEpipolar removes the epipolar curves from the images. The viewers drop them as well when the scene is
        cleared (removeAllItems) or rebuilt, so an item can be gone already: that is not an error.
        '''
        for imageObj, items in self.epipolarItems.items():
            for item in items:
                try:
                    imageObj.removeItem(item)
                except RuntimeError:
                    pass
            items[:]=[]

    def updateEpipolar(self, *args):
        '''
        updateEpipolar draws, in the image that waits for the second point of a stereo pair, the epipolar curve of the
        first point; with no pair half done it removes the curves. It is called after every click, so the curve
        appears with the first point and goes with the pair.
        '''
        self.clearEpipolar()
        if not self.epipolarEnabled():
            return
        try:
            pending=self.pendingStereoPoints()
            if pending is not None:
                self.showEpipolar(*pending)
        except Exception:
            # the hints are a help: never let them stop the marking
            traceback.print_exc()

    def showEpipolar(self, imageObj, points):
        '''
        showEpipolar draws in the other image the curve on which the match of each point (clicked in imageObj) must lie.
        '''
        otherObj=self.gvRight if imageObj is self.gvLeft else self.gvLeft
        size=(otherObj.imgPixmap.width(), otherObj.imgPixmap.height())
        color=QColor(theme.colors()['accentSoft'])
        for point in points:
            curve=epipolar.epipolarCurve(self.stereoComp.calData, (point.x(), point.y()), 'L' if imageObj is self.gvLeft else 'R',
                                         size if size[0]>0 else None)
            item=otherObj.addCurve(curve, color=[color.red(), color.green(), color.blue()], thickness=1.5, linestyle='-')
            if item is not None:
                self.epipolarItems[otherObj].append(item)
        otherObj.viewport().update()

    ######################1. SETUP FUNCTIONS################################
    
    def cameraViewAction(self):
        # in stereo, Measure Target is usable only while recording and not making bounding boxes
        measureOn=self.recordBtn.isChecked() and not self.trainBtn.isChecked()
        if self.stereoRadio.isChecked():
            # restore stereo state
            self.frameLeft.show()
            self.frameRight.show()
            self.measureBtn.setEnabled(measureOn)
            self.measurementBox.setEnabled(measureOn)
            self.activeGV='Both'
        else: # we are going mono
            if not self.defaultMonoCamera:
                from dialogs import camviewseldlg 
                dlg=camviewseldlg.CamViewSelDlg(self)
                if dlg.exec():
                    if dlg.leftRadio.isChecked():
                        self.frameRight.hide()
                        self.activeGV='Left'
                    else:
                        self.frameLeft.hide()
                        self.activeGV='Right'
                    self.measureBtn.setEnabled(False)
                    self.measurementBox.setEnabled(False)
                else:
                    # restore stereo state
                    self.frameLeft.show()
                    self.frameRight.show()
                    self.measureBtn.setEnabled(measureOn)
                    self.measurementBox.setEnabled(measureOn)
                    self.stereoRadio.setChecked(True)
    
    def getGuiSettings(self):
        dlg=guisettingdlg.GuiSettingDlg(self)
        if dlg.exec():
            self.guiSettings=dlg.guiSettings
            if self.recordBtn.isChecked():
                self.__changeImage()
                
    def getGridSetup(self):
        from dialogs import gridsetupdlg
        dlg=gridsetupdlg.GridSetupDlg(self)
        if dlg.exec():
            self.gridSetup=dlg.gridSetup
            if self.recordBtn.isChecked():
                self.__changeImage()
                
    def setupProfiles(self):
        dlg=profilesetupdlg.ProfileSetupDlg(self)
        if self.activeProfile==None:
            dlg.reloadBtn.hide()
        dlg.exec()
        if dlg.reloadFlag:
            self.loadProfile()
                
    def setActiveProfiles(self):
        
        from dialogs import setactiveprofiledlg
        dlg=setactiveprofiledlg.SetActiveProfilesDlg(self)
        dlg.exec()
        
    def importExportProfiles(self):
        
        from dialogs import selexportcompdlg
        dlg=selexportcompdlg.SelExportCompDlg(self)
        dlg.exec()
    
    def createNewProject(self):
        from dialogs import newprojectdlg
        dlg=newprojectdlg.NewProjectDlg(self)
        if dlg.exec():
            pass
    
    def setupSpcBtns(self):
            # species
            self.speciesList=[]
            self.speciesDescList=[]
            self.spcColors=[]
            query=self.appDB.dbQuery("SELECT species_group, button_color, description FROM SPECIES_SETUP WHERE species_collection='"+sqlQuote(self.speciesCollection)+"' ORDER BY sort_order NULLS LAST, species_group")
            cnt=0
            for spc, color,  desc in query:
                self.speciesList.append(spc)
                self.speciesDescList.append(desc)
                val=color.split(',')
                try:
                    self.spcColors.append([int(val[0]), int(val[1]), int(val[2])])
                except:
                    self.spcColors.append([255, 255, 0])
                    color=''
                # add names to buttons
                if cnt<len(self.spcButtons):
                    btn=self.spcButtons[cnt]
                    btn.setEnabled(True)
                    btn.setText(self.speciesList[cnt])
                    btn.setToolTip(self.speciesDescList[cnt])
                    if color=='':
                        rgb='255,255,0'
                    else:
                        rgb=color
                    bits=rgb.split(',')
                    total_bits=int(bits[0])+int(bits[1])+int(bits[2])
                    if total_bits<3*128:
                        txt_color="white"
                    else:
                        txt_color="black"
                    #btn.setStyleSheet("QPushButton { background-color: rgb("+rgb+")}")
                    # not selected: outline in the species color; selected: filled with it.
                    # rgb() must stay the first number in the style sheet: imageClick reads the mark color from it
                    btn.setStyleSheet(f"""
                    QPushButton {{
                        border-color: rgb({rgb});
                        border-style: solid;
                        border-width: 3px;
                        border-radius: 4px;
                        background-color: transparent;
                        padding: 8px 16px;
                        font-weight: normal;
                    }}
                    QPushButton:hover {{
                        background-color: rgba({rgb}, 70);
                    }}
                    QPushButton:checked {{
                        background-color: rgb({rgb});
                        color: {txt_color};
                        font-weight: bold;
                    }}
                """)
                cnt+=1
            self.showSpeciesButtons(min(cnt, len(self.spcButtons)))

    def showSpeciesButtons(self, count):
        '''
        showSpeciesButtons shows the first count species buttons and hides the others, which have no species. The second
        tab (buttons 16 to 30) and the tab bar are there only when the species need more than the first tab holds.
        '''
        for index, btn in enumerate(self.spcButtons):
            if index>=count:
                # a button that had a species before the profile or the species changed
                btn.setChecked(False)
                btn.setText('')
                btn.setToolTip('')
                btn.setStyleSheet('')
            btn.setVisible(index<count)
        firstTabSize=len(self.tab_1.findChildren(QPushButton))
        second=self.speciesTabWidget.indexOf(self.tab_2)
        self.speciesTabWidget.setTabVisible(second, count>firstTabSize)
        self.speciesTabWidget.tabBar().setVisible(count>firstTabSize)
        if count<=firstTabSize:
            self.speciesTabWidget.setCurrentIndex(self.speciesTabWidget.indexOf(self.tab_1))

    def loadProfile(self):
        try:
            # settings
            self.settings={}
            query=self.appDB.dbQuery("SELECT setting, value as val FROM PROFILE_SETTINGS WHERE profile='"+sqlQuote(self.activeProfile)+"'")
            for parameter, value in query:
                self.settings.update({parameter:value})

            self.setupSpcBtns()
            self.spcSelDlg.setList(self.speciesList)


            # populate metadata
            if self.settings['CollectMetadata'].lower()=='true' or self.settings['CollectMetadata'].lower()=='yes':
                self.metadataCheckBox.setChecked(True)
            else:
                self.metadataCheckBox.setChecked(False)
                
            if self.metadataCheckBox.isChecked():
                self.metadataDockWidget.setWindowTitle(self.metadataGroup)
                self.radioBtnList1=[]
                self.radioBtnDescriptionsList1=[]
                query=self.appDB.dbQuery("SELECT metadata_tag, metadata_type, description FROM FRAME_METADATA_SETUP WHERE metadata_group='"+sqlQuote(self.metadataGroup)+
                "' AND metadata_gui_element='ExclusiveRadioBox1' ORDER BY sort_order")
                value=None
                for value, Type,  desc in query:
                        self.radioBtnList1.append(value)
                        self.radioBtnDescriptionsList1.append(desc)
                if len(self.radioBtnList1)>0:
                    self.metadataTypesDict.update({'ExclusiveRadioBox1':Type})
                
                self.radioBtnList2=[]
                self.radioBtnDescriptionsList2=[]
                query=self.appDB.dbQuery("SELECT metadata_tag, metadata_type, description FROM FRAME_METADATA_SETUP WHERE metadata_group='"+sqlQuote(self.metadataGroup)+
                "' AND metadata_gui_element='ExclusiveRadioBox2' ORDER BY sort_order")
                for value, Type,  desc in query:
                        self.radioBtnList2.append(value)
                        self.radioBtnDescriptionsList2.append(desc)
                if len(self.radioBtnList2)>0:
                    self.metadataTypesDict.update({'ExclusiveRadioBox2':Type})
                    
                self.radioBtnList3=[]
                self.radioBtnDescriptionsList3=[]# this one is for horizontal single line radios
                query=self.appDB.dbQuery("SELECT metadata_tag, metadata_type, description FROM FRAME_METADATA_SETUP WHERE metadata_group='"+sqlQuote(self.metadataGroup)+
                "' AND metadata_gui_element='ExclusiveRadioBox3' ORDER BY sort_order")
                for value, Type,  desc in query:
                        self.radioBtnList3.append(value)
                        self.radioBtnDescriptionsList3.append(desc)
                if len(self.radioBtnList3)>0:
                    self.metadataTypesDict.update({'ExclusiveRadioBox3':Type})
                
                self.lineEditList=[]
                self.metadataTypeLabel2.setText('')
                query=self.appDB.dbQuery("SELECT metadata_tag, metadata_type FROM FRAME_METADATA_SETUP WHERE metadata_group='"+sqlQuote(self.metadataGroup)+
                "' AND metadata_gui_element='LineEdit' ORDER BY sort_order")
                for value, Type in query:
                        self.lineEditList.append(value)
                if len(self.lineEditList)>0:
                    self.metadataTypesDict.update({'LineEdit':Type})
                    self.metadataTypeLabel2.setText(Type)
                
                self.checkBoxList=[]
                self.metadataTypeLabel3.setText('')
                query=self.appDB.dbQuery("SELECT metadata_tag, metadata_type FROM FRAME_METADATA_SETUP WHERE metadata_group='"+sqlQuote(self.metadataGroup)+
                "' AND metadata_gui_element='CheckBox' ORDER BY sort_order")
                for value, Type in query:
                        self.checkBoxList.append(value)
                if len(self.checkBoxList)>0:
                    self.metadataTypesDict.update({'CheckBox':Type})
                    self.metadataTypeLabel3.setText(Type)
                
                if len(self.radioBtnList1)>0:# we have some of this type
                    self.exclusiveRadioBox1.show()
                    self.exclusiveRadioBox1.setTitle(self.metadataTypesDict['ExclusiveRadioBox1'])
                    for i in list(range(len(self.radioBtnTags1))):
                        if i<len(self.radioBtnList1):
                            self.radioBtnTags1[i].show()
                            self.radioBtnTags1[i].setText(self.radioBtnList1[i])
                            self.radioBtnTags1[i].setToolTip(self.radioBtnDescriptionsList1[i])
                        else:
                            self.radioBtnTags1[i].setText('')
                            self.radioBtnTags1[i].hide()
                else:
                    self.exclusiveRadioBox1.hide()
                    
                if len(self.radioBtnList2)>0:# we have some of this type
                    self.exclusiveRadioBox2.show()
                    self.exclusiveRadioBox2.setTitle(self.metadataTypesDict['ExclusiveRadioBox2'])
                    for i in list(range(len(self.radioBtnTags2))):
                        if i<len(self.radioBtnList2):
                            self.radioBtnTags2[i].show()
                            self.radioBtnTags2[i].setText(self.radioBtnList2[i])
                            self.radioBtnTags2[i].setToolTip(self.radioBtnDescriptionsList2[i])
                        else:
                            self.radioBtnTags2[i].setText('')
                            self.radioBtnTags2[i].hide()
                else:
                    self.exclusiveRadioBox2.hide()
                    
                if len(self.radioBtnList3)>0:# we have some of this type
                    self.exclusiveRadioBox3.show()
                    self.exclusiveRadioBox3.setTitle(self.metadataTypesDict['ExclusiveRadioBox3'])
                    for i in list(range(len(self.radioBtnTags3))):
                        if i<len(self.radioBtnList3):
                            self.radioBtnTags3[i].show()
                            self.radioBtnTags3[i].setText(self.radioBtnList3[i])
                            self.radioBtnTags3[i].setToolTip(self.radioBtnDescriptionsList3[i])
                        else:
                            self.radioBtnTags3[i].setText('')
                            self.radioBtnTags3[i].hide()
                else:
                    self.exclusiveRadioBox3.hide()
                # populate metadata Check boxes
                cnt=0
                for btn in self.metadataCheckBoxes:
                    if cnt<len(self.checkBoxList):
                        if self.checkBoxList[cnt]!='':
                            btn.setText(self.checkBoxList[cnt])
                        else:
                            btn.hide()
                    else:
                        btn.hide()
                    cnt+=1
                # populate coverage
                cnt=0
                for label in self.metadataLineEditLabels:
                    if cnt<len(self.lineEditList):
                        if self.lineEditList!='':
                            label.setText(self.lineEditList[cnt])
                        else:
                            label.hide()
                            self.metadataLineEdits[cnt].hide()
                    else:
                        label.hide()
                        self.metadataLineEdits[cnt].hide()
                    cnt+=1
                    if self.metadataGroup=='CamTrawl_metadata':
                        self.camtrawlMetadataFlag=True
                        import CamTrawlMetadata
                        self.metadata = CamTrawlMetadata.CamTrawlMetadata()
                        self.metadata.open(self.deploymentPath)
                        self.metadata.query()
                self.metadataStickyBox.setEnabled(True)
                if self.guiSettings['DefaultMetadataSelection']=='retain':
                    self.metadataStickyBox.setChecked(True)
                else:
                    self.metadataStickyBox.setChecked(False)
            if 'SubsampleMask' in self.settings:
                if self.settings['SubsampleMask'].lower()=='no' or self.settings['SubsampleMask'].lower()=='':
                    self.doMask=False
                else:
                    self.doMask=True
            else:
                self.doMask=False
                
            # this is fix form makng trawlable a radiobutton
            if self.metadataGroup in ['Habitat', 'Habitat_Coral']:
                if self.dataDB:
                    if self.dataDB.db.isOpen():
                        # look to see if there are any trawlability records under checkbox
                        query=self.dataDB.dbQuery("SELECT deployment_id, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value FROM FRAME_METADATA "+" WHERE deployment_id='"+
                        sqlQuote(self.deployment)+"' AND metadata_tag='Trawlable' and metadata_type='Check Box'")
                        for deployment_id, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value in query:
                            # insert net type of record
                            if metadata_value=='Checked':
                                self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project, deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value,annotator)"+
                                    " VALUES('"+sqlQuote(self.activeProject)+"', '"+sqlQuote(deployment_id)+"',"+frame_number+",'"+sqlQuote(metadata_group)+"','Yes','"+sqlQuote(self.metadataTypesDict['ExclusiveRadioBox3'])+
                                    "','Checked','"+sqlQuote(self.annotator)+"')")
                            else:
                                self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project, deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value,annotator)"+
                                    " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(deployment_id)+"',"+frame_number+",'"+sqlQuote(metadata_group)+"','No','"+sqlQuote(self.metadataTypesDict['ExclusiveRadioBox3'])+
                                    "','Checked','"+sqlQuote(self.annotator)+"')")
                            
                        # delete old style records
                        self.dataDB.dbExec("DELETE FROM FRAME_METADATA WHERE"+
                        " metadata_tag='Trawlable' and metadata_type='Check Box'  AND deployment_ID='"+sqlQuote(self.deployment)+"'")

            return True
        except:
            self.showError()
            return False


    def createMissingDBFiles(self):
        '''
        On a first run there is no SEBASTES/db folder: create an empty Application.db and
        copy the data db template from the schema folder. Existing files are left alone.
        '''
        schemaDir=self.baseDir+'/schema/'
        try:
            QDir().mkpath('../db')
            if not QFile('../db/Project.db.sql').exists():
                QFile.copy(schemaDir+'Project.db.sql', '../db/Project.db.sql')
            if not QFile('../db/Application.db').exists():
                with open(schemaDir+'Application.db.sql') as f:
                    script=f.read()
                conn=sqlite3.connect('../db/Application.db')
                conn.executescript(script)
                conn.close()
                QMessageBox.information(self, "NOTE", 'Created an empty "Application.db" in the SEBASTES/db folder.\n\n'+
                    'Before loading a deployment, use Settings > Profiles to create a species collection and a profile.')
        except:
            self.showError()

    def showError(self):
        t=traceback.format_exception(*sys.exc_info())
        txt=''
        for line in t:
            txt=txt+line+'\n'
        print(txt)
        QMessageBox.warning(self, "ERROR", txt)


    def userName(self):
        try:
            return getpass.getuser()
        except Exception:
            return 'unknown'

    def storedProfile(self, dbFile, deployment):
        '''
        storedProfile returns the profile saved with a deployment in its data database, or None.
        The file is only read, so the deployment that is open is not touched.
        '''
        if not os.path.exists(dbFile):
            return None
        try:
            conn=sqlite3.connect(pathlib.Path(dbFile).resolve().as_uri()+'?mode=ro', uri=True)
            try:
                row=conn.execute("SELECT profile FROM deployment WHERE deployment_ID=?", (deployment,)).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            return None
        if row and row[0]:
            return row[0]
        return None

    def createLock(self):
        '''
        createLock makes the lock file that tells other users this deployment is open.
        '''
        try:
            self.lockPath=self.dataPath+self.userName()+".lck"
            self.lockfile=open(self.lockPath, "w")
        except OSError:
            self.lockPath=None
            self.lockfile=None

    def releaseLock(self):
        '''
        releaseLock closes and removes the lock file of the deployment that was open, if any.
        '''
        if self.lockfile is not None:
            try:
                self.lockfile.close()
            except OSError:
                pass
            self.lockfile=None
        if self.lockPath:
            try:
                os.remove(self.lockPath)
            except OSError:
                pass
            self.lockPath=None

    def closeDeployment(self):
        '''
        closeDeployment saves and closes the deployment that is open, if any.
        '''
        self.stopPlay()
        if self.dataDB is not None:
            self.writeFrameData()
            self.dataDB.dbClose()
            self.writeDatatoCSV()
            self.dataDB=None
        self.releaseLock()
        # must clear out everything
        self.activeProfile=None

    def unloadDeployment(self):
        '''
        unloadDeployment leaves SEBASTES as at start-up when a deployment could not be loaded, so
        that another one can be chosen. The reason has been shown to the user already.
        '''
        self.stopPlay()
        if self.dataDB is not None:
            self.dataDB.dbClose()
            self.dataDB=None
        self.releaseLock()
        for video in self.videoSources.values():
            video.release()
        self.videoSources={}
        # progress bars of a load that stopped half way
        for progressBar in [self.leftPB, self.rightPB]:
            if progressBar is not None:
                self.statusBar.removeWidget(progressBar)
        self.leftPB=None
        self.rightPB=None
        self.deployment=None
        self.activeProfile=None
        self.noLoad=True
        self.recordBtn.setChecked(False)
        self.recordBtn.setEnabled(False)
        self.playBtn.setEnabled(False)
        self.copyBtn.setEnabled(False)
        self.setNavEnabled(False)
        self.imageSlider.setEnabled(True)
        for widget in self.recordEnableWidgets:
            widget.setEnabled(False)
        self.showTools(self.recordOnlyWidgets, False)
        for dock in [self.speciesDockWidget, self.metadataDockWidget, self.measurementsDock]:
            dock.hide()
        self.maxFrame.setText('/ 0')
        self.videoMode=False
        self.updateTimeLabel()
        self.imageSlider.setMarks([], [])
        self.updateDeploymentLabel()
        self.clearMarks()
        for obj in [self.gvLeft, self.gvRight]:
            obj.clearViewer()
        self.showWelcome()

    def loadDeployment(self, deploymentPath=None):
        '''
        loadDeployment loads a deployment. The folder is asked for unless it is given (the welcome page gives the one
        that was chosen in its list); everything else is checked the same way.
        '''
        if not isinstance(deploymentPath, str):
            #  get the deployment directory
            deploymentPath = QFileDialog.getExistingDirectory(self, 'Select Deployment Directory', self.__dataDir,
                                                  QFileDialog.Option.ShowDirsOnly)
        elif not os.path.isdir(deploymentPath):
            QMessageBox.warning(self, "ERROR", deploymentPath+" is not a folder any more.")
            return
        if deploymentPath == '':
            return
        deploymentPath = deploymentPath.replace(os.sep, '/').rstrip('/')
        deployment = deploymentPath.split('/')[-1]
        sourcePath = QDir(deploymentPath)
        sourcePath.cdUp()
        self.__dataDir = sourcePath.path()
        dataPath = sourcePath.path()+ '/' +deployment + '/' + "data" + '/'

        # Everything that can be cancelled or refused comes first: the deployment that is open
        # stays as it is until the new one is committed to below.
        # check for lock state
        username = self.userName()
        ownLocks = []
        for lockPath in glob.glob(glob.escape(dataPath) + '*.lck'):
            lockUser = os.path.splitext(os.path.basename(lockPath))[0]
            if lockUser != username:# stop from oopening!
                QMessageBox.warning(self, "ERROR", lockUser+" has this deployment open. Go check with them.")
                return
            # i have this open, must have crashed or something.  the lockfile is replaced below
            ownLocks.append(lockPath)

        # get projects
        dlg=selectprojectdlg.SelectProjectDlg(self)
        if not dlg.exec() or dlg.selectedProject==None:
            QMessageBox.warning(self, "ERROR", "You have to select a Project to load deployment.")
            return
        project=dlg.selectedProject
        projectDict=dlg.selectedProjectDict

        # the profile saved with this deployment, else ask for one
        profile=self.storedProfile(dataPath+project+'_'+deployment+'.db', deployment)
        if not profile:
            profile=self.storedProfile(dataPath+deployment+'.db', deployment)# legacy database
        newProfile=not profile
        if newProfile:
            dlg=makeseldlg.MakeSelDlg(self,  'profile', 'active')
            if not dlg.exec():
                QMessageBox.warning(self, "ERROR", "Need a profile to work.")
                return
            profile=dlg.value
            query=self.appDB.dbQuery("SELECT value FROM PROFILE_SETTINGS WHERE profile='"+sqlQuote(profile)+"' AND setting='LeftCameraImagePath'")
            leftPath, =query.first()
            if leftPath==None or not QDir(deploymentPath + '/' + leftPath + '/').exists():
                QMessageBox.warning(self, "ERROR", "This is not a valid deployment folder.")
                return

        # go ahead: close the deployment that is open and switch to the new one
        self.closeDeployment()
        for lockPath in ownLocks:
            try:
                os.remove(lockPath)
            except OSError:
                pass
        self.deploymentPath = deploymentPath
        self.deployment = deployment
        self.sourcePath = sourcePath
        self.dataPath = dataPath
        self.activeProject = project
        self.projectDict = projectDict
        if self.openDeployment(profile, newProfile):
            self.addRecentDeployment(deploymentPath)
        else:
            self.unloadDeployment()

    def openDeployment(self, profile, newProfile):
        '''
        openDeployment opens the data database of the deployment chosen in loadDeployment, loads
        its profile and shows it. It returns False, after telling the user why, when it can't.
        '''
        #  check if the database folder exists
        self.speciesCollection=self.projectDict['species_collection']
        self.metadataGroup=self.projectDict['metadata_group']

        ################   HERE we will open a local "data db" ######################

        #  check if the local SQLite database file exists
        if QDir(self.dataPath).exists():
            #  check if the SQLite database file exists
            if QFile(self.dataPath + self.activeProject+'_' + self.deployment+'.db').exists():
                #  try to open the database
                try:
                    self.dataDB = dbConnection.dbConnection(self.dataPath + self.activeProject+'_' + self.deployment+'.db', '', '',label='dataDB', driver="QSQLITE")
                except:
                    QMessageBox.warning(self, "ERROR", "There's something amiss with the data folder. You need to clear this up to access this deployment.")
                    return False
                # check for existing profile in profile db
                try:
                    self.dataDB.dbOpen()
                except:
                    self.showError()
                    return False

            elif QFile(self.dataPath +  self.deployment+'.db').exists():# legacy database
                # rename file to current db naming convention with the project 
                QFile().rename(self.dataPath +  self.deployment+'.db', self.dataPath + self.activeProject+'_' + self.deployment+'.db')
                #  try to open the database
                try:
                    self.dataDB = dbConnection.dbConnection(self.dataPath + self.activeProject+'_' + self.deployment+'.db', '', '',label='dataDB', driver="QSQLITE")
                except:
                    QMessageBox.warning(self, "ERROR", "There's something amiss with the data folder. You need to clear this up to access this deployment.")
                    return False
                # check for existing profile in profile db
                try:
                    self.dataDB.dbOpen()
                except:
                    self.showError()
                    return False
            else: # we have a new project, lets make a new db file, shall we?
                try:
                    self.dataDB = dbConnection.dbConnection(self.dataPath + self.activeProject+'_' + self.deployment+'.db', '', '',label='dataDB', driver="QSQLITE")
                    self.dataDB.dbOpen()
                    if self.dataDB.db.isOpen():
                        self.makeDB()
                    else:
                        QMessageBox.warning(self, "ERROR", "Can't create local database.")
                        return False
                except:
                    self.showError()
                    return False
        else:# a new db file is needed - this is the first time we are opening this drop
            # make the folder
            QDir().mkdir(self.dataPath)
            try:
                self.dataDB = dbConnection.dbConnection(self.dataPath + self.activeProject+'_' + self.deployment+'.db', '', '',label='dataDB', driver="QSQLITE")
                self.dataDB.dbOpen()
                if self.dataDB.db.isOpen():
                    self.makeDB()
                else:
                    QMessageBox.warning(self, "ERROR", "Can't create local database.")
                    return False
            except:
                self.showError()
                return False

        self.createLock()

        # add annotator and time stamp field if it doesnt exist
        query = self.dataDB.dbQuery("PRAGMA table_info('TARGETS')")
        fields=[]
        for field in query:
            fields.append(field[1])
        if not 'ANNOTATOR' in fields:
            self.dataDB.dbExec("ALTER TABLE TARGETS ADD COLUMN ANNOTATOR TEXT;")
            self.dataDB.dbExec("ALTER TABLE FRAME_METADATA ADD COLUMN ANNOTATOR TEXT;")
            self.dataDB.dbExec("ALTER TABLE FRAMES ADD COLUMN ANNOTATOR TEXT;")
            self.dataDB.dbExec("ALTER TABLE BOUNDING_BOXES ADD COLUMN ANNOTATOR TEXT;")

        # check for timastamp field in db, if not, add it
        query = self.dataDB.dbQuery("PRAGMA table_info('TARGETS')")
        fields=[]
        for field in query:
            fields.append(field[1])
        if not 'TIME_STAMP' in fields:
            self.dataDB.dbExec("ALTER TABLE TARGETS ADD COLUMN TIME_STAMP TEXT;")
            self.dataDB.dbExec("ALTER TABLE FRAMES ADD COLUMN TIME_STAMP TEXT;")

        # check for timastamp field in db, if not, add it
        query = self.dataDB.dbQuery("PRAGMA table_info('TARGETS')")
        fields=[]
        for field in query:
            fields.append(field[1])
        if not 'PROJECT' in fields:
            self.dataDB.dbExec("ALTER TABLE DEPLOYMENT ADD COLUMN PROJECT TEXT;")
            self.dataDB.dbExec("ALTER TABLE TARGETS ADD COLUMN PROJECT TEXT;")
            self.dataDB.dbExec("ALTER TABLE FRAME_METADATA ADD COLUMN PROJECT TEXT;")
            self.dataDB.dbExec("ALTER TABLE FRAMES ADD COLUMN PROJECT TEXT;")
            self.dataDB.dbExec("ALTER TABLE BOUNDING_BOXES ADD COLUMN PROJECT TEXT;")

        # if they do not exist, create points and lengths tables and move the data over from targets.  Then change targets table too...
        if not "POINTS" in self.dataDB.db.tables():
            file=open('../db/v3ChangesToDB.db.sql')
            sql_script=file.read()
            statements=sql_script.split(';')
            for statement in statements:
                if statement !='':
                    statement=statement.replace('\t', ' ')
                    statement=statement.replace('\n', '')
                    try:
                        self.dataDB.dbExec(statement)
                    except:
                        pass
            self.dataDB.dbExec("BEGIN TRANSACTION;")
            # move the data from targerts
            query = self.dataDB.dbQuery("SELECT frame_number, target_number,  LX, LY, RX, RY, Range, Error, Length, LHX,LHY, LTX, LTY, RHX, RHY, RTX, RTY, HX, HY, HZ, TX, TY, TZ FROM targets WHERE deployment_id='"+sqlQuote(self.deployment)+"'")
            for frame_number, target_number, LX, LY, RX, RY, Range, Error, Length, LHX, LHY, LTX, LTY, RHX, RHY, RTX, RTY, HX, HY, HZ, TX, TY, TZ in query:

                # this is point data
                if LX == None:# this is only one point in one image
                    LX='NULL'
                    LY='NULL'
                    HZ='NULL'
                    HX='NULL'
                    HY='NULL'
                    Range='NULL'
                    Error='NULL'
                    point_label='single_image_mark'
                elif RX == None:
                    RX='NULL'
                    RY='NULL'
                    HZ='NULL'
                    HX='NULL'
                    HY='NULL'
                    Range='NULL'
                    Error='NULL'
                    point_label='single_image_mark'
                else:
                    point_label='range_to_target'
                sql="INSERT INTO points (project, deployment_ID,frame_number, target_number,  point_label, LX, LY, RX, RY, X, Y, Z, Range, Error)  VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+frame_number+","+target_number+",'"+point_label+"',"+LX+","+LY+","+RX+","+RY+","+HX+","+HY+","+HZ+","+Range+","+Error+")"
                self.dataDB.dbExec(sql)
                if not Length==None:
                    # this is  line data
                    line_label='length'
                    self.dataDB.dbExec("INSERT INTO lines (project, deployment_ID,frame_number, target_number, line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2, X1, Y1, Z1, X2,Y2, Z2, Length, Error)  "+
                                    "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+frame_number+","+target_number+",'"+line_label+"',"+LHX+","+LHY+","+LTX+","+LTY+","+RHX+","+RHY+","+
                                    RTX+","+RTY+","+HX+","+HY+","+HZ+","+TX+","+TY+","+TZ+","+Length+","+Error+")")
            self.dataDB.dbExec("COMMIT;")
            # now delete target table extra fields
            dropfileds=['LX','LY','RX','RY','Range','Error','Length','LHX','LHY','LTX','LTY','RHX','RHY','RTX','RTY','HX','HY','HZ','TX','TY','TZ']
            for field in dropfileds:
                self.dataDB.dbExec("ALTER TABLE TARGETS DROP COLUMN "+field+';')

        # measurement names
        query = self.dataDB.dbQuery("PRAGMA table_info('LINES')")
        fields=[]
        for field in query:
            fields.append(field[1])
        if not 'NAME' in fields:
            self.dataDB.dbExec("ALTER TABLE LINES ADD COLUMN NAME TEXT;")
        # now load the profile
        self.activeProfile=profile
        if not self.loadProfile():
            QMessageBox.warning(self, "ERROR", "There's something amiss with the profile settings.  Have a peek!")
            self.dataDB.dbExec("DELETE FROM deployment WHERE project='"+sqlQuote(self.activeProject)+"' and deployment_id='"+sqlQuote(self.deployment)+"'")
            return False
        if newProfile:
            #were good to go,  put it into the db
            time_now=QDateTime().currentDateTime()
            self.dataDB.dbExec("INSERT INTO deployment (project, deployment_ID,last_opened,profile)"+
            " VALUES('"+sqlQuote(self.activeProject)+"', '"+sqlQuote(self.deployment)+"','"+time_now.toString()+"','"+sqlQuote(self.activeProfile)+"')")

        self.loadEnhancements()

        self.appSettings.setValue('self.dataPath', self.deploymentPath)
        return bool(self.setupDeployment())

    def loadEnhancements(self):
        try:
            if QDir(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/').exists():
                if QFile(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.deployment+'_image_adjustments.npy').exists():
                    temp=ny.load(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.deployment+'_image_adjustments.npy', allow_pickle=True)
                    imageadjustments=temp.item()
                    
                    self.leftAdjustmentParms=imageadjustments['left']
                    self.rightAdjustmentParms=imageadjustments['right']
                    self.gvLeft.image.setParameters(self.leftAdjustmentParms)
                    self.gvRight.image.setParameters(self.rightAdjustmentParms)
        except:
            pass
    
        

        
    def setupDeployment(self):
        try:
            self.updateDeploymentLabel()
            # clear out gv transform
            self.gvRight.resetTransform()
            self.gvLeft.resetTransform()
            # apply mask, if desired
            if self.doMask:
                val=self.settings['SubsampleMask']
                vals=val.split(',')
                rect=QRect(int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3]))
                self.gvRight.setSubsampleRect(rect)
                self.gvLeft.setSubsampleRect(rect)

            # a video ImageFileType means one video per camera folder instead of still images
            self.videoMode=self.settings.get('ImageFileType', '').strip().lower() in videoSource.VIDEO_TYPES
            for video in self.videoSources.values():
                video.release()
            self.videoSources={}

            # load in some fetcher properties
            if not self.videoMode:
                p=self.settings['FrameNumberIndices'].split('-')
                self.imgNumInds=[int(p[0]), int(p[1])]

                if self.settings['ImageTimestampType'].strip()=='in_file_name':
                    self.imgTimestamp=[self.settings['ImageTimestampFormat'].strip(), int(self.settings['ImageTimestampStart'].strip())]
                elif self.settings['ImageTimestampType'].strip()=='EXIF':
                    self.imgTimestamp=['exif',0]
                else:
                    self.imgTimestamp=['NoTimestamp',0]

            # get image names
            self.LPath=self.deploymentPath + '/' + self.settings['LeftCameraImagePath']+ '/'
            self.RPath=self.deploymentPath + '/' + self.settings['RightCameraImagePath']+ '/'
            # check for validity
            if not QDir(self.LPath).exists():
                QMessageBox.warning(self, "ERROR", self.LPath+" Is not a valid folder.")
                return False
            if not QDir(self.RPath).exists():
                QMessageBox.warning(self, "ERROR", self.RPath+" Is not a valid folder.")
                return False
            #  set the loading error var
            self.__loadingError = False
            #  create a couple of progress bars
            self.leftPB = QProgressBar()
            self.leftPB.setRange(0,100)
            self.leftPB.setValue(0)
            self.rightPB = QProgressBar()
            self.rightPB.setRange(0,100)
            self.rightPB.setValue(0)
            self.statusBar.addWidget(self.leftPB)
            self.statusBar.addWidget(self.rightPB)
            # turn s**t on
            for widget in self.recordEnableWidgets:
                widget.setEnabled(True)
            #  clear the viewers
            for obj in [self.gvLeft, self.gvRight]:
                obj.removeScene()
                obj.createScene()
            self.leftImageDict=self.getImageFiles(self.LPath,  self.leftPB)
            if self.leftImageDict is None:
                return False
            keys=list(self.leftImageDict.keys())
            keys.sort()
            self.leftImageFrames=keys
            self.statusBar.removeWidget(self.leftPB)
            self.leftPB = None
            self.rightImageDict=self.getImageFiles(self.RPath,  self.rightPB)
            if self.rightImageDict is None:
                return False
            keys=list(self.rightImageDict.keys())
            keys.sort()
            self.rightImageFrames=keys
            self.statusBar.removeWidget(self.rightPB)
            self.rightPB = None
            if self.videoMode:
                # the play speed slider is in frames per second: play videos at their own frame rate
                fps=self.videoSources[self.LPath].fps
                if fps:
                    self.playSpeedSlider.setValue(int(round(fps)))

            self.noLoad=False
            self.datadlg=dataviewdlg.DataViewDlg(self)
            #position = self.appSettings.value('datawinposition', QPoint(10,10))
            #self.datadlg.move(position)
            self.datadlg.selectionEvent.connect(self.changeSelectionFromTable)
            
            self.datadlg.keyPress.connect(self.__keyPressEvent)
            # load in stereo calibration

            
            # the profile dialog saves an empty CalibrationFileName when there is no calibration
            if self.settings.get('CalibrationFileName', '').strip():
                self.mode='stereo'
                filename=str(self.settings['CalibrationFileName'])
                filename=filename.strip()
                if filename[-4:]=='.npz':
                    self.stereoComp.mode='openCV'
                elif filename[-4:]=='.mat':
                    self.stereoComp.mode='matlab'
                elif filename[-4:]=='.yml':
                    self.stereoComp.mode='yaml'
                else:
                    QMessageBox.warning(self, "ERROR", filename+" is not an accepted file type.")
                    return False
                if QFile('../calibrations/' + filename).exists():
                    try:
                        State, cal = self.stereoComp.importCalData('../calibrations/' + filename)
                    except:
                        QMessageBox.warning(self, "ERROR", filename+ "  Has issues!!!")
                        return False
                else:
                    QMessageBox.warning(self, "ERROR", filename+" Is not located in the SEBASTES calibration folder.  Please put it there.")
                    return False
                if not State:
                    QMessageBox.warning(self, "ERROR", cal)
                    return False
            else:
                self.mode='mono'

            #  try to get the camera orientations
            if 'RotateRightImage' in self.settings:
                self.gvRight.setRotation(self.settings['RotateRightImage'])
            else:
                #  no orientation data available for this camera
                self.gvRight.setRotation('0')
            if 'RotateLeftImage' in self.settings:
                self.gvLeft.setRotation(self.settings['RotateLeftImage'])
            else:
                #  no orientation data available for this camera
                self.gvLeft.setRotation('0')


            self.minFr=min(min(self.leftImageFrames), min(self.rightImageFrames))
            self.maxFr=max(max(self.leftImageFrames), max(self.rightImageFrames))
            self.maxFrame.setText('/ '+str(self.maxFr))
            self.imageSlider.setMinimum(0)
            self.imageSlider.setMaximum(len(self.leftImageDict)-1)
            self.imageSlider.setSingleStep(1)
            self.recordBtn.setEnabled(True)
            self.copyBtn.setEnabled(True)
            self.setNavEnabled(True)
            self.showViews()
            self.fitNavBar()
            self.toggleRecord()
            # the first frame is the first of the slider: frame 0 of a video, the first image file of a folder of images
            if self.imageSlider.value()==self.imageSlider.minimum():
                # the slider is already there (an earlier deployment) and sends no valueChanged
                self.__changeImage()
            else:
                self.imageSlider.setValue(self.imageSlider.minimum())
            self.playBtn.setEnabled(True)
            self.measurementsDock.setDeployment(self.dataDB, self.deployment)
            if self.measurementsDock.isHidden():
                self.measurementsDock.show()
                if not self.layoutRestored:
                    # no saved layout: a width that shows the main columns, and not more than 30 % of the window; the user can drag its edge
                    self.resizeDocks([self.measurementsDock], [min(MEASUREMENTS_WIDTH, int(0.3*self.width()))], Qt.Orientation.Horizontal)
            return True
        except:
            self.showError()
            return
        
    def makeDB(self):
        file=open('../db/Project.db.sql')
        sql_script=file.read()
        statements=sql_script.split(';')
        for statement in statements:
            if statement.strip() !='':
                statement=statement.replace('\t', ' ')
                statement=statement.replace('\n', '')
                try:
                    self.dataDB.dbExec(statement)
                except:
                    pass


    def getVideoFrames(self, imPath):
        '''
        Video mode counterpart of getImageFiles: opens the one video in imPath and
        returns the same {frame: [timestamp, file name]} dict, frames numbered from 0.
        '''
        type=self.settings['ImageFileType'].strip().lower()
        videoFiles=[f for f in os.listdir(str(imPath)) if f.lower().endswith('.'+type)]
        if len(videoFiles)!=1:
            QMessageBox.warning(self, "ERROR", imPath+" must contain exactly one ."+type+" video, found "+str(len(videoFiles))+".")
            return None
        try:
            video=videoSource.videoSource(os.path.join(str(imPath), videoFiles[0]))
        except:
            self.showError()
            return None
        self.videoSources[imPath]=video
        return {frame:[video.frameTime(frame), videoFiles[0]] for frame in range(video.frameCount)}

    def getImageFiles(self,  imPath,  progressbar):
        if self.videoMode:
            return self.getVideoFrames(imPath)
        try:
            #  check if the cached directory structure exists
            # left images
#            if QFile(imPath+'.imListCache').exists(): # weve alread loaded this one
#                icacheFile = open(imPath + '.imListCache')
#                imageFileDict = pickle.load(icacheFile)
#                icacheFile.close()
#            else:#  get the directory listing
            imageFileDict={}
            if 'ImageFileType' in self.settings:
                type=self.settings['ImageFileType']
            else:
                type='jpg'
            lastProgress = 0
            totalFrames = len(os.listdir(str(imPath) ))
            i=1
            goodtimestamp=True
            # match the extension case-insensitively (Linux glob is case-sensitive)
            imageFiles=[f for f in os.listdir(str(imPath)) if f.lower().endswith('.'+type.lower())]
            for imageFile in imageFiles:
                file=os.path.join(str(imPath), imageFile)
                imageFrame=int(imageFile[max([(self.imgNumInds[0]-1), 0]):self.imgNumInds[1]])
                if self.settings['ImageTimestampType'].lower()=='in_file_name':
                    try:
                        dateStartInd=self.imgTimestamp[1]-1# for python's sake
                        if self.imgTimestamp[0]=='DyyyyMMdd-Thhmmss.zzz':
                            trim=3
                            pydateformat='D%Y%m%d-T%H%M%S.%f'
                        else:
                            pydateformat=self.imgTimestamp[0]
                            trim=0
                        try:
                            timestamp=datetime.strptime(imageFile[dateStartInd:dateStartInd+len(datetime.now().strftime(pydateformat))-trim], pydateformat)
                            goodtimestamp=True
                        except:
                            goodtimestamp=False
                            timestamp=None

                    except:# fix this in the future?
                        goodtimestamp=False
                        timestamp=None
                elif  self.settings['ImageTimestampType'].lower()=='exif':
                    try:
                        img = Image(open(file, 'rb'))
                        if img.has_exif:
                            goodtimestamp=True
                            timestamp=datetime.strptime(img.datetime,'%Y:%m:%d %H:%M:%S')
                        else:
                            goodtimestamp=False
                            timestamp=None
                    except:
                            goodtimestamp=False
                            timestamp=None
                else:
                    goodtimestamp=False
                    timestamp=None
                    
                imageFileDict.update({imageFrame:[timestamp, imageFile]})
                #  signal our progress
                progress = int((i / float(totalFrames)) * 100)
                if (progress !=  lastProgress):
                    lastProgress = progress
                    progressbar.setValue(progress)
                i+=1
#                icacheFile = open(imPath + '.imListCache', 'wb')
#                pickle.dump(imageFileDict, icacheFile)
#                icacheFile.close()
            if not goodtimestamp:
                QMessageBox.warning(self, "ERROR", "Timestamp could not be extracted from file name. Check the profile setup!")
            
            return imageFileDict
        except:
            self.showError()

    def viewApplicationDB(self):
        dlg=viewapplicationdbdlg.ViewApplicationDBDlg(self)
        dlg.exec()
        
    def directEditDBTables(self):
        dlg=directeditDBdlg.DirectEditDBDlg(self)
        dlg.exec()
##############################2. GV FUNCTIONS ######################################



    def showHelpImage(self):
        '''
        showHelpImage shows the welcome page (the photo of the fish is on it), unless a deployment has been loaded since.
        '''
        if self.appDB==None:
            self.close()

        if self.deployment is None:
            self.showWelcome()

    def showAdjustmentsDialog(self):
        if self.sender()==self.adjLeftBtn:
            gv=self.gvLeft
            self.leftAdjustmentParms = gv.image.getParameters()
            gv.adjustmentDialog.setState(self.leftAdjustmentParms)
        else:
            gv=self.gvRight
            self.rightAdjustmentParms = gv.image.getParameters()
            gv.adjustmentDialog.setState(self.rightAdjustmentParms)
        gv.adjustmentDialog.show()

    def resizeEvent(self, event):

        #  Scale the image to fill the the image widget when we resize.
        #  This is a bit heavy handed, it will reset the zoom on resize,
        #  but we want the image to scale when we resize and dealing with
        #  the details of resizing when zoomed is a headache.
        self.gvLeft.fillExtent()
        self.gvRight.fillExtent()

    def __changeImage(self):
        '''
        This method is called whenever the images are changed, either by
        adjusting brightness, gamma, or contrast or by moving the image
        slider.
        '''
        try:
            #  tell the fetchers to send us an new/adjusted image
            if self.recordBtn.isChecked():
                self.deSelect()
                self.clearMarks()
                # deal with orphaned stereo pair
                self.pairPoints=[]
                # and with a fish being marked: the scene is rebuilt, start again from its head
                self.fishStep=0
                self.fishLines={}
                # deal with the grid
                if not self.gridSetup['PersistentGrid'] and self.gridCheck.isChecked():
                    self.gridCheck.setChecked(False)
                    self.gridBoxAction()
                for obj in [self.gvLeft, self.gvRight]:
                    obj.removeScene()
                    obj.createScene()
            
                    
            self.LFile=self.readImage(self.gvLeft)
            self.RFile=self.readImage(self.gvRight)
            if self.imageSlider.value()>len(self.leftImageFrames)-1:
                return
            currentFrame=self.leftImageFrames[self.imageSlider.value()]
            self.frameBox.setText(str(currentFrame))
            self.updateTimeLabel(currentFrame)
            
            if self.measureBtn.isChecked():
                    self.measureBtn.setChecked(False)
            self.zoomBtn=0
            self.targetLinkLabel.setText('')
            if self.recordBtn.isChecked():
                self.reloadData()
                self.incrementCounters()
            else:
                # read only
                self.showAnnotations()
            self.currentTarget=0
            self.updateFishGuide()
            if self.gridSetup['PersistentGrid'] and self.gridCheck.isChecked():
                self.gridBoxAction()
            if self.camtrawlMetadataFlag:
                # check to see if this has already had an entry in the metadata table
                query = self.dataDB.dbQuery("SELECT frame_number FROM frame_metadata WHERE frame_number = "+self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                got_frame, =query.first()
                if got_frame==None:
                    self.getCamtrawlMetadataValues(self.imageSlider.value())

            
            
        except:
            self.showError()

    def getCamtrawlMetadataValues(self,  frame):
        if int(frame) in self.metadata.sensorData['CTControl']['$OHPR']:
            attitudeString = self.metadata.sensorData['CTControl']['$OHPR'][int(frame)]
            stringParts = attitudeString.split(',')
            depth = '%.1f' % (float(stringParts[5]))
            # populate line boxes
            self.metadataLineEdits[0].setText(depth)
            self.metadataLineEdits[1].setText(stringParts[2])
            self.metadataLineEdits[2].setText(stringParts[1])
            self.metadataLineEdits[3].setText(stringParts[3])

    def readImage(self, gvObj):
        if self.imageSlider.value()>len(self.leftImageFrames)-1:
            return
        currentFrame=self.leftImageFrames[self.imageSlider.value()]
        try:
            if gvObj==self.gvLeft:
                imFile=self.leftImageDict[currentFrame][1]
                imTime=self.leftImageDict[currentFrame][0]
                imPath=self.LPath
            else:
                if currentFrame in self.rightImageDict:
                    imFile=self.rightImageDict[currentFrame][1]
                    imTime=self.rightImageDict[currentFrame][0]
                    imPath=self.RPath
                else:
                    gvObj.clearViewer()# this camera has no image for the frame
                    return
            imgFileLoc=imPath+imFile

            #  create the timestamp string
            if imTime:
                #self.dtString = dateTime.toString('yyyy-MM-dd hh:mm:ss.zzz')
                self.dtString = imTime.strftime('%Y-%m-%d %H:%M:%S.%f')
            else:
                self.dtString = ''
            if self.videoMode:
                image=self.videoSources[imPath].getFrame(currentFrame)
                if image is None:
                    gvObj.clearViewer()
                    return
                gvObj.setImageFromCvImage(image)
            else:
                gvObj.setImageFromFile(imgFileLoc)
            gvObj.resetView()
            gvObj.fillExtent()
            self.activeMark[gvObj]=None
            self.mouseInWidget(self.mousebits[0], self.mousebits[1], self.mousebits[2])
            return imgFileLoc

        except:
            self.showError()

    def mouseInWidget(self, imageObj, location, modifier):
        if imageObj==None:
            return
        #  you can use the mouseMoveEvent signal to provide a current pixel location
        #  on your GUI say in the status bar
        winsize=self.closeupWinSize
        source=QRect(max(int(round(location.x())-winsize/2), 0),max(int(round(location.y())-winsize/2), 0) , winsize, winsize)
        dest=QPixmap(256, 256)
        paint=QPainter(dest)
        paint.drawPixmap(QRect(0, 0, 256, 256), imageObj.imgPixmap,source)
        mark = QPolygonF()
        mark.append(QPointF(128,128-10))
        mark.append(QPointF(128,128+10))
        mark.append(QPointF(128,128))
        mark.append(QPointF(128-10,128))
        mark.append(QPointF(128+10,128))
        mark.append(QPointF(128,128))
        pen = QPen(QColor(255, 255, 0), 255)
        pen.setWidthF(1)
        paint.setPen(pen)

        paint.drawPolyline(mark)
        paint.end()
        self.closeup.imgLabel.setPixmap(dest)
        self.mousebits=[imageObj, location, modifier]

    def speedSet(self):
        self.playSpeed=float(self.playSpeedSlider.value())*(float(self.guiSettings['PlaybackSpeedAdjust']))
        self.playTimer.setInterval(int(1./self.playSpeed*1000))
        # restart the playback clock at the new speed
        self.playStartIndex=None

    def play(self):
        if self.playBtn.isChecked():
            self.playStartIndex=None
            self.playTimer.start()
        else:
            self.playTimer.stop()
        self.updatePlayButton()

    def stopPlay(self):
        if self.playBtn.isChecked():
            self.playBtn.setChecked(False)
            self.play()

    def moveSlider(self):
        '''
        moveSlider shows the frame the playback clock has reached. When drawing the two images
        takes longer than the frame interval, the frames in between are skipped and the video
        still plays at the chosen speed.
        '''
        frameIndex=self.imageSlider.value()
        if frameIndex>=self.imageSlider.maximum():
            # end of the deployment
            self.stopPlay()
            return
        if self.playStartIndex is None or frameIndex!=self.playLastIndex:
            # start, new speed, or the slider was moved by hand: count from the current frame
            self.playStartIndex=frameIndex
            self.playClock.start()
        targetIndex=self.playStartIndex+int(self.playClock.elapsed()/1000.*self.playSpeed)+1
        if targetIndex<=frameIndex:
            return
        if targetIndex-frameIndex>videoSource.MAX_GRAB:
            # this computer can't keep up: a longer jump would be a slow seek in the video,
            # so go on from here instead of falling further behind the clock
            targetIndex=frameIndex+videoSource.MAX_GRAB
            self.playStartIndex=None
        targetIndex=min(targetIndex, self.imageSlider.maximum())
        self.playLastIndex=targetIndex
        self.imageSlider.setValue(targetIndex)

#####################4. UI FUNCTIONS########################################

    def btnPress(self):
        for btn in [self.measureBtn]:
            if btn.isChecked():
                btn.setChecked(False)
        if self.pressTime.elapsed()<250:# user double clicked
            if self.spcSelDlg.exec() and self.spcSelDlg.listWidget.currentIndex().row()>-1:
                new_spc=self.spcSelDlg.listWidget.currentItem().text()
                # check to see if it is already in the button list
                ind=self.speciesList.index(new_spc)
                if ind<len(self.spcButtons):# new species is already attached to a button
                    # switch sort orders
                    old_sort=str(ind+1)
                else:# new species is coming in hot
                    old_sort="NULL"
                    
                btn=self.sender()
                old_spc=btn.text()
                new_sort=str(self.spcButtons.index(btn)+1)
                # update db
                self.appDB.dbExec("UPDATE SPECIES_SETUP SET sort_order="+old_sort+" WHERE species_group='"+sqlQuote(old_spc)+"' AND species_collection='"+sqlQuote(self.speciesCollection)+"'")
                self.appDB.dbExec("UPDATE SPECIES_SETUP SET sort_order="+new_sort+" WHERE species_group='"+sqlQuote(new_spc)+"' AND species_collection='"+sqlQuote(self.speciesCollection)+"'")
                self.setupSpcBtns()
        else:
            self.pressTime.start()
            if self.sender() in self.spcButtons:
                templist=list(self.spcButtons)
                templist.remove(self.sender())
            for btn in templist:
                btn.setChecked(False)

    def btnRelease(self):
        self.incrementCounters()

    def event(self, event):
        if (event.type() == QEvent.KeyPress):
            self.__keyPressEvent(None, event)
            return True
        else:
            return QMainWindow.event(self, event)

    def __keyPressEvent(self, ivObj, ev):
        if self.noLoad:
            return
        # which key is being held down
        self.key=ev.key()

        if ev.key() == 65:
            if self.computeMatchBox.isChecked():
                self.computeMatchBox.setChecked(False)
            else:
                self.computeMatchBox.setChecked(True)
                
        elif (ev.key() == Qt.Key_Delete):

            self.deleteSelMark()


        elif (ev.key() == Qt.Key_Home):
            self.linkBtn.setChecked(True)
            self.toggleLink()

        # navigate though images
        elif ev.key() in [ Qt.Key_Right, Qt.Key_Left]:
            # the navigation buttons come to the same place
            self.stepFrame(1 if ev.key() == Qt.Key_Right else -1, ev.modifiers() == Qt.ControlModifier)

        elif (ev.key() == Qt.Key_Escape):
            halfPair=len(self.pairPoints)==1 # a pair that was started and is being cancelled
            if halfPair:
                # get the zoom state before the marks are cleared
                lZoom=self.gvLeft.zoomLevel
                rZoom=self.gvRight.zoomLevel
                if self.activeMark[self.gvLeft]:
                    lPoint=self.activeMark[self.gvLeft].mapToScene(self.activeMark[self.gvLeft].boundingRect().center())
                else:
                    lPoint=None
                if self.activeMark[self.gvRight]:
                    rPoint=self.activeMark[self.gvRight].mapToScene(self.activeMark[self.gvRight].boundingRect().center())
                else:
                    rPoint=None
            self.deSelect()
            self.clearMarks()
            self.activeLine[self.gvLeft]=None
            self.activeLine[self.gvRight]=None
            self.activeMark[self.gvLeft]=None
            self.activeMark[self.gvRight]=None
            try:
                if self.rubberBanding:
                    self.rubberBanding = False
            except:
                self.showError()

            self.__changeImage()
            if halfPair:
                # zoom back
                if lPoint!=None:
                    self.gvLeft.zoomToPoint(lPoint, lZoom)
                if rPoint!=None:
                    self.gvRight.zoomToPoint(rPoint, rZoom)
                self.pairPoints=[]
        
        elif (ev.key() == Qt.Key_Z):
            # this is to quick undo auto targets only
            if self.computeMatchBox.isChecked():
                # remove current mark and delete from db
                self.dataDB.dbExec("DELETE FROM lines WHERE frame_number = "+self.frameBox.text()+" AND target_number = "+str(self.currentTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                self.dataDB.dbExec("DELETE FROM points WHERE frame_number = "+self.frameBox.text()+" AND target_number = "+str(self.currentTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                self.dataDB.dbExec("DELETE FROM targets WHERE frame_number = "+self.frameBox.text()+" AND target_number = "+str(self.currentTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                # remove mark
                self.gvLeft.removeItem(self.activeMark[self.gvLeft])
                self.gvLeft.update()
                self.gvRight.removeItem(self.activeMark[self.gvRight])
                self.gvRight.update()
                self.measurementsDock.refresh()
                
    def __keyReleaseEvent(self,ivObj, ev):
        # no key is being held down right now

        if (ev.key() == Qt.Key_Shift):
            # in the guided fish marking the pending point waits for the other image (Esc cancels it)
            if  not self.stereoOnlyCheckBox.isChecked() and not self.fishGuideActive():
                if len(self.pairPoints)==1: #user lifted shift button  but didn't mean to
                    lZoom=self.gvLeft.zoomLevel
                    rZoom=self.gvRight.zoomLevel
                                # get the zoom state
                    if self.activeMark[self.gvLeft]:
                        lPoint=self.activeMark[self.gvLeft].mapToScene(self.activeMark[self.gvLeft].boundingRect().center())
                    else:
                        lPoint=None
                    if self.activeMark[self.gvRight]:
                        rPoint=self.activeMark[self.gvRight].mapToScene(self.activeMark[self.gvRight].boundingRect().center())
                    else:
                        rPoint=None
                    # find the pair
                    self.__changeImage()
                    # zoom back
                    if lPoint!=None:
                        self.gvLeft.zoomToPoint(lPoint, lZoom)
                    if rPoint!=None:
                        self.gvRight.zoomToPoint(rPoint, rZoom)
                    self.pairPoints=[]
        self.key=None



    def myWheelEvent(self, imageObj, ev):
        """
        Zoom using the wheel event.
        """

        #  ev is the Qt mouse wheel event structure. Important elements are:
        #   delta - which is +120 for a forward roll and -120 for a backward roll
        #   pos - which is the position as QPointF


        #  for this example we'll only zoom if we have an active mark in each
        #  image. This way the
        if (self.activeMark[self.gvLeft] or
            self.activeMark[self.gvRight]):

            #  For zooming in this example we'll zoom to our active mark. This
            #  means that when possible, the mark will be centered in the view.

            if (ev.angleDelta().y() > 0):
                #  mouse rolled forward - zoom in
                if self.activeMark[self.gvLeft]:
                    self.gvLeft.zoomToMark(self.activeMark[self.gvLeft], 1)
                if self.activeMark[self.gvRight]:
                    self.gvRight.zoomToMark(self.activeMark[self.gvRight], 1)
                self.zoomBtn=self.zoomBtn+1
            else:
                #  mouse rolled back - zoom out
                if self.activeMark[self.gvLeft]:
                    self.gvLeft.zoomToMark(self.activeMark[self.gvLeft], -1)
                if self.activeMark[self.gvRight]:
                    self.gvRight.zoomToMark(self.activeMark[self.gvRight], -1)
                self.zoomBtn=self.zoomBtn-1

#        else:
#            if (ev.angleDelta() > 0):
#                    self.gvLeft.scale( 1, 1)
#                    self.gvRight.scale( 1, 1)
#            else:
#                    self.gvLeft.zoomToPoint(ev.pos(), -1)
#                    self.gvRight.zoomToPoint(ev.pos(), -1)

    def deSelect(self):
        for items in self.__selectedItems:
            items.setSelected(False)
        self.activeMark [self.gvRight]=None
        self.activeMark [self.gvLeft]=None
        self.__selectedItems=[]


    def imageClick(self, imageObj, clickLoc, button, currentKbKey, item):
        # whatever the click did (the handler has many ways out), the epipolar hints show the pair it left half done
        try:
            self.handleImageClick(imageObj, clickLoc, button, currentKbKey, item)
        finally:
            self.updateEpipolar()

    def handleImageClick(self, imageObj, clickLoc, button, currentKbKey, item):
        # selection code
        if button==Qt.MouseButton.RightButton:
            # first deselect everything
            self.deSelect()
            remList=[]
            for i in item:
                if not i in self.pointMarks and not i in self.boxMarks:
                    remList.append(i)
            for i in remList:
                item.remove(i)
            if len(item)>0:# we only want to select non temp marks!


                item=item[0]
                item.setSelected(True)
                self.__selectedItems.append(item)
                self.pairedTarget=False

                if item in self.pointMarks:#these are the points
                    self.activeMark [imageObj]=item
                    # check for paired item
                    target_number = int(self.pointMarks[item][0])
                    self.currentTarget=target_number
                    # get target level annotator
                    query = self.dataDB.dbQuery("SELECT annotator FROM TARGETS WHERE frame_number = "+self.frameBox.text()+" and target_number="+str(self.currentTarget)+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                    current_tator, =query.first()
                    if current_tator==None:
                        current_tator=''
                    self.annotatorLabel.setText(current_tator)
                    
                    query = self.dataDB.dbQuery("SELECT target_link FROM targets WHERE frame_number = "+self.frameBox.text()+" and target_number="+str(self.currentTarget)+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                    target_link, =query.first()
                    if target_link!='':
                        self.targetLinkLabel.setText(target_link)
                    for pairItem, info in self.pointMarks.items():
                        if info[0]==target_number:
                            if not info[1]==imageObj:
                                pairItem.setSelected(True)
                                self.pairedTarget=True
                                self.__selectedItems.append(pairItem)
                                if imageObj==self.gvLeft:
                                    self.activeMark [self.gvRight]=pairItem
                                else:
                                    self.activeMark [self.gvLeft]=pairItem
                if self.showDataCheck.isChecked():
                    self.selectValueFromImage()# this is to send delection signal to data view window and select the appropriate row
                # if we have checked link button, put in th elink
                # clear link display

                if len(self.linkData)>0:
                    self.dataDB.dbExec("UPDATE targets SET target_link = "+str(self.linkData[1])+
                    " WHERE frame_number = "+self.frameBox.text()+" AND target_number ="+str(self.currentTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                    self.linkData=[]
                    self.targetLinkLabel.setText(str(self.currentTarget))
                    self.linkBtn.setChecked(False)
        else:
            try:
                if self.fishGuideActive() and imageObj!=self.fishImage():
                    # the dimmed image waits for its turn
                    return
                if self.measureBtn.isChecked():
                    dimLine = imageObj.startDimensionLine(clickLoc, taillength=self.guiSettings['MeasureLineTailLength'],  thickness=self.guiSettings['MeasureLineWidth'], color=self.guiSettings['TargetLineColor'])
                    self.rubberBanding = True
                    #check to see if we already have amark on this gv?
                    old_line=None
                    for lineObj, descriptor in self.lineMarks.items():
                        if descriptor[1]==imageObj and descriptor[0]==self.currentTarget:# we already have a dimension line for this target in this image
                            old_line=lineObj
                            break
                    if old_line:# we do, get rid of it
                        del self.lineMarks[old_line] 
                        imageObj.removeItem(old_line)
                    self.lineMarks.update({dimLine:[self.currentTarget, imageObj]})
                    

                else:

                    # add a species count marker
                    # check to see if any species is selected
                    self.spcInd=None
                    for btn in self.spcButtons:
                        if btn.isChecked():
                            self.spcInd=self.spcButtons.index(btn)
                            break
                    if not self.spcInd==None:# theres some kind of class selected
                        if item:
                            remList=[]
                            for i in item:
                                if not i in self.pointMarks:
                                    remList.append(i)
                            for i in remList:
                                item.remove(i)

                        # once a fish is started its other points need no Shift
                        stereoClick=(QGuiApplication.queryKeyboardModifiers()==Qt.ShiftModifier or self.stereoOnlyCheckBox.isChecked()
                                     or self.fishStep>0)
                        if stereoClick:
                            if not self.stereoAvailable():
                                return
                            if self.fishStep>=2:
                                self.addTailPoint(imageObj, clickLoc)
                                return
                            style='o'
                            col=self.spcColors[self.spcInd]
                            if len(self.pairPoints)>0:
                                if imageObj in self.pairPoints[0]:
                                    return
                        else:
                            style='+'
                        # extract color from button?
                        btn=self.spcButtons[self.spcInd]
                        colstr=re.findall(r'\d+', btn.styleSheet())
                        col=[int(colstr[0]), int(colstr[1]), int(colstr[2])]

                        if self.recordBtn.isChecked():
                            # check to see if in grid boundary, if needed
                            if self.gridSetup['CellBoundary'] and self.gridCheck.isChecked():
                                if self.randomCellBounds is not None:
                                    if clickLoc.x()<self.randomCellBounds[0] or clickLoc.x()>self.randomCellBounds[1] or clickLoc.y()<self.randomCellBounds[2] or clickLoc.y()>self.randomCellBounds[3]:
                                        QMessageBox.warning(self, "ERROR", "Target not within selected grid cell! If you don't want this, check grid setup.")
                                        return
                            # add the mark
                            query = self.dataDB.dbQuery("SELECT max(target_number) FROM targets WHERE frame_number = "+self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                            target_count, =query.first()
                            if target_count!=None:
                                self.currentTarget=int(target_count)+1
                            else:# no targets yet for this frame
                                self.currentTarget=1
                            if self.makeBoxes:
                                imageObj.startRubberBand(clickLoc, color=self.spcColors[self.spcInd],thickness=self.guiSettings['BoxLineThickness'])

                                self.rubberBanding = True
                                return# we are just rubberbanding, no need to do anythin else


                            marker = imageObj.addMark(clickLoc, style=style, color=col,
                                                      size=1.0, thickness=1.0, alpha=255, selectThickness=self.selThickness,  selectColor=self.selColor)
                            spcLabel=''
                            if self.guiSettings['LabelSpeciesParam']>0 and (self.spcInd !=None):
                                spcLabel=self.spcButtons[self.spcInd].text()
                                if len(spcLabel)>self.guiSettings['LabelSpeciesParam']:
                                    spcLabel=spcLabel[0:self.guiSettings['LabelSpeciesParam']]

                            marker.addLabel(str(self.currentTarget)+" "+spcLabel, color=col, offset=self.textOffset, name='tnumber',  size=self.guiSettings['LabelTextSize'])
                            if not self.labelCheck.isChecked():
                                marker.hideLabels(None)


                            if stereoClick:# matched target
                                if len(self.pairPoints)<1:# have only half of the points for this matched target
                                    if self.computeMatchBox.isChecked():# here we auto fill both points
                                        if imageObj==self.gvLeft:
                                            im1=self.gvLeft.image.enhancedData
                                            im2=self.gvRight.image.enhancedData
                                        else:
                                            im2=self.gvLeft.image.enhancedData
                                            im1=self.gvRight.image.enhancedData
                                        point=ny.array([[clickLoc.x(), clickLoc.y()]])
                                        state,  point_c,  score=self.stereoComp.computeMatch(im1, im2, point)
                                        if not state:
                                            QMessageBox.warning(self, "ERROR",score)
                                            self.__changeImage()
                                            self.computeMatchBox.setChecked(False)
                                            return
                                        try:
                                            t=float(self.matchThresholdEdit.text())
                                        except:
                                            t=None
    #                                    if t[1]:
    #                                        if score>t[0]:
    #                                            print(score)
    #                                            QMessageBox.warning(self, "ERROR", "Couldn't find an appropriate match!")
    #                                            self.__changeImage()
    #                                            return
                                        if imageObj==self.gvLeft:
                                            otherObj=self.gvRight
                                        else:
                                            otherObj=self.gvLeft
                                        # check projection error first!
                                        self.targetPosition=[]
                                        self.pairedTarget=True
                                        if  imageObj==self.gvLeft:
                                            self.targetPosition.append(QPointF(clickLoc.x(), clickLoc.y()))
                                            self.targetPosition.append(QPointF(point_c[0][0], point_c[0][1]))
                                            points=str(clickLoc.x())+","+str(clickLoc.y())+","+str(point_c[0][0])+","+str(point_c[0][1])
                                        else:
                                            self.targetPosition.append(QPointF(point_c[0][0], point_c[0][1]))
                                            self.targetPosition.append(QPointF(clickLoc.x(), clickLoc.y()))
                                            points=str(point_c[0][0])+","+str(point_c[0][1])+","+str(clickLoc.x())+","+str(clickLoc.y())
                                        self.calculate('point')
                                        if t:
                                            if self.targetStereoData[1]>t:
                                                QMessageBox.warning(self, "ERROR", "Couldn't find an appropriate match!")
                                                self.__changeImage()
                                                self.computeMatchBox.setChecked(False)
                                                return
                                        # crate mark for other side
                                        self.theOtherTarget = otherObj.addMark(QPoint(point_c[0][0], point_c[0][1]), style=style, color=col,
                                                  size=1.0, thickness=1.0, alpha=255, selectThickness=self.selThickness,  selectColor=self.selColor)
                                        self.theOtherTarget.addLabel(str(self.currentTarget)+" "+spcLabel, color=col, offset=self.textOffset, name='tnumber',  size=self.guiSettings['LabelTextSize'])
                                        if not self.labelCheck.isChecked():
                                            self.theOtherTarget.hideLabels(None)
                                        self.pointMarks.update({marker:[self.currentTarget,  imageObj]})
                                        # and your twin too!

                                        if imageObj==self.gvLeft:
                                            self.activeMark [self.gvLeft]=marker
                                            self.activeMark [self.gvRight]=self.theOtherTarget
                                            self.pointMarks.update({self.theOtherTarget:[self.currentTarget,  self.gvRight]})
                                        else:
                                            self.activeMark [self.gvLeft]=self.theOtherTarget
                                            self.activeMark [self.gvRight]=marker
                                            self.pointMarks.update({self.theOtherTarget:[self.currentTarget,  self.gvLeft]})
                                        self.theOtherTarget=None
                                        tClass=self.spcButtons[self.spcInd].text()
                                        dt=datetime.now(timezone.utc)
                                        self.dataDB.dbExec("INSERT INTO targets (project, deployment_ID,frame_number, target_number, species_group, annotator, time_stamp)  "+
                                        "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentTarget)+",'"+sqlQuote(tClass)+"','"+sqlQuote(self.annotator)+"','"+dt.strftime(self.timestamp_format)+"')")
                                        self.dataDB.dbExec("INSERT INTO points (project, deployment_ID,frame_number, target_number, point_label, LX, LY, RX, RY, X,Y,Z, range, error)  "+
                                        "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentTarget)+",'range_to_target',"+points+","+str(self.targetStereoData[2])+","+
                                        str(self.targetStereoData[3])+","+str(self.targetStereoData[4])+","+str(self.targetStereoData[0])+","+str(self.targetStereoData[1])+")")
                                        self.pairPoints=[]

                                        if len(self.linkData)>0:
                                            self.dataDB.dbExec("UPDATE targets SET target_link = "+str(self.linkData[1])+
                                            " WHERE frame_number = "+self.frameBox.text()+" AND target_number ="+str(self.currentTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                                            self.linkData=[]
                                            self.linkBtn.setChecked(False)
                                        targetLabel=str(self.currentTarget)+" r = "+str(round(self.targetStereoData[0], 2))+"  e = "+str(round(self.targetStereoData[1], 2))
                                        if self.guiSettings['ShowClassOnLabel']=='true':
                                            targetLabel=targetLabel+' '+tClass
                                        self.activeMark[self.gvLeft].setLabelText('tnumber',targetLabel)
                                        if not self.labelCheck.isChecked():
                                            self.activeMark[self.gvLeft].hideLabels(None)
                                        if self.showDataCheck.isChecked():
                                            self.datadlg.refreshView()
                                        self.startFishTail()
                                        return




                                    self.pairPoints.append([imageObj, clickLoc.x(), clickLoc.y()])
                                    self.pairedTarget=False
                                    # active mark stuff
                                    self.activeMark [self.gvLeft]=None
                                    self.activeMark [self.gvLeft]=None
                                    self.theOtherTarget=marker
                                    if self.fishGuideActive():
                                        # head in the left image done, now the same point in the right one
                                        self.fishStep=1
                                        self.updateFishGuide()
                                else:# this the second point of the pair
                                    if imageObj==self.gvLeft:
                                        self.activeMark [self.gvLeft]=marker
                                        self.activeMark [self.gvRight]=self.theOtherTarget
                                        self.theOtherTarget=None
                                    else:
                                        self.activeMark [self.gvLeft]=self.theOtherTarget
                                        self.activeMark [self.gvRight]=marker
                                        self.theOtherTarget=None

                                    self.targetPosition=[]
                                    self.pairedTarget=True
                                    if  imageObj==self.gvLeft:
                                        self.targetPosition.append(QPointF(clickLoc.x(), clickLoc.y()))
                                        self.targetPosition.append(QPointF(self.pairPoints[0][1], self.pairPoints[0][2]))
                                        points=str(clickLoc.x())+","+str(clickLoc.y())+","+str(self.pairPoints[0][1])+","+str(self.pairPoints[0][2])
                                    else:
                                        self.targetPosition.append(QPointF(self.pairPoints[0][1], self.pairPoints[0][2]))
                                        self.targetPosition.append(QPointF(clickLoc.x(), clickLoc.y()))
                                        points=str(self.pairPoints[0][1])+","+str(self.pairPoints[0][2])+","+str(clickLoc.x())+","+str(clickLoc.y())
                                    tClass=self.spcButtons[self.spcInd].text()
                                    self.calculate('point')
                                    dt=datetime.now(timezone.utc)
                                    self.dataDB.dbExec("INSERT INTO targets (project, deployment_ID,frame_number, target_number, species_group, annotator, time_stamp)  "+
                                    "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentTarget)+",'"+sqlQuote(tClass)+"','"+sqlQuote(self.annotator)+"','"+dt.strftime(self.timestamp_format)+"')")
                                    self.dataDB.dbExec("INSERT INTO points (project, deployment_ID,frame_number, target_number, point_label, LX, LY, RX, RY, X,Y,Z, range, error)  "+
                                    "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentTarget)+",'range_to_target',"+points+","+str(self.targetStereoData[2])+","+
                                    str(self.targetStereoData[3])+","+str(self.targetStereoData[4])+","+str(self.targetStereoData[0])+","+str(self.targetStereoData[1])+")")
                                    self.pairPoints=[]
                                    if len(self.linkData)>0:
                                        self.dataDB.dbExec("UPDATE targets SET target_link = "+str(self.linkData[1])+
                                        " WHERE frame_number = "+self.frameBox.text()+" AND target_number ="+str(self.currentTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                                        self.linkData=[]
                                        self.linkBtn.setChecked(False)

                                    targetLabel=str(self.currentTarget)+" r = "+str(round(self.targetStereoData[0], 2))+"  e = "+str(round(self.targetStereoData[1], 2))
                                    if self.guiSettings['ShowClassOnLabel']=='true':
                                        targetLabel=targetLabel+' '+tClass
                                    self.activeMark[self.gvLeft].setLabelText('tnumber',targetLabel)
                                    if not self.labelCheck.isChecked():
                                        self.activeMark[self.gvLeft].hideLabels(None)
                                    if self.showDataCheck.isChecked():
                                        self.datadlg.refreshView()
                                        ##########
                                    self.pairPoints=[]
                                    self.startFishTail()
                                        
                            else:# non-matched target
                                #set active mark for zooming
                                if imageObj==self.gvLeft:
                                    self.activeMark [self.gvLeft]=marker
                                    self.activeMark [self.gvRight]=None
                                else:
                                    self.activeMark [self.gvLeft]=None
                                    self.activeMark [self.gvRight]=marker
                                # set selection
                                if  imageObj==self.gvLeft:
                                    points=str(clickLoc.x())+","+str(clickLoc.y())+",NULL,NULL"
                                else:
                                    points="NULL,NULL,"+str(clickLoc.x())+","+str(clickLoc.y())
                                tClass=self.spcButtons[self.spcInd].text()
                                dt=datetime.now(timezone.utc)
                                if self.spcInd!=None:
                                    self.dataDB.dbExec("INSERT INTO targets (project, deployment_ID,frame_number, target_number, species_group,annotator, time_stamp)  "+
                                    "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentTarget)+",'"+sqlQuote(tClass)+"','"+sqlQuote(self.annotator)+"','"+dt.strftime(self.timestamp_format)+"')")
                                    self.dataDB.dbExec("INSERT INTO points (project, deployment_ID,frame_number, target_number, point_label, LX, LY, RX, RY)  "+
                                    "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentTarget)+",'single_image_mark',"+points+")")
                                    self.pairedTarget=False
                                    if self.showDataCheck.isChecked():
                                        self.datadlg.refreshView()
                                    # add to speices in grid if grid is activated
                                    if self.gridCheck.isChecked():
                                        self.speciesInGrid.add(self.spcButtons[self.spcInd].text())
                            self.pointMarks.update({marker:[self.currentTarget,  imageObj]})
                            # the frame has a target now
                            self.updateTimelineMarks()
                self.incrementCounters()
            except:
                self.showError()
            
    def deleteSelMark(self):
        if not self.recordBtn.isChecked():
            # outside Record the marks are read only
            return
        if len(self.__selectedItems)>0:
            item =self.__selectedItems[0]# it it is a pair, grab just one
            reply=QMessageBox.warning(self, "WARNING", "Sure you want to delete the mark(s)?",  QMessageBox.Yes, QMessageBox.No)
            if reply==QMessageBox.No:
                return

            for i in self.__selectedItems:
                i.setSelected(False)
            self.__selectedItems=[]
            if item in self.pointMarks:
                target=self.pointMarks[item][0]
                if target in self.linkData:
                    if self.linkData[1]==target:
                        self.linkData=[]
                self.dataDB.dbExec("DELETE FROM lines WHERE frame_number = "+self.frameBox.text()+" AND target_number = "+str(target)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                self.dataDB.dbExec("DELETE FROM points WHERE frame_number = "+self.frameBox.text()+" AND target_number = "+str(target)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                self.dataDB.dbExec("DELETE FROM targets WHERE frame_number = "+self.frameBox.text()+" AND target_number = "+str(target)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
            elif item in self.boxMarks:
                boxTarget=self.boxMarks[item][0]
                self.dataDB.dbExec("DELETE FROM bounding_boxes WHERE frame_number = "+self.frameBox.text()+" AND target_number = "+str(boxTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
            self.__changeImage()
            self.measurementsDock.refresh()
                # zoom back if there are any active targets in either frame
        self.incrementCounters()

    def fishGuideActive(self):
        '''
        The guided fish marking runs while recording stereo targets with a calibration: the head
        and then the tail are clicked in the left image and then in the right one, and the
        length is saved without pressing Measure Target.
        '''
        return (self.recordBtn.isChecked() and self.stereoRadio.isChecked() and not self.measureBtn.isChecked()
                and not self.trainBtn.isChecked() and getattr(self, 'mode', None)=='stereo')

    def fishImage(self):
        # the image waiting for the next click of the fish being marked
        if self.fishStep in (1, 3):
            return self.gvRight
        return self.gvLeft

    def updateFishGuide(self, *args):
        '''
        updateFishGuide dims the image that isn't waiting for a click and says in the status bar
        what to click next.
        '''
        if not self.fishGuideActive():
            self.fishStep=0
            self.gvLeft.setDimmed(False)
            self.gvRight.setDimmed(False)
            self.statusBar.clearMessage()
            return
        self.gvLeft.setDimmed(self.fishImage()!=self.gvLeft)
        self.gvRight.setDimmed(self.fishImage()!=self.gvRight)
        messages=['Fish: Shift+click the head in the LEFT image (a plain click only counts the fish).',
                  'Fish: click the same point of the head in the RIGHT image. Esc cancels.',
                  'Fish: click the tail in the LEFT image. Esc keeps the fish without a length.',
                  'Fish: click the same point of the tail in the RIGHT image. Esc keeps the fish without a length.']
        self.statusBar.showMessage(messages[self.fishStep])

    def startFishTail(self):
        '''
        startFishTail is called when the head of a fish has been marked in both images: the tail
        comes next, left image first.
        '''
        if not self.fishGuideActive():
            return
        self.fishTarget=self.currentTarget
        self.fishHead=[QPointF(self.targetPosition[0]), QPointF(self.targetPosition[1])]
        self.fishHeadMarks=[self.activeMark[self.gvLeft], self.activeMark[self.gvRight]]
        self.fishLines={}
        self.fishStep=2
        self.updateFishGuide()

    def addTailPoint(self, imageObj, clickLoc, auto=False):
        '''
        addTailPoint takes the tail of the fish: left image first, then the right one (found by
        Auto Match when it is ticked). With both, the length is computed and saved.
        '''
        tail=QPointF(clickLoc.x(), clickLoc.y())
        head=self.fishHead[0] if imageObj==self.gvLeft else self.fishHead[1]
        if QLineF(head, tail).length()<1:
            QMessageBox.warning(self, "ERROR", "The tail must be away from the head.")
            return
        self.fishLines[imageObj]=imageObj.addDimensionLine(head, tail, taillength=self.guiSettings['MeasureLineTailLength'],
                thickness=self.guiSettings['MeasureLineWidth'], color=self.guiSettings['TargetLineColor'])
        self.lineMarks.update({self.fishLines[imageObj]:[self.fishTarget, imageObj]})
        if imageObj==self.gvRight:
            self.saveFishLength(auto)
            return
        self.fishStep=3
        self.updateFishGuide()
        if self.computeMatchBox.isChecked():
            point=ny.array([[tail.x(), tail.y()]])
            state, point_c, score=self.stereoComp.computeMatch(self.gvLeft.image.enhancedData, self.gvRight.image.enhancedData, point)
            if state:
                self.addTailPoint(self.gvRight, QPointF(point_c[0, 0], point_c[0, 1]), auto=True)
            else:
                QMessageBox.warning(self, "ERROR", score+". Click the tail in the right image.")

    def saveFishLength(self, auto=False):
        '''
        saveFishLength computes the fish length from its head and tail in both images and saves
        it as a line of the fish's target, like Measure Target does.
        '''
        lineL, lineR=self.fishLines[self.gvLeft], self.fishLines[self.gvRight]
        self.activeLine[self.gvLeft]=lineL
        self.activeLine[self.gvRight]=lineR
        self.calculate('line')
        self.activeLine[self.gvLeft]=None
        self.activeLine[self.gvRight]=None
        if auto:
            try:
                t=float(self.matchThresholdEdit.text())
            except:
                t=None
            if t and self.targetStereoData[2]>t:
                # a poor automatic match: let the user click the tail
                del self.lineMarks[lineR]
                self.gvRight.removeItem(lineR)
                del self.fishLines[self.gvRight]
                QMessageBox.warning(self, "ERROR", "Couldn't find an appropriate match! Click the tail in the right image.")
                return
        label=self.measurementBox.currentText()
        values=[str(v) for v in self.targetStereoData]
        self.keepLineName(self.fishTarget, label)
        # one line per measurement type and target
        self.dataDB.dbExec("DELETE FROM lines WHERE frame_number = "+self.frameBox.text()+" AND target_number ="+str(self.fishTarget)+
            " AND line_label='"+label+"' AND deployment_ID='"+sqlQuote(self.deployment)+"'")
        self.dataDB.dbExec("INSERT INTO lines (project, deployment_ID,frame_number, target_number, line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2, X1, Y1, Z1, X2,Y2, Z2, Length, Error)  "+
            "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.fishTarget)+",'"+label+"',"+
            ",".join(values[3:17])+","+values[0]+","+values[2]+")")
        lineL.addLabel(self.fishHead[0], label[0:3]+" = "+str(round(self.targetStereoData[0], 2))+" e = "+str(round(self.targetStereoData[2], 2)),
                color=self.guiSettings['TargetLineColor'], size=self.guiSettings['LabelTextSize'])
        if not self.labelCheck.isChecked():
            lineL.hideLabels(None)
        self.separateLabels(self.fishHeadMarks[0], lineL)
        self.separateLabels(self.fishHeadMarks[1], lineR)
        self.currentTarget=self.fishTarget
        self.fishStep=0
        self.fishLines={}
        self.updateFishGuide()
        name=self.nameMeasurement(self.fishTarget, label)
        self.statusBar.showMessage(name+': '+label+' '+str(round(self.targetStereoData[0], 2))+' cm saved. '+
                self.statusBar.currentMessage())
        if self.showDataCheck.isChecked():
            self.datadlg.refreshView()

    def keepLineName(self, target, label):
        # remember the name of a measurement about to be replaced, to offer it again
        query=self.dataDB.dbQuery("SELECT name FROM lines WHERE deployment_id='"+sqlQuote(self.deployment)+"' AND frame_number="+self.frameBox.text()+
            " AND target_number="+str(target)+" AND line_label='"+label+"'")
        for name, in query:
            if name:
                self.previousLineName=(self.frameBox.text(), target, label, name)

    def defaultMeasurementName(self, target, label):
        '''
        The name offered for a new measurement: its old name when it is measured again, else the
        name of another measurement of the same fish, else the fish's species followed by the
        next free number in the deployment (Sargus 1, Sargus 2, ...).
        '''
        previous=getattr(self, 'previousLineName', None)
        self.previousLineName=None
        if previous and previous[:3]==(self.frameBox.text(), target, label):
            return previous[3]
        query=self.dataDB.dbQuery("SELECT name FROM lines WHERE deployment_id='"+sqlQuote(self.deployment)+"' AND frame_number="+self.frameBox.text()+
            " AND target_number="+str(target)+" AND line_label<>'"+label+"'")
        for name, in query:
            if name:
                return name
        species=None
        query=self.dataDB.dbQuery("SELECT species_group FROM targets WHERE deployment_id='"+sqlQuote(self.deployment)+"' AND frame_number="+self.frameBox.text()+
            " AND target_number="+str(target))
        for species, in query:
            pass
        species=species or 'Fish'
        numbers=[0]
        query=self.dataDB.dbQuery("SELECT name FROM lines WHERE deployment_id='"+sqlQuote(self.deployment)+"'")
        for name, in query:
            if name and name.startswith(species+' ') and name[len(species)+1:].isdigit():
                numbers.append(int(name[len(species)+1:]))
        return species+' '+str(max(numbers)+1)

    def nameMeasurement(self, target, label):
        '''
        nameMeasurement asks the name of the measurement just saved and stores it. Cancel keeps
        the name offered. Names can be changed later in the Measurements panel.
        '''
        default=self.defaultMeasurementName(target, label)
        name, ok=QInputDialog.getText(self, 'Measurement name', 'Name of this '+label+' measurement:', QLineEdit.EchoMode.Normal, default)
        name=name.strip() if ok and name.strip() else default
        self.dataDB.dbExec("UPDATE lines SET name='"+sqlQuote(name)+"' WHERE deployment_id='"+sqlQuote(self.deployment)+"' AND frame_number="+
            self.frameBox.text()+" AND target_number="+str(target)+" AND line_label='"+label+"'")
        self.measurementsDock.refresh()
        return name

    def separateLabels(self, mark, line):
        '''
        separateLabels keeps a target label and its length label apart and inside the view. The
        target label goes beyond the mark (away from the line), else above or below it; the length
        label beyond the far end of the line, else below or above its middle. The first pair of
        places that fits in the view without overlapping is used.
        '''
        if mark is None or line is None:
            return
        view=line.view
        markLabels=mark.getLabelsFromName('tnumber')
        lineLabels=list(line.labels)
        markPos=mark.markItem.pos()
        p1, p2=line.p1(), line.p2()
        # the line end away from the mark
        if QLineF(markPos, p1).length()>QLineF(markPos, p2).length():
            far, near=p1, p2
        else:
            far, near=p2, p1
        middle=(p1+p2)/2
        farRight=far.x()>=near.x()
        # (anchor, horizontal and vertical alignment, offset in screen pixels)
        markPlaces=[(markPos, 'right' if farRight else 'left', 'center', QPointF(-8 if farRight else 8, 0)),
                    (markPos, 'center', 'bottom', QPointF(0, -10)),
                    (markPos, 'center', 'top', QPointF(0, 10))]
        linePlaces=[(far, 'left' if farRight else 'right', 'center', QPointF(8 if farRight else -8, 0)),
                    (middle, 'center', 'top', QPointF(0, 10)),
                    (middle, 'center', 'bottom', QPointF(0, -10))]
        scale=1.0/view.transform().m11()
        def place(labels, where):
            for label in labels:
                label.position, label.halign, label.valign, label.offset=where
                label.setPos(label.position, scale)
        def screenRect(label):
            return label.deviceTransform(view.viewportTransform()).mapRect(label.boundingRect())
        viewRect=QRectF(view.viewport().rect())
        for markPlace in markPlaces:
            for linePlace in linePlaces:
                place(markLabels, markPlace)
                place(lineLabels, linePlace)
                markRects=[screenRect(label) for label in markLabels]
                lineRects=[screenRect(label) for label in lineLabels]
                if (all(viewRect.contains(r) for r in markRects+lineRects) and
                        not any(a.intersects(b) for a in markRects for b in lineRects)):
                    view.viewport().update()
                    return
        # nothing fits the view: keep them apart
        place(markLabels, markPlaces[0])
        place(lineLabels, linePlaces[0])
        view.viewport().update()

    def separateTargetLabels(self, target):
        # separateLabels for the target's mark and first line in each image
        for imageObj in [self.gvLeft, self.gvRight]:
            mark=next((m for m, info in self.pointMarks.items() if info[0]==target and info[1]==imageObj), None)
            line=next((l for l, info in self.lineMarks.items() if info[0]==target and info[1]==imageObj), None)
            self.separateLabels(mark, line)

    def imageUnClick(self, imageObj, clickLoc, button, modifier):
        # a line drawn in one image with Measure Target gets its hints in the other one
        try:
            self.handleImageRelease(imageObj, clickLoc, button, modifier)
        finally:
            self.updateEpipolar()

    def handleImageRelease(self, imageObj, clickLoc, button, modifier):

        if self.rubberBanding:
            if self.makeBoxes:
                rubberbandObj = imageObj.endRubberBand()
                #set minimum size in pix (makes it easer to delete bad regions)
                if rubberbandObj.width()<20.:
                    rubberbandObj.setWidth(20.)
                if rubberbandObj.height()<20.:
                    rubberbandObj.setHeight(20.)
                #  add a polygon item showing the RB selection
                boxObj = imageObj.addPolygon(rubberbandObj,color=self.spcColors[self.spcInd], thickness=self.guiSettings['BoxLineThickness'], selectable=True,
                        selectThickness=4.0, selectColor=self.selColor)
                # figure out bbox target number
                query = self.dataDB.dbQuery("SELECT max(target_number) FROM bounding_boxes WHERE frame_number = "+self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                max_target, =query.first()
                if max_target!=None:
                    self.currentBBoxTarget=int(max_target)+1
                else:# no targets yet for this frame
                    self.currentBBoxTarget=1
                self.boxMarks.update({boxObj:[self.currentBBoxTarget,  imageObj]})
                #  and add a label - polygon labels are attached to the vertices and the first
                #  argument is the index of the vertex you want to attach the label to. For
                #  rubber band boxes, the verts are always ordered clockwise from the upper left
                spcLabel=''
                if self.guiSettings['LabelSpeciesParam']>0:
                    spcLabel=self.spcButtons[self.spcInd].text()
                    if len(spcLabel)>self.guiSettings['LabelSpeciesParam']:
                        spcLabel=spcLabel[0:self.guiSettings['LabelSpeciesParam']]

                boxObj.addLabel(0, str(self.currentBBoxTarget)+" "+spcLabel, size=self.guiSettings['LabelTextSize'],  color=self.spcColors[self.spcInd])
                BoxCoords=rubberbandObj.toRect()
                self.rubberBanding = False
                # this would be where we write the results
                #print("write stuff")
                if imageObj==self.gvLeft:
                    image_file_name=self.LFile
                    cam='left'
                else:
                    image_file_name=self.RFile
                    cam='right'
                width=imageObj.image.enhancedData.shape[1]
                height=imageObj.image.enhancedData.shape[0]
                self.dataDB.dbExec("INSERT INTO bounding_boxes (project, deployment_ID,frame_number, target_number, species_group, camera_id, image_file_name, origin_x,origin_y,width, height, frame_width, frame_height,annotator)"+
                                                    " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentBBoxTarget)+",'"+sqlQuote(self.spcButtons[self.spcInd].text())+"','" +cam+"',"
                                                    "'"+sqlQuote(image_file_name)+"', "+str(BoxCoords.x())+", "+str(BoxCoords.y())+", "+str(BoxCoords.width())+", "+str(BoxCoords.height())+","+str(width)+","+str(height)+",'"+sqlQuote(self.annotator)+"')")
                return# we are just rubberbanding, no need to do anythin else

            dimLine = imageObj.endDimensionLine()
            self.rubberBanding = False
            self.activeLine[imageObj] = dimLine
            if self.measureBtn.isChecked():
                if not self.activeLine[self.gvLeft]==None and not self.activeLine[self.gvRight]==None:
                    col=self.guiSettings['TargetLineColor']
                    # stereo triangulation
                    self.calculate('line')
                    # check to see alignment of target and line

                    line=self.activeLine[self.gvLeft].getLine()
                    self.activeLine[self.gvLeft].addLabel(line.p1(), self.measurementBox.currentText()[0:3]+" = "+str(round(self.targetStereoData[0], 2))+" e = "+str(round(self.targetStereoData[2], 2)), color=col,  size=self.guiSettings['LabelTextSize'])


                    if not self.labelCheck.isChecked():
                        self.activeLine[self.gvLeft].hideLabels(None)
                    self.separateTargetLabels(self.currentTarget)

                    self.activeLine[self.gvLeft]=None
                    self.activeLine[self.gvRight]=None
                    # write results
                    #[length, range, LHX, LHY,LTX,LTY, RHX, RHY,RTX,RTY,plhx, plhy, plhz,pltx,plty, pltz]
                    if self.measureBtn.isChecked():
                        if self.pairedTarget:
                            Length = str(self.targetStereoData[0])
                            Error = str(self.targetStereoData[2])
                            LHX = str(self.targetStereoData[3])
                            LHY = str(self.targetStereoData[4])
                            LTX = str(self.targetStereoData[5])
                            LTY = str(self.targetStereoData[6])
                            RHX = str(self.targetStereoData[7])
                            RHY = str(self.targetStereoData[8])
                            RTX = str(self.targetStereoData[9])
                            RTY = str(self.targetStereoData[10])                            
                            HX = str(self.targetStereoData[11])
                            HY = str(self.targetStereoData[12])
                            HZ = str(self.targetStereoData[13])
                            TX = str(self.targetStereoData[14])
                            TY = str(self.targetStereoData[15])
                            TZ = str(self.targetStereoData[16])
                            self.dataDB.dbExec("INSERT INTO lines (project, deployment_ID,frame_number, target_number, line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2, X1, Y1, Z1, X2,Y2, Z2, Length, Error)  "+
                                        "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentTarget)+",'"+self.measurementBox.currentText()+"',"+LHX+","+LHY+","+LTX+","+LTY+","+RHX+","+RHY+
                                        ","+RTX+","+RTY+","+HX+","+HY+","+HZ+","+TX+","+TY+","+TZ+","+Length+","+Error+")")
                            self.nameMeasurement(self.currentTarget, self.measurementBox.currentText())
                        self.measureBtn.setChecked(False)

                else: # line is drawn on only one side
                    if self.computeMatchBox.isChecked():
                        #get the points
                        if not self.activeLine[self.gvLeft]==None: #we've clicked on the left' - search right for match
                            im1=self.gvLeft.image.enhancedData
                            im2=self.gvRight.image.enhancedData
                            line=self.activeLine[self.gvLeft].getLine()
                        else:
                            im2=self.gvLeft.image.enhancedData
                            im1=self.gvRight.image.enhancedData
                            line=self.activeLine[self.gvRight].getLine()
                        #get auto match

                        point1=ny.array([[line.x1(), line.y1()]])
                        point2=ny.array([[line.x2(), line.y2()]])
                        state,  point1_c, score=self.stereoComp.computeMatch(im1, im2, point1)
                        if not state:
                            QMessageBox.warning(self, "ERROR",score)
                            return
                        else:
                            state,  point2_c, score=self.stereoComp.computeMatch(im1, im2, point2)
                            if not state:
                                QMessageBox.warning(self, "ERROR",score)
                                return

                        #draw match line
                        stPoint=QPointF(point1_c[0, 0], point1_c[0, 1])
                        endPoint=QPointF(point2_c[0, 0], point2_c[0, 1])
                        if not self.activeLine[self.gvLeft]==None: #we've clicked on the left' - draw line on right
                            
                            lineObjs=self.gvRight.addDimensionLine(stPoint,endPoint, taillength=self.guiSettings['MeasureLineTailLength'],
                            thickness=self.guiSettings['MeasureLineWidth'],  color=self.guiSettings['TargetLineColor'])
                            self.lineMarks.update({lineObjs:[self.currentTarget,  self.gvRight]})
                            self.activeLine[ self.gvRight] = lineObjs
                        else:
                            lineObjs=self.gvLeft.addDimensionLine(stPoint,endPoint, taillength=self.guiSettings['MeasureLineTailLength'],
                            thickness=self.guiSettings['MeasureLineWidth'],  color=self.guiSettings['TargetLineColor'])
                            self.lineMarks.update({lineObjs:[self.currentTarget,  self.gvLeft]})
                            self.activeLine[ self.gvLeft] = lineObjs
                        self.rubberBanding=False
                        # stereo triangulation
                        self.calculate('line')
                        self.targetStereoData[2]
                        try:
                            t=float(self.matchThresholdEdit.text())
                        except:
                            t=None
                        if t:
                            if self.targetStereoData[2]>t:
                                QMessageBox.warning(self, "ERROR", "Couldn't find an appropriate match!")
                                self.computeMatchBox.setChecked(False)
                                self.__changeImage()
                                return
                                            # check to see alignment of target and line
                        if self.measureBtn.isChecked():
                            for obj in [self.gvLeft,  self.gvRight]:
                                # get position of current target
                                point=None
                                for mark,  bits in self.pointMarks.items():
                                    if bits[0]==self.currentTarget and bits[1]==obj:
                                        point=mark.pos()
                                line=self.activeLine[obj].getLine()
                                if not point:
                                    return
                        line=self.activeLine[self.gvLeft].getLine()
                        targetLabel=self.measurementBox.currentText()+" = "+str(round(self.targetStereoData[0], 2))+" e = "+str(round(self.targetStereoData[2], 2))
#                        if self.showClassInLabel:
#                            targetLabel=targetLabel+'\n'+tClass
                        self.activeLine[self.gvLeft].addLabel(line.p1(), targetLabel, color=self.guiSettings['TargetLineColor'],  size=self.guiSettings['LabelTextSize'])


                        if not self.labelCheck.isChecked():
                            self.activeLine[self.gvLeft].hideLabels(None)
                        self.separateTargetLabels(self.currentTarget)

                        self.activeLine[self.gvLeft]=None
                        self.activeLine[self.gvRight]=None
                        # write results
                        #[length, range, LHX, LHY,LTX,LTY, RHX, RHY,RTX,RTY,plhx, plhy, plhz,pltx,plty, pltz]
                        if self.measureBtn.isChecked():
                            if self.pairedTarget:
                                Length = str(self.targetStereoData[0])
                                Error = str(self.targetStereoData[2])
                                LHX = str(self.targetStereoData[3])
                                LHY = str(self.targetStereoData[4])
                                LTX = str(self.targetStereoData[5])
                                LTY = str(self.targetStereoData[6])
                                RHX = str(self.targetStereoData[7])
                                RHY = str(self.targetStereoData[8])
                                RTX = str(self.targetStereoData[9])
                                RTY = str(self.targetStereoData[10])                            
                                HX = str(self.targetStereoData[11])
                                HY = str(self.targetStereoData[12])
                                HZ = str(self.targetStereoData[13])
                                TX = str(self.targetStereoData[14])
                                TY = str(self.targetStereoData[15])
                                TZ = str(self.targetStereoData[16])
                                self.dataDB.dbExec("INSERT INTO lines (project, deployment_ID,frame_number, target_number, line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2, X1, Y1, Z1, X2,Y2, Z2, Length, Error)  "+
                                            "VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+","+str(self.currentTarget)+",'"+self.measurementBox.currentText()+"',"+LHX+","+LHY+","+LTX+","+LTY+","+RHX+","+RHY+
                                            ","+RTX+","+RTY+","+HX+","+HY+","+HZ+","+TX+","+TY+","+TZ+","+Length+","+Error+")")
                                self.nameMeasurement(self.currentTarget, self.measurementBox.currentText())
                            self.measureBtn.setChecked(False)


                    if self.showDataCheck.isChecked():
                        self.datadlg.refreshView()
        self.incrementCounters()
                        
    def incrementCounters(self):
        self.spcInd=None
        for btn in self.spcButtons:
            if btn.isChecked():
                self.spcInd=self.spcButtons.index(btn)
                break
        if self.spcInd is not None:
            species_selected=self.spcButtons[self.spcInd].text()
            query = self.dataDB.dbQuery("SELECT count(*) FROM targets WHERE species_group='"+sqlQuote(species_selected)+
            "' AND frame_number="+self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
            count, =query.first()

            countstr="targets = "+count
            self.countInFrameLabel.setText(countstr)

    def clearValues(self):
        if self.metadataCheckBox.isChecked():
            if not self.metadataStickyBox.isChecked():# reset the boxes
                self.clearAutoExclusiveRadioBtnBoxes()
                for box in self.metadataCheckBoxes:
                    if box.isVisible():
                        box.setChecked(False)
            for box in self.metadataLineEdits:
                if box.isVisible():
                    box.setText('')
        if self.guiSettings['RetainSpeciesSelection'].lower()=='clear':
            for btn in self.spcButtons:
                btn.setChecked(False)
#        self.frameComment=''

    def getFrame(self):
        if self.deployment==None:
            return
        # the box holds the number that was typed: until the frame is shown it must say which
        # frame is on screen, as that is the frame the data being saved belongs to
        typed=self.frameBox.text()
        self.frameBox.setText(str(self.leftImageFrames[self.imageSlider.value()]))
        try:
            frame=int(typed)
        except ValueError:
            QMessageBox.warning(self, "ERROR", "The frame number must be a whole number.")
            return
        if frame>self.maxFr:
            QMessageBox.warning(self, "ERROR", "Max frame number is "+str(self.maxFr))
            return
        if frame<self.minFr:
            QMessageBox.warning(self, "ERROR", "Min frame number is "+str(self.minFr) )
            return
        if frame in self.leftImageDict:
            frameIndex=self.leftImageFrames.index(frame)
            self.changeFrame(frameIndex)
        else:
            QMessageBox.warning(self, "ERROR", "This frame number isn't in the image folder.")
            return

    def changeFrame(self, frameIndex):
        '''
        changeFrame shows the frame at the given slider position. While recording, the data of
        the frame being left is saved first, as when stepping with the arrow keys.
        '''
        if frameIndex==self.imageSlider.value():
            return
        if self.recordBtn.isChecked():
            self.writeFrameData()
            self.clearValues()
        self.imageSlider.setValue(frameIndex)

####################3. UTILITY FUNCTIONS AND CALCULATIONS ############################
    def getTargetComment(self):
        try:
            if self.currentTarget>0:
                query = self.dataDB.dbQuery("SELECT species_group, comment FROM targets WHERE frame_number = "+self.frameBox.text()+" and target_number ="+str(self.currentTarget)+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                species_group, comment=query.first()
                if species_group!=None:
                    targetClass=species_group
                    targetComment=comment

                dlg=commentdlg.CommentDlg(targetComment,  targetClass,  self.currentTarget)
                dlg.exec()
                targetComment=dlg.comment
                if not targetComment==None:
                    self.dataDB.dbExec("UPDATE targets SET comment = '"+sqlQuote(targetComment)+"' WHERE frame_number = "+self.frameBox.text()+" and target_number ="+str(self.currentTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
            else:
                QMessageBox.warning(self, "ERROR", "No Active Target!")
        except:
            self.showError()

    def getFrameComment(self):

        if self.frameCommentBtn.isChecked():
            self.frameCommentDlg.show()
        else:
            self.frameCommentDlg.hide()

    def goToLastFrame(self):
        frameIndex=None
        query = self.dataDB.dbQuery("SELECT max(frame_number) FROM targets WHERE deployment_id='"+sqlQuote(self.deployment)+"'")
        frame, = query.first()
        if frame!=None:
            #get my index from targets
            frameIndex=self.leftImageFrames.index(int(frame))
        else:
            query = self.dataDB.dbQuery("SELECT max(frame_number) FROM frame_metadata WHERE deployment_id='"+sqlQuote(self.deployment)+"'")
            frame, = query.first()
            if frame!=None:
                #get my index from targets
                frameIndex=self.leftImageFrames.index(int(frame))
                
        if frameIndex is not None:
            self.goToIndex(frameIndex)

    def stepFrame(self, direction, oneFrame):
        '''
        stepFrame goes one frame (oneFrame) or one sample step forward (direction 1) or back (-1). The Left and Right
        keys and the navigation buttons all come here.
        '''
        if self.measureBtn.isChecked():
            self.statusBar.showMessage('Finish the measurement, or press Esc, before changing frame.', 4000)
            return# dont advance frame while measurements are taking place
        frameIndex=self.imageSlider.value()
        try:
            sampleRate = float(self.sampleRateEdit.text())
        except ValueError:
            sampleRate = 1
        if sampleRate < 1:
            sampleRate = 1
        try:
            offset = float(self.rateOffsetEdit.text())
        except:
            offset = 0
        if oneFrame:
            targetIndex=frameIndex + direction
        else:
            #  one sample step
            targetIndex=int(round((float(frameIndex + direction*sampleRate-offset)) /
                            float(sampleRate)) * sampleRate)+offset
        #  goToIndex keeps the index inside the slider: the first frame (index 0) is reached by stepping as by the First button
        self.goToIndex(targetIndex)

    def goToIndex(self, targetIndex):
        '''
        goToIndex shows the frame at a slider position, as the arrow keys do: not while a measurement is taking
        place, inside the range of the slider, with the link data of a target dropped when the frame is more than
        one away, and with the data of the frame being left saved while recording (changeFrame).
        '''
        if self.noLoad:
            return
        if self.measureBtn.isChecked():
            self.statusBar.showMessage('Finish the measurement, or press Esc, before changing frame.', 4000)
            return
        targetIndex=int(targetIndex)
        #  clamp the image numbers to a valid range
        if targetIndex > self.imageSlider.maximum():
            targetIndex = self.imageSlider.maximum()
        if targetIndex < self.imageSlider.minimum():
            targetIndex = self.imageSlider.minimum()
        #  check for linked data, null out if more than one frame out
        if len(self.linkData)>0:
            if not (targetIndex - self.linkData[0]) in [0, 1]:
                self.linkData=[]
                self.linkBtn.setChecked(False)
        self.changeFrame(targetIndex)
        
    def editSpecies(self):
        dlg=editspeciesdlg.EditSpeciesDlg(self)
        dlg.goToTargetEvent.connect(self.changeSelectionFromTable)
        dlg.exec()
        self.__changeImage()
        self.measurementsDock.refresh()
    
    def changeSelectionFromTable(self, frame, target, zoom=None):
        frameIndex=self.leftImageFrames.index(frame)
        self.changeFrame(frameIndex)
        self.selectValueFromTable(frame, target, zoom)

    def selectValueFromTable(self, frame, target, zoom):
        if not target==None:
            for items in self.__selectedItems:
                items.setSelected(False)
            self.__selectedItems=[]
            self.activeMark [self.gvRight]=None
            self.activeMark [self.gvLeft]=None
            for item, info in self.pointMarks.items():
                if info[0]==target:
                    item.setSelected(True)
                    self.__selectedItems.append(item)
                    if info[1]==self.gvLeft:
                        self.activeMark [self.gvLeft]=item
                        if not zoom == None:
                            if zoom==0:
                                self.gvLeft.centerOnMark(self.activeMark[self.gvLeft])
                            else:
                                self.gvLeft.zoomToMark(self.activeMark[self.gvLeft], zoom)
                    else:
                        self.activeMark [self.gvRight]=item
                        if not zoom == None:
                            if zoom==0:
                                self.gvRight.centerOnMark(self.activeMark[self.gvRight])
                            else:
                                self.gvRight.zoomToMark(self.activeMark[self.gvRight],  zoom)
                        

    def selectValueFromImage(self):
        self.datadlg.setSelectedRowFromData( int(self.frameBox.text()), self.currentTarget)
        
    def uncheckCloseupWindowBox(self,  flag):
        if flag:
            self.closeupCheck.setChecked(False)
            
    def toggleMetadataCollection(self):
        if self.metadataCheckBox.isChecked():
            # enable metadata inputs
            for widget in self.metadataWidgets:
                widget.setEnabled(True)
        else:
            # disable metadata inputs
            for widget in self.metadataWidgets:
                widget.setEnabled(False)
            
            

    def toggleRecord(self):
        if self.deployment==None:
            QMessageBox.warning(self, "ERROR", "Please load a deployment.")
            self.recordBtn.setChecked(False)
            return
        if self.recordBtn.isChecked():
            self.stopPlay()
            self.imageSlider.setEnabled(False)
            self.playBtn.setEnabled(False)
            self.speciesDockWidget.show()
            if self.metadataCheckBox.isChecked():
                self.metadataDockWidget.show()
            # get the annotator now!
            dlg=annotatorDlg.AnnotatorDlg()
            dlg.exec()
            self.annotator=dlg.annotator
            self.frameCommentDlg=framecommentdlg.CommentDlg(self)
            self.frameCommentDlg.hide()
            # replace the read only marks with editable ones
            self.clearMarks()
            self.reloadData()
            for widget in self.recordEnableWidgets:
                if widget in [self.measureBtn,  self.measurementBox] and self.monoRadio.isChecked(): # dont enable widgets for mono mode
                    continue
                widget.setEnabled(True)
            self.showTools(self.recordOnlyWidgets, True)

                

        else:
            self.imageSlider.setEnabled(True)
            self.playBtn.setEnabled(True)
            #self.__changeImage()
            self.speciesDockWidget.hide()
            self.metadataDockWidget.hide()
            # deselect spc buttons
            for btn in self.spcButtons:
                btn.setChecked(False)
            #self.groupBoxView.hide()
            self.deSelect()
            self.clearMarks()
            self.showAnnotations()

            try:
                self.datadlg.hide()
            except:
                pass
                
            for widget in self.recordEnableWidgets:
                widget.setEnabled(False)
            self.showTools(self.recordOnlyWidgets, False)
        self.resizeEvent(None)


    def toggleTraining(self):
        if self.trainBtn.isChecked():
            # we want to do some bounding box stuff
            for widget in self.bboxEnableWidgets:
                widget.setEnabled(False)

            self.makeBoxes=True
            # remove all marks
            self.__changeImage()
        else:
            # we want to go back to normal operations
            self.makeBoxes=False
            for widget in self.bboxEnableWidgets:
                if widget==self.measureBtn and self.monoRadio.isChecked(): # no measurements in mono mode
                    continue
                widget.setEnabled(True)
            self.__changeImage()

    def stereoAvailable(self):
        '''
        stereoAvailable returns True if a stereo calibration is loaded. Otherwise it explains
        why 3D measurements are not possible and returns False.
        '''
        if getattr(self, 'mode', None)=='stereo':
            return True
        QMessageBox.warning(self, "ERROR", "3D measurements need a stereo calibration, but the profile of this deployment has no CalibrationFileName.\n\n"+
            "Put the calibration file in the SEBASTES/calibrations folder, set CalibrationFileName in the profile (Settings > Profiles) "+
            "and load the deployment again.")
        return False

    def toggleMeasure(self):
        if self.measureBtn.isChecked():
            if not self.stereoAvailable():
                self.measureBtn.setChecked(False)
                return
            if self.currentTarget==0:
                QMessageBox.warning(self, "ERROR", "You need to select a target first!")
                self.measureBtn.setChecked(False)
                return
            if not self.pairedTarget:
                QMessageBox.warning(self, "ERROR", "The selected target is marked in one image only, so it can't be measured.\n\n"+
                    "To create a stereo target, hold Shift (or tick Annotate > Stereo Targets Only) and click the fish in the left image, then in the right image. "+
                    "Then press Measure Target and draw the length in both images.")
                self.measureBtn.setChecked(False)
                return
                    # find line marks
            t=self.currentTarget
            query = self.dataDB.dbQuery("SELECT target_number FROM targets WHERE frame_number = "+self.frameBox.text()+" and target_number ="+str(self.currentTarget)+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
            target_number, = query.first()
            if target_number!=None:
                # clear out current length measurements
                self.keepLineName(self.currentTarget, self.measurementBox.currentText())
                self.dataDB.dbExec("DELETE FROM lines WHERE frame_number = "+self.frameBox.text()+" and target_number ="+str(self.currentTarget)+"  AND line_label='"+self.measurementBox.currentText()+"' AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                self.updateTimelineMarks()
                # reload frame
                            # get the zoom state
                if self.activeMark[self.gvLeft]:
                    lPoint=self.activeMark[self.gvLeft].mapToScene(self.activeMark[self.gvLeft].boundingRect().center())
                else:
                    lPoint=None
                if self.activeMark[self.gvRight]:
                    rPoint=self.activeMark[self.gvRight].mapToScene(self.activeMark[self.gvRight].boundingRect().center())
                else:
                    rPoint=None

                lZoom=self.gvLeft.zoomLevel
                rZoom=self.gvRight.zoomLevel

                # find the pair
                self.__changeImage()
                # zoom back
                if lPoint!=None:
                    self.gvLeft.zoomToPoint(lPoint, lZoom)
                if rPoint!=None:
                    self.gvRight.zoomToPoint(rPoint, rZoom)
            # first time measurement
            self.measureBtn.setChecked(True)
            self.pairedTarget=True
            self.currentTarget=t
#            groupItems=[]
            for i, j in self.pointMarks.items():
                if j[0]==self.currentTarget and i !=None:
                    i.setSelected(True)
                    self.activeMark[j[1]]=i
                    self.__selectedItems.append(i)
#                    groupItems.append(i)
#            for i in groupItems:
#                if i in self.lineMarks:
#                    self.garbage.append(self.lineMarks.pop(i))

    def toggleLink(self):
        if self.linkBtn.isChecked():
            self.linkData=[int(self.frameBox.text()),  self.currentTarget]
        else:
            self.linkData=[]

    def deleteLink(self):
            reply=QMessageBox.warning(self, "WARNING", "Sure you want to delete the target link for \ntarget "+str(self.currentTarget)+" and linked target "+self.targetLinkLabel.text()+"?",  QMessageBox.Yes, QMessageBox.No)
            if reply==QMessageBox.No:
                return
            self.linkData=[]
            self.dataDB.dbQuery("UPDATE targets set target_link=NULL WHERE frame_number = "+self.frameBox.text()+" and target_number="+str(self.currentTarget)+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
            self.targetLinkLabel.setText('')
                        
                        
    def metadataSelAction(self):

        self.sender().setAutoExclusive(False)
        if self.sender().isChecked():
            self.sender().setChecked(False)
            self.sender().setAutoExclusive(True)
            
    def writeCurrentFrame(self):
        pass

    def writeFrameData(self):
        try:
            if not self.recordBtn.isChecked():
                return
            # get the annotator business with commas
            current_tators=self.annotatorLabel.text()
            # get the current frame comment
            comment=self.frameCommentDlg.commentBox.toPlainText()

            # see if current frame is already in 
            query=self.dataDB.dbQuery("SELECT frame_number FROM FRAMES WHERE frame_number="+self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
            frame, =query.first()
            if frame:# already exists
                self.dataDB.dbExec("UPDATE frames SET comment='"+sqlQuote(comment)+"', annotator='"+sqlQuote(current_tators)+"' WHERE frame_number="+self.frameBox.text()+
                "  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
            else:
                dt=datetime.now(timezone.utc)
                self.dataDB.dbExec("INSERT INTO frames (project, deployment_ID, frame_number, frame_time, comment, annotator, time_stamp)"+
                    " VALUES('"+sqlQuote(self.activeProject)+"', '"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'"+self.dtString+"','"+sqlQuote(comment)+"','"+sqlQuote(current_tators)+"','"+dt.strftime(self.timestamp_format)+"')")
            if self.metadataCheckBox.isChecked():
                # now we write metadata
                self.dataDB.dbExec("DELETE FROM FRAME_METADATA WHERE frame_number="+self.frameBox.text()+" AND metadata_group='"+sqlQuote(self.metadataGroup)+"' AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                if 'ExclusiveRadioBox1' in self.metadataTypesDict:
                    for rBtn in self.radioBtnTags1:
                        if rBtn.isChecked():
                            mdt_tag=rBtn.text()
                            # write exclusive radio button 1
                            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project, deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value,annotator)"+
                            " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'"+sqlQuote(self.metadataGroup)+"','"+sqlQuote(mdt_tag)+"','"+sqlQuote(self.metadataTypesDict['ExclusiveRadioBox1'])+
                            "','Checked','"+sqlQuote(self.annotator)+"')")
                            break # we can do this caouse its autoexclusive!
                            
                if 'ExclusiveRadioBox2' in self.metadataTypesDict:
                    for rBtn in self.radioBtnTags2:
                        if rBtn.isChecked():
                            mdt_tag=rBtn.text()
                            # write exclusive radio button 1
                            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project, deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value, annotator)"+
                            " VALUES('"+sqlQuote(self.activeProject)+"', '"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'"+sqlQuote(self.metadataGroup)+"','"+sqlQuote(mdt_tag)+"','"+sqlQuote(self.metadataTypesDict['ExclusiveRadioBox2'])+
                            "','Checked','"+sqlQuote(self.annotator)+"')")
                            break # we can do this caouse its autoexclusive!
                                    
                    for rBtn in self.radioBtnTags3:
                        if rBtn.isChecked():
                            mdt_tag=rBtn.text()
                            # write exclusive radio button 1
                            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project, deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value,annotator)"+
                            " VALUES('"+sqlQuote(self.activeProject)+"', '"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'"+sqlQuote(self.metadataGroup)+"','"+sqlQuote(mdt_tag)+"','"+sqlQuote(self.metadataTypesDict['ExclusiveRadioBox3'])+
                            "','Checked','"+sqlQuote(self.annotator)+"')")
                            break # we can do this caouse its autoexclusive!
                            
                if 'LineEdit' in self.metadataTypesDict:
                    for i in list(range(len(self.metadataLineEdits))):
                        if self.metadataLineEditLabels[i].isVisible():
                            mdt_tag=self.metadataLineEditLabels[i].text()
                            mtd_val=self.metadataLineEdits[i].text()
                            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project, deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value, annotator)"+
                            " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'"+sqlQuote(self.metadataGroup)+"','"+sqlQuote(mdt_tag)+"','"+sqlQuote(self.metadataTypesDict['LineEdit'])+"','"+
                            sqlQuote(mtd_val)+"','"+sqlQuote(self.annotator)+"')")

                if 'CheckBox' in self.metadataTypesDict:
                    for i in list(range(len(self.metadataCheckBoxes))):
                        if self.metadataCheckBoxes[i].isVisible():
                            mdt_tag=self.metadataCheckBoxes[i].text()
                            if self.metadataCheckBoxes[i].isChecked():
                                mtd_val='Checked'
                            else:
                                mtd_val='Unchecked'
                            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project,deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value, annotator)"+
                            " VALUES('"+sqlQuote(self.activeProject)+"', '"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'"+sqlQuote(self.metadataGroup)+"','"+sqlQuote(mdt_tag)+"','"+sqlQuote(self.metadataTypesDict['CheckBox'])+"','"+
                            sqlQuote(mtd_val)+"','"+sqlQuote(self.annotator)+"')")
            if not self.metadataStickyBox.isChecked():# reset autoexclusive buttons
                self.clearAutoExclusiveRadioBtnBoxes()
            if self.showDataCheck.isChecked():
                self.datadlg.refreshView()
            if self.gridCheck.isChecked():
                self.writeGridDetailsToMetadata()
        except:
            self.showError()

    

    def showAnnotations(self):
        '''
        showAnnotations draws the targets and measurements of the frame when not recording, read
        only. After a measurement is chosen in the Measurements panel, its fish is drawn as usual
        and the other fish of that frame are faded.
        '''
        self.clearMarks()
        if self.dataDB is None or self.noLoad:
            return
        frame=self.frameBox.text()
        if not frame.isdigit():
            return
        focus=None
        if self.annotationFocus:
            if str(self.annotationFocus[0])==frame:
                focus=self.annotationFocus[1]
            else:
                # the chosen measurement is on another frame
                self.annotationFocus=None
        size=self.guiSettings['LabelTextSize']
        query=self.dataDB.dbQuery("SELECT target_number, species_group FROM targets WHERE frame_number="+frame+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
        for target, species_group in query:
            target=int(target)
            alpha=255 if focus is None or target==focus else 60
            col=self.guiSettings['SceneColor']
            if species_group in self.speciesList:
                col=self.spcColors[self.speciesList.index(species_group)]
            spcLabel=''
            if self.guiSettings['LabelSpeciesParam']>0 and species_group:
                spcLabel=' '+species_group[0:self.guiSettings['LabelSpeciesParam']]
            query1=self.dataDB.dbQuery("SELECT LX, LY, RX, RY, Range, Error FROM points WHERE frame_number="+frame+" AND deployment_id='"+sqlQuote(self.deployment)+
                "' AND target_number="+str(target))
            for LX, LY, RX, RY, Range, Error in query1:
                style='o' if LX!=None and RX!=None else '+'
                for imageObj, x, y in [(self.gvLeft, LX, LY), (self.gvRight, RX, RY)]:
                    if x==None:
                        continue
                    marker=imageObj.addMark(QPointF(float(x), float(y)), style=style, color=col, size=1.0, thickness=1.0, alpha=alpha, selectable=False)
                    self.pointMarks.update({marker:[target, imageObj]})
                    text=str(target)
                    if imageObj==self.gvLeft and style=='o' and Range!=None:
                        text=text+" r = "+str(round(float(Range), 2))+"  e = "+str(round(float(Error), 2))
                    marker.addLabel(text+spcLabel, color=col, alpha=alpha, size=size, offset=self.textOffset, name='tnumber')
                    if not self.labelCheck.isChecked():
                        marker.hideLabels(None)
            query2=self.dataDB.dbQuery("SELECT line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2, Length, Error, name FROM lines WHERE frame_number="+frame+
                " AND deployment_id='"+sqlQuote(self.deployment)+"' AND target_number="+str(target))
            for line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2, Length, Error, name in query2:
                lineObjs={}
                for imageObj, x1, y1, x2, y2 in [(self.gvLeft, LX1, LY1, LX2, LY2), (self.gvRight, RX1, RY1, RX2, RY2)]:
                    if QPointF(float(x1), float(y1))==QPointF(float(x2), float(y2)):
                        continue
                    lineObjs[imageObj]=imageObj.addDimensionLine(QPointF(float(x1), float(y1)), QPointF(float(x2), float(y2)), taillength=self.guiSettings['MeasureLineTailLength'],
                            thickness=self.guiSettings['MeasureLineWidth'], color=self.guiSettings['TargetLineColor'], alpha=alpha)
                    self.lineMarks.update({lineObjs[imageObj]:[target, imageObj]})
                if self.gvLeft in lineObjs:
                    text=line_label[0:3]+" = "+str(round(float(Length), 2))+" e = "+str(round(float(Error), 2))
                    if name:
                        text=name+": "+text
                    lineObjs[self.gvLeft].addLabel(QPointF(float(LX1), float(LY1)), text, color=self.guiSettings['TargetLineColor'], alpha=alpha, size=size)
                    if not self.labelCheck.isChecked():
                        lineObjs[self.gvLeft].hideLabels(None)
            self.separateTargetLabels(target)

    def showMeasurement(self, frame, target):
        '''
        showMeasurement goes to the frame of a row clicked in the Measurements panel and shows its
        fish: selected while recording, otherwise drawn over the faded other fish of the frame.
        '''
        self.annotationFocus=(frame, target)
        if not self.recordBtn.isChecked() and self.leftImageFrames[self.imageSlider.value()]==frame:
            # same frame: the slider doesn't move, redraw here
            self.showAnnotations()
        self.changeSelectionFromTable(frame, target)

    def reloadData(self):
        if not self.recordBtn.isChecked():
            return
        try:
            if self.makeBoxes:
                # redraw boxes
                query = self.dataDB.dbQuery("SELECT camera_id,species_group,origin_x,origin_y,width,height,target_number FROM bounding_boxes WHERE frame_number="+self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                for camera_id,species_group,origin_x,origin_y,width,height,target_number in query:
                    if camera_id=='left':
                        imageObj=self.gvLeft
                    else:
                        imageObj=self.gvRight
                    spcInd=None
                    for btn in self.spcButtons:
                        if btn.text()==species_group:
                            spcInd=self.spcButtons.index(btn)
                            break
                    if not spcInd==None:
                        col=self.spcColors[spcInd]
                    else:
                        col=[255,  0,  0]
                    boxCoords=QRect(int(origin_x),int(origin_y),int(width),int(height))
                    boxObj = imageObj.addPolygon(boxCoords,color=col, thickness=self.guiSettings['BoxLineThickness'], selectable=True,
                            selectThickness=4.0, selectColor=self.selColor)

                    self.boxMarks.update({boxObj:[int(target_number),  imageObj]})
                    #  and add a label - polygon labels are attached to the vertices and the first
                    #  argument is the index of the vertex you want to attach the label to. For
                    #  rubber band boxes, the verts are always ordered clockwise from the upper left
                    spcLabel=''
                    if self.guiSettings['LabelSpeciesParam']>0:
                        spcLabel=species_group
                        if len(spcLabel)>self.guiSettings['LabelSpeciesParam']:
                            spcLabel=spcLabel[0:self.guiSettings['LabelSpeciesParam']]
                    boxObj.addLabel(0, target_number+" "+spcLabel, color=col, size=self.guiSettings['LabelTextSize'])

            else:
                # get frame level annotator
                query = self.dataDB.dbQuery("SELECT annotator FROM FRAMES WHERE frame_number="+self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                current_tators, =query.first()
                if current_tators==None:
                    current_tators=''
                tators=current_tators.split('|')
                if not self.annotator in tators:
                    # add our tator
                    if len(current_tators)>0:
                        current_tators=current_tators+"|"+self.annotator
                    else:
                        current_tators=self.annotator
                self.annotatorLabel.setText(current_tators)
                # draw targets
                self.activeLine[self.gvLeft]=None
                self.activeLine[self.gvRight]=None
                
                query = self.dataDB.dbQuery("SELECT target_number, species_group FROM targets WHERE frame_number="+
                self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"'")
                targetToDelete=[]
                for target_number, species_group in query:
                    # points
                    query1 = self.dataDB.dbQuery("SELECT point_label, LX, LY, RX, RY, Range, Error FROM points WHERE frame_number="+
                    self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"' AND target_number="+target_number)
                    for point_label,  LX, LY, RX, RY, Range, Error in query1: #, Length, LHX,LHY, LTX, LTY, RHX, RHY, RTX, RTY
                        spcLabel=''
                        if self.guiSettings['LabelSpeciesParam']>0:
                            spcLabel=species_group
                            if len(spcLabel)>self.guiSettings['LabelSpeciesParam']:
                                spcLabel=spcLabel[0:self.guiSettings['LabelSpeciesParam']]
                        # find out the class and appropriate color
                        if species_group in ['SceneRange',  'SceneMeasurement']:
                            col=self.guiSettings['SceneColor']
                            style='d'
                        else:
                            spcInd=None
                            for btn in self.spcButtons:
                                if btn.text()==species_group:
                                    spcInd=self.spcButtons.index(btn)
                                    break
                            if not spcInd==None:
                                col=self.spcColors[spcInd]
                                style='o'
                            else:
                                col=self.guiSettings['SceneColor']
                                style='o'
                        if RX==None and LX!=None:# this is in the left image only target
                            marker = self.gvLeft.addMark(QPointF(float(LX), float(LY)), style='+', color=col,
                                                          size=1.0, thickness=1.0, alpha=255, selectThickness=self.selThickness,  selectColor=self.selColor)

                            self.pointMarks.update({marker:[int(target_number),  self.gvLeft]})

                            marker.addLabel(target_number+" "+spcLabel, color=col,  size=self.guiSettings['LabelTextSize'], offset=self.textOffset, name='tnumber')
                            if not self.labelCheck.isChecked():
                                marker.hideLabels(None)

                        elif LX==None and RX!=None:# this is in the right image only target
                            marker = self.gvRight.addMark(QPointF(float(RX), float(RY)), style='+', color=col,
                                                          size=1.0, thickness=1.0, alpha=255, selectThickness=self.selThickness,  selectColor=self.selColor)
                            
                            marker.addLabel(target_number+" "+spcLabel , color=col,  size=self.guiSettings['LabelTextSize'], offset=self.textOffset, name='tnumber')
                            self.pointMarks.update({marker:[int(target_number),  self.gvRight]})
                            if not self.labelCheck.isChecked():
                                marker.hideLabels(None)
                        elif RX!=None and LX!=None:# this is a stereo target

                            marker = self.gvRight.addMark(QPointF(float(RX), float(RY)), style=style, color=col,
                                                          size=1.0, thickness=1.0, alpha=255, selectThickness=self.selThickness,  selectColor=self.selColor)
                            self.pointMarks.update({marker:[int(target_number),  self.gvRight]})
                            marker.addLabel(target_number+" "+spcLabel , color=col,  size=self.guiSettings['LabelTextSize'], offset=self.textOffset, name='tnumber')
                            if not self.labelCheck.isChecked():
                                marker.hideLabels(None)
                            marker = self.gvLeft.addMark(QPointF(float(LX), float(LY)), style=style, color=col,
                                                          size=1.0, thickness=1.0, alpha=255, selectThickness=self.selThickness,  selectColor=self.selColor)
                            self.pointMarks.update({marker:[int(target_number),  self.gvLeft]})
                            targetLabel=target_number +" r = "+str(round(float(Range), 2))+"  e = "+str(round(float(Error), 2))
                            if self.guiSettings['ShowClassOnLabel']=='true':
                                targetLabel=targetLabel+' '+species_group
                            marker.addLabel(targetLabel+" "+spcLabel, color=col,size=self.guiSettings['LabelTextSize'], offset=self.textOffset, name='tnumber')
                            if not self.labelCheck.isChecked():
                                marker.hideLabels(None)
                    # lines
                    query2 = self.dataDB.dbQuery("SELECT line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2, Length, Error FROM lines WHERE frame_number="+
                    self.frameBox.text()+" AND deployment_id='"+sqlQuote(self.deployment)+"' AND target_number="+target_number)
                    for line_label,  LX1,LY1, LX2, LY2, RX1, RY1, RX2, RY2,  Length,  Error in query2: #, 
                        if species_group == 'SceneMeasurement':  #this is a line only object
                            col=self.guiSettings['SceneColor']
                        else:# this is a measurement line associated with a target
                            col=self.guiSettings['TargetLineColor']
        #                print(query.value(2).toString())
                        stPoint=QPointF(float(LX1), float(LY1))
                        endPoint=QPointF(float(LX2), float(LY2))
                        if stPoint==endPoint:# this will be prevented in the future!
                            QMessageBox.warning(self, "ERROR", "This Target has a dimension line that starts and ends at the same point, which is an Error.  The target will be deleted.")
                            targetToDelete.append(target_number)
                            continue
                        lineObjsL=self.gvLeft.addDimensionLine(stPoint,endPoint, taillength=self.guiSettings['MeasureLineTailLength'], thickness=self.guiSettings['MeasureLineWidth'],  color=col)
                        self.lineMarks.update({lineObjsL:[int(target_number),  self.gvLeft]})
                        # right image
                        stPoint=QPointF(float(RX1), float(RY1))
                        endPoint=QPointF(float(RX2), float(RY2))
                        if stPoint==endPoint:# this will be prevented in the future!
                            QMessageBox.warning(self, "ERROR", "This Target has a dimension line that starts and ends at the same point, which is an Error.  The target will be deleted.")
                            targetToDelete.append(target_number)
                            continue
                        lineObjs=self.gvRight.addDimensionLine(stPoint,endPoint, taillength=self.guiSettings['MeasureLineTailLength'], thickness=self.guiSettings['MeasureLineWidth'], color=col)
                        self.lineMarks.update({lineObjs:[int(target_number),  self.gvRight]})
                        lineObjsL.addLabel(QPointF(float(LX1), float(LY1)),line_label[0:3]+" = "+str(round(float(Length), 2))+" e = "+str(round(float(Error), 2)), color=col,  size=self.guiSettings['LabelTextSize'])
                        if not self.labelCheck.isChecked():
                            lineObjsL.hideLabels(None)
                        self.separateTargetLabels(int(target_number))
                            

                        
                # delete bad target (temporary)
                for t in targetToDelete:
                    self.dataDB.dbExec("DELETE FROM targets WHERE frame_number="+self.frameBox.text()+" AND target_number="+t+"  AND deployment_ID='"+sqlQuote(self.deployment)+"'")
                if targetToDelete:
                    self.updateTimelineMarks()
                # relod frame metadata
                if self.settings['CollectMetadata'].lower()=='true' or self.settings['CollectMetadata'].lower()=='yes':
                    if 'ExclusiveRadioBox1' in self.metadataTypesDict:
                        query = self.dataDB.dbQuery("SELECT metadata_tag, metadata_value FROM FRAME_METADATA WHERE frame_number="+
                        self.frameBox.text()+" AND metadata_group='"+sqlQuote(self.metadataGroup)+"' AND metadata_type='"+sqlQuote(self.metadataTypesDict['ExclusiveRadioBox1'])+"' AND deployment_id='"+sqlQuote(self.deployment)+"'")
                        # this should be only one
                        radioBtnTag1,  val=query.first()
                        if radioBtnTag1:
                            for tag in self.radioBtnTags1:
                                if tag.text()==radioBtnTag1:
                                    tag.setChecked(True)
                                    
                    if 'ExclusiveRadioBox2' in self.metadataTypesDict:
                        query = self.dataDB.dbQuery("SELECT metadata_tag, metadata_value FROM FRAME_METADATA WHERE frame_number="+
                        self.frameBox.text()+" AND metadata_group='"+sqlQuote(self.metadataGroup)+"' AND metadata_type='"+sqlQuote(self.metadataTypesDict['ExclusiveRadioBox2'])+"' AND deployment_id='"+sqlQuote(self.deployment)+"'")
                        # this should be only one
                        radioBtnTag2,  val=query.first()
                        if radioBtnTag2:
                            for tag in self.radioBtnTags2:
                                if tag.text()==radioBtnTag2:
                                    tag.setChecked(True)
                                    
                    if 'ExclusiveRadioBox3' in self.metadataTypesDict:
                        query = self.dataDB.dbQuery("SELECT metadata_tag, metadata_value FROM FRAME_METADATA WHERE frame_number="+
                        self.frameBox.text()+" AND metadata_group='"+sqlQuote(self.metadataGroup)+"' AND metadata_type='"+sqlQuote(self.metadataTypesDict['ExclusiveRadioBox3'])+"' AND deployment_id='"+sqlQuote(self.deployment)+"'")
                        # this should be only one
                        radioBtnTag3,  val=query.first()
                        if radioBtnTag3:
                            for tag in self.radioBtnTags3:
                                if tag.text()==radioBtnTag3:
                                    tag.setChecked(True)
                                    
                    if 'LineEdit' in self.metadataTypesDict:
                        query = self.dataDB.dbQuery("SELECT metadata_tag, metadata_value FROM FRAME_METADATA WHERE frame_number="+
                        self.frameBox.text()+" AND metadata_group='"+sqlQuote(self.metadataGroup)+"' AND metadata_type='"+sqlQuote(self.metadataTypesDict['LineEdit'])+"' AND deployment_id='"+sqlQuote(self.deployment)+"'")
                        for lineEditTag,  val in query:
                            if lineEditTag:
                                for i in list(range(len(self.metadataLineEditLabels))):
                                    if self.metadataLineEditLabels[i].text()==lineEditTag:
                                        self.metadataLineEdits[i].setText(val)
                                        
                    if 'CheckBox' in self.metadataTypesDict:
                        query = self.dataDB.dbQuery("SELECT metadata_tag, metadata_value FROM FRAME_METADATA WHERE frame_number="+
                        self.frameBox.text()+" AND metadata_group='"+sqlQuote(self.metadataGroup)+"' AND metadata_type='"+sqlQuote(self.metadataTypesDict['CheckBox'])+"' AND deployment_id='"+sqlQuote(self.deployment)+"'")
                        for checkBoxTag,  val in query:
                            if checkBoxTag:
                                for i in list(range(len(self.metadataLineEditLabels))):
                                    if self.metadataCheckBoxes[i].text()==checkBoxTag:
                                        if val=='Checked':
                                            self.metadataCheckBoxes[i].setChecked(True)
                                        else:
                                            self.metadataCheckBoxes[i].setChecked(False)
            # reload the frame comment
            frame=self.leftImageFrames[self.imageSlider.value()]
            self.frameCommentDlg.showComment(str(frame))
        except:
            self.showError()
            
                
    def clearMetadataSelections(self):
        if not self.metadataStickyBox.isChecked():# reset autoexclusive buttons
            self.clearAutoExclusiveRadioBtnBoxes()
        
    def clearAutoExclusiveRadioBtnBoxes(self):
        for rad in self.radioBtnTags1:
            rad.setAutoExclusive(False)
            rad.setChecked(False)
            rad.setAutoExclusive(True)
        for rad in self.radioBtnTags2:
            rad.setAutoExclusive(False)
            rad.setChecked(False)
            rad.setAutoExclusive(True)
        for rad in self.radioBtnTags3:
            rad.setAutoExclusive(False)
            rad.setChecked(False)
            rad.setAutoExclusive(True)


    def clearMarks(self):
        self.clearEpipolar()
        self.gvLeft.removeAllItems()
        self.gvRight.removeAllItems()
        self.lineMarks={}
        self.pointMarks={}
        self.boxMarks={}
        # the marks are deleted: forget any reference to them
        self.__selectedItems=[]
        self.activeMark[self.gvLeft]=None
        self.activeMark[self.gvRight]=None

    def copyImg(self):
        dirDlg = QFileDialog(self)
        copyDir = dirDlg.getExistingDirectory(self, 'Select Copy Location', self.__copyImageDir,
                                              QFileDialog.Option.ShowDirsOnly)
        if copyDir !='':
            self.__copyImageDir=copyDir
            if self.videoMode:
                # no image files to copy - save the current frames instead
                for gvObj, file in [(self.gvRight, self.RFile), (self.gvLeft, self.LFile)]:
                    if file:
                        name=os.path.splitext(os.path.basename(file))[0]+'_frame%06d.png' % int(self.frameBox.text())
                        cv2.imwrite(copyDir+'/'+name, gvObj.image.sourceData)
            else:
                f=self.RFile.split('/')
                QFile(self.RFile).copy(copyDir+'/'+f[-1])
                f=self.LFile.split('/')
                QFile(self.LFile).copy(copyDir+'/'+f[-1])

    def changeActiveTarget(self,  target,  frame,  zoom):
        if int(frame)!=self.imageSlider.value():
            self.imageSlider.setValue(int(frame))
            self.resizeEvent(None)
        for items in self.__selectedItems:
            items.setSelected(False)
        self.__selectedItems=[]
        self.activeMark [self.gvRight]=None
        self.activeMark [self.gvLeft]=None
        for item, info in self.pointMarks.items():
            if info[0]==int(target):
                item.setSelected(True)
                self.__selectedItems.append(item)
                if info[1]==self.gvLeft:
                    self.activeMark [self.gvLeft]=item
                else:
                    self.activeMark [self.gvRight]=item
        if self.activeMark[self.gvLeft]:
            self.gvLeft.zoomToMark(self.activeMark[self.gvLeft], int(zoom))
        if self.activeMark[self.gvRight]:
            self.gvRight.zoomToMark(self.activeMark[self.gvRight], int(zoom))

#
#    def toggleClass(self, species):
#        for btn in self.spcButtons:
#            if btn.text()==species:
#                btn.setChecked(True)
#            else:
#                btn.setChecked(False)

    def calculate(self, what):
        unit=10
        if what=='point':
            xL=ny.array([[self.targetPosition[0].x()],[self.targetPosition[0].y()]])
            xR=ny.array([[self.targetPosition[1].x()],[self.targetPosition[1].y()]])
            (XL, XR)=self.stereoComp.triangulatePoint(xL, xR)
            lx=XL[0, 0]/unit
            ly=XL[2, 0]/unit
            lz=-XL[1, 0]/unit
            xLp=self.stereoComp.projectPoint(XL, 'L')
            xRp=self.stereoComp.projectPoint(XR, 'R')
            width=max(self.gvLeft.imgPixmap.width(), self.gvRight.imgPixmap.width())
            error=self.stereoComp.computeError(xL,xLp,xR,xRp)
            #error=error/width*10000

            Range=round(sqrt(lx**2+ly**2+lz**2), len(str(unit)))
            self.targetStereoData=[Range, error,  lx, ly, lz]
        elif what=='line':
            lineL=self.activeLine[self.gvLeft].getLine()
            lineR=self.activeLine[self.gvRight].getLine()
            LHX=lineL.x1()
            LHY=lineL.y1()
            LTX=lineL.x2()
            LTY=lineL.y2()
            RHX=lineR.x1()
            RHY=lineR.y1()
            RTX=lineR.x2()
            RTY=lineR.y2()
            xL=ny.array([[LHX,LTX],[LHY,LTY]])
            xR=ny.array([[RHX,RTX],[RHY,RTY]])

            (XL, XR)=self.stereoComp.triangulatePoint(xL, xR)
            xLp=self.stereoComp.projectPoint(XL, 'L')
            xRp=self.stereoComp.projectPoint(XR, 'R')

            width=max(self.gvLeft.imgPixmap.width(), self.gvRight.imgPixmap.width())
            error=self.stereoComp.computeError(xL,xLp,xR,xRp)
            #error=(error/width)*10000
            lhx=XL[0, 0]/unit
            lhy=XL[2, 0]/unit
            lhz=-XL[1, 0]/unit
            ltx=XL[0, 1]/unit
            lty=XL[2, 1]/unit
            ltz=-XL[1, 1]/unit
            rhx=XR[0, 0]/unit
            rhy=XR[2, 0]/unit
            rhz=-XR[1, 0]/unit
            rtx=XR[0, 1]/unit
            rty=XR[2, 1]/unit
            rtz=-XR[1, 1]/unit
            length=round((sqrt((lhx-ltx)**2+(lhy-lty)**2+(lhz-ltz)**2)+sqrt((rhx-rtx)**2+(rhy-rty)**2+(rhz-rtz)**2))/2, len(str(unit)))
            Range=round(sqrt(((lhx+ltx/2))**2+((lhy+lty)/2)**2+((lhz+ltz)/2)**2), len(str(unit)))# range from left camera
            self.targetStereoData=[length, Range, error,  LHX, LHY,LTX,LTY, RHX, RHY,RTX,RTY,lhx, lhy, lhz,ltx,lty, ltz]

    def recompute3D(self):
        if not self.stereoAvailable():
            return
        # points
        sql=("SELECT deployment_id, frame_number, target_number, point_label, LX, LY, RX, RY FROM points WHERE range is not NULL") #LHX, LHY, LTX, LTY,  RHX, RHY, RTX, RTY
        try:
            self.targetPosition=[None,  None]
            query = self.dataDB.dbQuery(sql)
            for deployment, frame_number, target_number,point_label,  LX, LY, RX, RY in query: #, LHX, LHY, LTX, LTY,  RHX, RHY, RTX, RTY
                self.targetPosition[0]=QPointF(float(LX), float(LY))
                self.targetPosition[1]=QPointF(float(RX), float(RY))
                self.calculate('point')
                #self.targetStereoData=[range, error,  lx, ly, lz]
                sql=("UPDATE points SET Range = "+str(self.targetStereoData[0])+",  Error = "+str(self.targetStereoData[1])+",  x = "+
                str(self.targetStereoData[2])+",  y = "+str(self.targetStereoData[3])+",  z = "+str(self.targetStereoData[4])+" WHERE frame_number = "+
                frame_number+" AND target_number="+target_number+" AND point_label='"+point_label+"'")
                self.dataDB.dbExec(sql)
        except:
            self.showError()
            return
        # lines
        sql=("SELECT deployment_id, frame_number, target_number, line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2 FROM lines") #LHX, LHY, LTX, LTY,  RHX, RHY, RTX, RTY
        try:
            from QImageViewer import QIVDimensionLine
            query = self.dataDB.dbQuery(sql)
            for deployment, frame_number, target_number,line_label, LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2 in query:
                dimLine = QIVDimensionLine.QIVDimensionLine(startPoint=QPointF(float(LX1), float(LY1)), endPoint=QPointF(float(LX2), float(LY2)), color=self.guiSettings['TargetLineColor'],
                                    thickness=self.guiSettings['MeasureLineWidth'], alpha=255, linestyle='-',
                                    taillength=self.guiSettings['MeasureLineTailLength'], view=self.gvLeft)
                self.activeLine[self.gvLeft] = dimLine
                dimLine = QIVDimensionLine.QIVDimensionLine(startPoint=QPointF(float(RX1), float(RY1)), endPoint=QPointF(float(RX2), float(RY2)), color=self.guiSettings['TargetLineColor'],
                                    thickness=self.guiSettings['MeasureLineWidth'], alpha=255, linestyle='-',
                                    taillength=self.guiSettings['MeasureLineTailLength'], view=self.gvRight)
                self.activeLine[self.gvRight] = dimLine
                self.calculate('line')
                #self.targetStereoData=[length, range, error,  LHX, LHY,LTX,LTY, RHX, RHY,RTX,RTY,lhx, lhy, lhz,ltx,lty, ltz]
                self.dataDB.dbExec("UPDATE lines SET Length = "+str(self.targetStereoData[0])+", Error = "+str(self.targetStereoData[2])+",  X1 = "+
                str(self.targetStereoData[11])+",  Y1 = "+str(self.targetStereoData[12])+",  Z1 = "+str(self.targetStereoData[13])+", X2 = "+
                str(self.targetStereoData[14])+", Y2 = "+str(self.targetStereoData[15])+", Z2 = "+str(self.targetStereoData[16])+" WHERE frame_number = "+
                frame_number+" AND target_number="+target_number+" AND line_label='"+line_label+"'")
            QMessageBox.warning(self, "INFO", "Positions have been recalculated :-)")
            self.__changeImage()
            self.measurementsDock.refresh()
        except:
            self.showError()
            
    def checkBoxAction(self):
        if self.sender()==self.closeupCheck:
            if self.closeupCheck.isChecked():
                position = self.appSettings.value('zoomwinposition', QPoint(10,10))
                #self.closeup.move(position)
                self.closeup.show()
            else:
                self.appSettings.setValue('zoomwinposition', self.closeup.pos())
                self.closeup.hide()
        elif self.sender()==self.showDataCheck:
            if self.showDataCheck.isChecked():
                position = self.appSettings.value('datawinposition', QPoint(10,10))
                #self.datadlg.move(position)
                self.datadlg.show()
                self.datadlg.refreshView()
            else:
                self.appSettings.setValue('datawinposition', self.datadlg.pos())
                self.datadlg.hide()
        elif self.sender()==self.labelCheck:
            if self.labelCheck.isChecked():
                for mark,  x in self.pointMarks.items():
                    mark.showLabels(None)
                for line,  x in self.lineMarks.items():
                    line.showLabels(None)

            else:
                for mark,  x in self.pointMarks.items():
                    mark.hideLabels(None)
                for line,  x in self.lineMarks.items():
                    line.hideLabels(None)
        elif self.sender()==self.metadataCheckBox:
            if self.metadataCheckBox.isChecked():
                # enable metadata inputs
                for widget in self.metadataWidgets:
                    widget.setEnabled(True)
            else:
                # disable metadata inputs
                for widget in self.metadataWidgets:
                    widget.setEnabled(False)
    def gridBoxAction(self):

        if self.gridCheck.isChecked(): # we are adding grid
            self.showGrid()
        else:
            self.clearGridAndSave()
            
    def showGrid(self):
        if self.activeGV=='Right':# figure out which gv is up
            gvObj=self.gvRight
        else:
            gvObj=self.gvLeft
        # check to see if we already have data with a grid here
        query=self.dataDB.dbQuery("SELECT metadata_value FROM FRAME_METADATA WHERE frame_number="+self.frameBox.text()+\
        " AND metadata_group='CountingGridInformation' AND metadata_tag='1' AND metadata_type='GridSize' AND deployment_id='"+sqlQuote(self.deployment)+"'")
        gridsize=query.first()[0]# we may have an existing grid we collected data with
        if not gridsize:# first grid in this frame
            self.randomCell=None
            self.gridCount=1
            gridsize=self.gridSetup['GridSize']
        else: # get random square previously used
            if gridsize==self.gridSetup['GridSize']:# if grid size is same, reload previous grid
                query=self.dataDB.dbQuery("SELECT metadata_value FROM FRAME_METADATA WHERE frame_number="+self.frameBox.text()+\
                " AND metadata_group='CountingGridInformation' AND metadata_tag='1' AND metadata_type='RandomCell' AND deployment_id='"+sqlQuote(self.deployment)+"'")
                randomCell, =query.first()
                if randomCell in (None, 'None'):
                    self.randomCell=None
                else:
                    self.randomCell=int(randomCell)
                query=self.dataDB.dbQuery("SELECT metadata_tag FROM FRAME_METADATA WHERE frame_number="+self.frameBox.text()+\
                " AND metadata_group='CountingGridInformation' AND metadata_type='GridSize' AND metadata_value='"+gridsize+"' AND deployment_id='"+sqlQuote(self.deployment)+"'")
                self.gridCount=int(query.first()[0])
            else:
                # this is a new grid with a different size!
                self.randomCell=None
                query=self.dataDB.dbQuery("SELECT metadata_tag FROM FRAME_METADATA WHERE frame_number="+self.frameBox.text()+\
                " AND metadata_group='CountingGridInformation' AND deployment_id='"+sqlQuote(self.deployment)+"' GROUP BY metadata_tag")
                grids=[]
                for grid,  in query:
                    grids.append(int(grid))
                self.gridCount=max(grids)+1
                gridsize=self.gridSetup['GridSize']
                self.speciesInGrid=set()
                
        x=gvObj.imgPixmap.width()
        y=gvObj.imgPixmap.height()
        if gridsize=='1x2':# vertical slip in two
            vLine1 = gvObj.addDimensionLine(QPointF(x/2, 0), QPointF(x/2, y), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)

            self.gridLines[gvObj] = [vLine1]

        elif gridsize=='2x2':# vertical & horizontal slip in two
            vLine1 = gvObj.addDimensionLine(QPointF(x/2, 0), QPointF(x/2, y), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)
            hLine1 = gvObj.addDimensionLine(QPointF(0, y/2), QPointF(x, y/2), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)

            self.gridLines[gvObj] = [vLine1, hLine1]
        elif gridsize=='2x3':# same as previous vertical slip in three
            vLine1 = gvObj.addDimensionLine(QPointF(x/3, 0), QPointF(x/3, y), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)
            vLine2 = gvObj.addDimensionLine(QPointF(2*x/3, 0), QPointF(2*x/3, y), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)
            hLine1 = gvObj.addDimensionLine(QPointF(0, y/2), QPointF(x, y/2), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)

            self.gridLines[gvObj] = [vLine1, vLine2,  hLine1]
        elif gridsize=='3x3':# horizontal and vertical slip in three
            vLine1 = gvObj.addDimensionLine(QPointF(x/3, 0), QPointF(x/3, y), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)
            vLine2 = gvObj.addDimensionLine(QPointF(2*x/3, 0), QPointF(2*x/3, y), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)
            hLine1 = gvObj.addDimensionLine(QPointF(0, y/3), QPointF(x, y/3), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)
            hLine2 = gvObj.addDimensionLine(QPointF(0, 2*y/3), QPointF(x, 2*y/3), color=self.gridSetup['GridLineColor'],
                                thickness=self.gridSetup['GridLineThickness'], alpha=255, linestyle=self.gridSetup['GridLineStyle'], taillength=0)

            self.gridLines[gvObj] = [vLine1, vLine2,  hLine1,  hLine2]
        if self.gridSetup['RandomizeCell']:
            self.lightupRandomCell(gridsize)
        else:
            self.randomCellLines[gvObj]=None
            self.randomCell=None
                
    def clearGridAndSave(self):
        if self.activeGV=='Right':# figure out which gv is up
            gvObj=self.gvRight
        else:
            gvObj=self.gvLeft
        # write data, if any
        if len(self.speciesInGrid)>0:
            self.writeGridDetailsToMetadata()
            self.speciesInGrid=set()
        # remove lines
        for lineObj in self.gridLines[gvObj]:
            gvObj.removeItem(lineObj)
        if self.randomCellLines[gvObj]:
            gvObj.removeItem(self.randomCellLines[gvObj])
            self.randomCell=None
            
    def lightupRandomCell(self,  gridsize):
        if self.activeGV=='Right':# figure out which gv is up
            gvObj=self.gvRight
        else:
            gvObj=self.gvLeft
        # delete any prevuious random grid
        gvObj.removeItem(self.randomCellLines[gvObj])
        x=gvObj.imgPixmap.width()
        y=gvObj.imgPixmap.height()
        self.randomCellBounds=[0, x, 0, y]
        if gridsize=='1x2':# vertical slip in two
            # get a random box
            if not self.randomCell:
                self.randomCell=random.randrange(2)
            if self.randomCell==0:#clockwise from top left
                verts=[QPointF(0, y), QPointF(0, 0), QPointF(x/2, 0), QPointF(x/2, y)]
                self.randomCellBounds=[0, x/2, 0, y]
            else:
                verts=[QPointF(x/2, 0), QPointF(x/2, y), QPointF(x, y), QPointF(x, 0)]
                self.randomCellBounds=[x/2, x,  0, y]
                
        elif gridsize=='2x2':# vertical & horizontal slip in two\
            # get a random self.randomCell
            if not self.randomCell:
                self.randomCell=random.randrange(4)
            if self.randomCell==0:#row order from top left
                verts=[QPointF(0, y/2), QPointF(0, 0), QPointF(x/2, 0), QPointF(x/2, y/2)]
                self.randomCellBounds=[0, x/2, 0, y/2]
            elif self.randomCell==1:
                verts=[QPointF(x/2, y/2), QPointF(x/2, 0), QPointF(x, 0), QPointF(x, y/2)]
                self.randomCellBounds=[x/2, x, 0, y/2]
            elif self.randomCell==2:
                verts=[QPointF(0, y/2), QPointF(0, y), QPointF(x/2, y), QPointF(x/2, y/2)]
                self.randomCellBounds=[0, x/2, y/2, y ]
            else:
                verts=[QPointF(x/2, y/2), QPointF(x/2, y), QPointF(x, y), QPointF(x, y/2)]
                self.randomCellBounds=[x/2, x, y/2,  y]
                
        elif gridsize=='2x3':# same as previous vertical slip in three
            # get a random self.randomCell
            if not self.randomCell:
                self.randomCell=random.randrange(6)
            if self.randomCell==0:#row order from top left
                verts=[QPointF(0, y/2), QPointF(0, 0), QPointF(x/3, 0), QPointF(x/3, y/2)]
                self.randomCellBounds=[0, x/3, 0, y/2]
            elif self.randomCell==1:
                verts=[QPointF(x/3, y/2), QPointF(x/3, 0), QPointF(2*x/3, 0), QPointF(2*x/3, y/2)]
                self.randomCellBounds=[x/3, 2*x/3, 0, y/2]
            elif self.randomCell==2:
                verts=[QPointF(2*x/3, y/2), QPointF(2*x/3, 0), QPointF(x, 0), QPointF(x,  y/2)]
                self.randomCellBounds=[2*x/3, x, 0, y/2]
            elif self.randomCell==3:
                verts=[QPointF(0, y), QPointF(0, y/2), QPointF(x/3, y/2), QPointF(x/3, y)]
                self.randomCellBounds=[0, x/3, y/2, y]
            elif self.randomCell==4:
                verts=[QPointF(x/3, y), QPointF(x/3,  y/2), QPointF(2*x/3,  y/2), QPointF(2*x/3, y)]
                self.randomCellBounds=[x/3,2*x/3,  y/2, y]
            elif self.randomCell==5:
                verts=[QPointF(2*x/3, y), QPointF(2*x/3,  y/2), QPointF(x,  y/2), QPointF(x,  y)]
                self.randomCellBounds=[2*x/3,x,  y/2, y]
                
        elif gridsize=='3x3':# same as previous vertical slip in three
            # get a random self.randomCell
            if not self.randomCell:
                self.randomCell=random.randrange(9)
            if self.randomCell==0:#clockwise from top left
                verts=[QPointF(0, y/3), QPointF(0, 0), QPointF(x/3, 0), QPointF(x/3, y/3)]
                self.randomCellBounds=[0,x/3, 0,  y/3]
            elif self.randomCell==1:
                verts=[QPointF(x/3, y/3), QPointF(x/3, 0), QPointF(2*x/3, 0), QPointF(2*x/3, y/3)]
                self.randomCellBounds=[x/3, 2*x/3,  0,  y/3]
            elif self.randomCell==2:
                verts=[QPointF(2*x/3, y/3), QPointF(2*x/3, 0), QPointF(x, 0), QPointF(x, y/3)]
                self.randomCellBounds=[2*x/3, x,  0,  y/3]
            elif self.randomCell==3:
                verts=[QPointF(0, 2*y/3), QPointF(0, y/3), QPointF(x/3, y/3), QPointF(x/3, 2*y/3)]
                self.randomCellBounds=[0,x/3, y/3, 2*y/3]
            elif self.randomCell==4:
                verts=[QPointF(x/3, 2*y/3), QPointF(x/3, y/3), QPointF(2*x/3, y/3), QPointF(2*x/3, 2*y/3)]
                self.randomCellBounds=[x/3,2*x/3,  y/3, 2*y/3]
            elif self.randomCell==5:
                verts=[QPointF(2*x/3, 2*y/3), QPointF(2*x/3, y/3), QPointF(x, y/3), QPointF(x, 2*y/3)]
                self.randomCellBounds=[2*x/3, x,  y/3, 2*y/3]
            elif self.randomCell==6:
                verts=[QPointF(0, y), QPointF(0, 2*y/3), QPointF(x/3, 2*y/3), QPointF(x/3,y)]
                self.randomCellBounds=[0, x/3,  2*y/3, y]
            elif self.randomCell==7:
                verts=[QPointF(x/3, y), QPointF(x/3, 2*y/3), QPointF(2*x/3, 2*y/3), QPointF(2*x/3, y)]
                self.randomCellBounds=[x/3, 2*x/3,  2*y/3, y]
            else:
                verts=[QPointF(2*x/3, y), QPointF(2*x/3, 2*y/3), QPointF(x, 2*y/3), QPointF(x, y)]
                self.randomCellBounds=[2*x/3, x, 2*y/3, y]
                
        randBoxObj = gvObj.addPolygon(verts, color=self.gridSetup['CellLineColor'],
                                thickness=self.gridSetup['GridLineThickness']*2, alpha=255, linestyle='_')
        self.randomCellLines[gvObj] = randBoxObj
        
    def writeGridDetailsToMetadata(self):
        # check to see if this size grid is already in
        query=self.dataDB.dbQuery("SELECT metadata_value FROM FRAME_METADATA WHERE frame_number="+self.frameBox.text()+\
        " AND metadata_group='CountingGridInformation' AND metadata_tag='1' AND metadata_type='GridSize' AND deployment_id='"+sqlQuote(self.deployment)+"'")
        gridsize=query.first()[0]# we may have an existing grid we collected data with
        if gridsize==self.gridSetup['GridSize']:# this size grid already exists for this frame, update species list?
            query=self.dataDB.dbQuery("SELECT metadata_value FROM FRAME_METADATA WHERE frame_number="+self.frameBox.text()+\
            " AND metadata_group='CountingGridInformation' AND metadata_tag='1' AND metadata_type='SpeciesInGrid' AND deployment_id='"+sqlQuote(self.deployment)+"'")
            spc_list=query.first()[0].split(";")# we may have an existing grid we collected data with
            for spc in spc_list:
                self.speciesInGrid.add(spc)
            # update species list if user added more counts
            self.dataDB.dbExec("UPDATE FRAME_METADATA SET metadata_value = '"+";".join(self.speciesInGrid)+"' WHERE frame_number="+self.frameBox.text()+\
            " AND metadata_group = 'CountingGridInformation'"+
             "AND metadata_type='SpeciesInGrid' AND metadata_tag='"+str(self.gridCount)+"' AND deployment_id='"+sqlQuote(self.deployment)+"'")
        else: # new grid, need to write everything
            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project,deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value, annotator)"+
                                " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'CountingGridInformation','"+str(self.gridCount)+"','GridSize','"+
                                self.gridSetup['GridSize']+"','"+sqlQuote(self.annotator)+"')")
            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project,deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value, annotator)"+
                                " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'CountingGridInformation','"+str(self.gridCount)+"','SpeciesInGrid','"+
                                ";".join(self.speciesInGrid)+"','"+sqlQuote(self.annotator)+"')")
            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project,deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value, annotator)"+
                                " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'CountingGridInformation','"+str(self.gridCount)+"','RandomCell','"+
                                str(self.randomCell)+"','"+sqlQuote(self.annotator)+"')")
            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project,deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value, annotator)"+
                                " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'CountingGridInformation','"+str(self.gridCount)+"','CameraUsed','"+
                                self.activeGV+"','"+sqlQuote(self.annotator)+"')")
            vals=self.gridSetup['GridSize'].split('x')
            self.dataDB.dbExec("INSERT INTO FRAME_METADATA (project, deployment_ID, frame_number, metadata_group, metadata_tag, metadata_type, metadata_value, annotator)"+
                                " VALUES('"+sqlQuote(self.activeProject)+"','"+sqlQuote(self.deployment)+"',"+self.frameBox.text()+",'CountingGridInformation','"+str(self.gridCount)+"','ScalingFactor','"+
                                str(int(vals[0])*int(vals[1]))+"','"+sqlQuote(self.annotator)+"')")

    def clearGridData(self):
        reply=QMessageBox.warning(self, "WARNING", "Sure you want to delete the grid data for this frame?",  QMessageBox.Yes, QMessageBox.No)
        if reply==QMessageBox.Yes:
            self.gridCheck.setChecked(False)
            self.dataDB.dbExec("DELETE FROM FRAME_METADATA WHERE frame_number="+self.frameBox.text()+" AND deployment_ID='"+sqlQuote(self.deployment)+"' AND metadata_group='CountingGridInformation'")
            self.gridBoxAction()

    def writeDatatoCSV(self):
        if not self.dataDB:
            return
        import pandas as pd
        import sqlite3
        try:
            conn = sqlite3.connect(self.dataPath + self.activeProject+'_' + self.deployment+'.db', isolation_level=None,detect_types=sqlite3.PARSE_COLNAMES)
            db_df = pd.read_sql_query("SELECT * FROM frames WHERE  deployment_id='"+sqlQuote(self.deployment)+"'", conn)
            filename=str(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.activeProject+'_' + self.deployment+'_frames.csv')
            db_df.to_csv(filename, index=False)
            db_df = pd.read_sql_query("SELECT * FROM targets WHERE  deployment_id='"+sqlQuote(self.deployment)+"'", conn)
            filename=str(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.activeProject+'_' + self.deployment+'_targets.csv')
            db_df.to_csv(filename, index=False)
            db_df = pd.read_sql_query("SELECT * FROM points WHERE  deployment_id='"+sqlQuote(self.deployment)+"'", conn)
            filename=str(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.activeProject+'_' + self.deployment+'_points.csv')
            db_df.to_csv(filename, index=False)
            db_df = pd.read_sql_query("SELECT * FROM lines WHERE  deployment_id='"+sqlQuote(self.deployment)+"'", conn)
            filename=str(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.activeProject+'_' + self.deployment+'_lines.csv')
            db_df.to_csv(filename, index=False)
            db_df = pd.read_sql_query("SELECT * FROM bounding_boxes WHERE  deployment_id='"+sqlQuote(self.deployment)+"'", conn)
            filename=str(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.activeProject+'_' + self.deployment+'_bounding_boxes.csv')
            db_df.to_csv(filename, index=False)
            db_df = pd.read_sql_query("SELECT * FROM frame_metadata WHERE  deployment_id='"+sqlQuote(self.deployment)+"'", conn)
            filename=str(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.activeProject+'_'+ self.deployment+'_frame_metadata.csv')
            db_df.to_csv(filename, index=False)
            # write out image adjustments as well
            self.leftAdjustmentParms=self.gvLeft.adjustmentDialog.getState()
            self.rightAdjustmentParms=self.gvRight.adjustmentDialog.getState()
            imageadjustments={'left':self.leftAdjustmentParms, 'right':self.rightAdjustmentParms}
            ny.save(self.sourcePath.path() + '/' + self.deployment + '/' + "data" + '/' + self.deployment+'_image_adjustments', imageadjustments)
        except:
            self.showError()
           

    def rgbStr2Lists(self,  rgbstr):
        try:
            vals=rgbstr.split(',')
            rgblist=[int(vals[0]), int(vals[1]), int(vals[2])]
            return(rgblist)
        except:
            self.showError()
            
    def closeEvent(self, event):
        self.closeup.hide()
        if (self.datadlg):
            try:
                self.datadlg.hide()
                self.appSettings.value('datawinposition', self.datadlg.pos())
            except:
                self.showError()

        #  shut down the fetchers and accept
        self.appSettings.setValue('winposition', self.pos())
        self.appSettings.setValue('winsize', self.size())
        # the layout of the window: restored at the next start (see __init__)
        self.appSettings.setValue('layoutVersion', LAYOUT_VERSION)
        self.appSettings.setValue('geometry', self.saveGeometry())
        self.appSettings.setValue('windowState', self.saveState(LAYOUT_VERSION))
        self.appSettings.setValue('samplerate', self.sampleRateEdit.text())
        self.appSettings.setValue('zoomwinposition', self.closeup.pos())
        self.appSettings.setValue('copyimagedir', self.__copyImageDir)
        # stash gui settings
        self.appSettings.setValue('MeasureLineTailLength',self.guiSettings['MeasureLineTailLength'])
        colstr=str(self.guiSettings['TargetLineColor'][0])+","+str(self.guiSettings['TargetLineColor'][1])+","+str(self.guiSettings['TargetLineColor'][2])
        self.appSettings.setValue('TargetLineColor', colstr)
        colstr=str(self.guiSettings['SceneColor'][0])+","+str(self.guiSettings['SceneColor'][1])+","+str(self.guiSettings['SceneColor'][2])
        self.appSettings.setValue('SceneColor', colstr)
        self.appSettings.setValue('BoxLineThickness', self.guiSettings['BoxLineThickness'])
        self.appSettings.setValue('LabelTextSize', self.guiSettings['LabelTextSize'])
        self.appSettings.setValue('LabelSpeciesParam', self.guiSettings['LabelSpeciesParam'])
        self.appSettings.setValue('ShowClassOnLabel', self.guiSettings['ShowClassOnLabel'])
        self.appSettings.setValue('DefaultMetadataSelection', self.guiSettings['DefaultMetadataSelection'])
        self.appSettings.setValue('RetainSpeciesSelection', self.guiSettings['RetainSpeciesSelection'])
        self.appSettings.setValue('PlaybackSpeedAdjust', self.guiSettings['PlaybackSpeedAdjust'])
        # stash grid settings
        self.appSettings.setValue('GridSize',self.gridSetup['GridSize'])
        colstr=str(self.gridSetup['GridLineColor'][0])+","+str(self.gridSetup['GridLineColor'][1])+","+str(self.gridSetup['GridLineColor'][2])
        self.appSettings.setValue('GridLineColor', colstr)
        colstr=str(self.gridSetup['CellLineColor'][0])+","+str(self.gridSetup['CellLineColor'][1])+","+str(self.gridSetup['CellLineColor'][2])
        self.appSettings.setValue('CellLineColor', colstr)
        self.appSettings.setValue('RandomizeCell', str(self.gridSetup['RandomizeCell']))
        self.appSettings.setValue('PersistentGrid', str(self.gridSetup['PersistentGrid']))
        self.appSettings.setValue('CellBoundary', str(self.gridSetup['CellBoundary']))
        self.appSettings.setValue('GridLineStyle', self.gridSetup['GridLineStyle'])
        self.appSettings.setValue('GridLineThickness', str(self.gridSetup['GridLineThickness']))

        # write out excel file from db
        if self.appDB:
            self.appDB.dbClose()
        # save and close the deployment, and remove its lockfile
        self.closeDeployment()
        event.accept()


class textBoxFilter(QObject):
    '''
    textBoxFilter is a simple Qt Event filter that diverts Left and Right arrow key presses
    and passes them onto a different event handler as specified in "action".
    '''
    def __init__(self, action, parent=None):
        super(textBoxFilter, self).__init__(parent)
        self.action = action

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress) and ((event.key()==Qt.Key_Left) or (event.key()==Qt.Key_Right)):
            #  eat the enter key press
            self.action(None, event)
            return True
        else:
            # not an enter key press - pass along
            return QObject.eventFilter(self, obj, event)


if __name__ == "__main__":

    #  paths like ../db and ../calibrations are relative to the application folder
    if not getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(os.path.realpath(__file__)))

    app = QApplication(sys.argv)
    theme.apply(app)
    form = SEBASTES()
    form.show()
    app.exec()


