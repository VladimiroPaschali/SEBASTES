# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SEBASTES_dockable.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDockWidget, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QRadioButton, QSizePolicy, QSlider, QSpacerItem,
    QSpinBox, QStackedWidget, QStatusBar, QTabWidget,
    QToolButton, QVBoxLayout, QWidget)

from QImageViewer.QImageViewer import QImageViewer
from timelineslider import TimelineSlider
from welcomepage import WelcomePage

class Ui_SEBASTES(object):
    def setupUi(self, SEBASTES):
        if not SEBASTES.objectName():
            SEBASTES.setObjectName(u"SEBASTES")
        SEBASTES.resize(1962, 905)
        SEBASTES.setMinimumSize(QSize(0, 0))
        font = QFont()
        font.setPointSize(10)
        SEBASTES.setFont(font)
        self.actionLoad = QAction(SEBASTES)
        self.actionLoad.setObjectName(u"actionLoad")
        self.actionExit = QAction(SEBASTES)
        self.actionExit.setObjectName(u"actionExit")
        self.actionProfiles = QAction(SEBASTES)
        self.actionProfiles.setObjectName(u"actionProfiles")
        self.actionGUI_settings = QAction(SEBASTES)
        self.actionGUI_settings.setObjectName(u"actionGUI_settings")
        self.actionGrid_setup = QAction(SEBASTES)
        self.actionGrid_setup.setObjectName(u"actionGrid_setup")
        self.actionSet_Active_Profiles = QAction(SEBASTES)
        self.actionSet_Active_Profiles.setObjectName(u"actionSet_Active_Profiles")
        self.actionImport_Export_Profiles = QAction(SEBASTES)
        self.actionImport_Export_Profiles.setObjectName(u"actionImport_Export_Profiles")
        self.actionCreate_New_Project = QAction(SEBASTES)
        self.actionCreate_New_Project.setObjectName(u"actionCreate_New_Project")
        self.actionviewApplicationDB = QAction(SEBASTES)
        self.actionviewApplicationDB.setObjectName(u"actionviewApplicationDB")
        self.actionedit_DB_tables = QAction(SEBASTES)
        self.actionedit_DB_tables.setObjectName(u"actionedit_DB_tables")
        self.actionAbout = QAction(SEBASTES)
        self.actionAbout.setObjectName(u"actionAbout")
        self.copyBtn = QAction(SEBASTES)
        self.copyBtn.setObjectName(u"copyBtn")
        self.labelCheck = QAction(SEBASTES)
        self.labelCheck.setObjectName(u"labelCheck")
        self.labelCheck.setCheckable(True)
        self.labelCheck.setChecked(True)
        self.showDataCheck = QAction(SEBASTES)
        self.showDataCheck.setObjectName(u"showDataCheck")
        self.showDataCheck.setCheckable(True)
        self.closeupCheck = QAction(SEBASTES)
        self.closeupCheck.setObjectName(u"closeupCheck")
        self.closeupCheck.setCheckable(True)
        self.gridCheck = QAction(SEBASTES)
        self.gridCheck.setObjectName(u"gridCheck")
        self.gridCheck.setCheckable(True)
        self.epipolarCheck = QAction(SEBASTES)
        self.epipolarCheck.setObjectName(u"epipolarCheck")
        self.epipolarCheck.setCheckable(True)
        self.epipolarCheck.setChecked(True)
        self.recordBtn = QAction(SEBASTES)
        self.recordBtn.setObjectName(u"recordBtn")
        self.recordBtn.setCheckable(True)
        self.measureBtn = QAction(SEBASTES)
        self.measureBtn.setObjectName(u"measureBtn")
        self.measureBtn.setCheckable(True)
        self.linkBtn = QAction(SEBASTES)
        self.linkBtn.setObjectName(u"linkBtn")
        self.linkBtn.setCheckable(True)
        self.delLinkBtn = QAction(SEBASTES)
        self.delLinkBtn.setObjectName(u"delLinkBtn")
        self.editSpeciesBtn = QAction(SEBASTES)
        self.editSpeciesBtn.setObjectName(u"editSpeciesBtn")
        self.targetCommentBtn = QAction(SEBASTES)
        self.targetCommentBtn.setObjectName(u"targetCommentBtn")
        self.frameCommentBtn = QAction(SEBASTES)
        self.frameCommentBtn.setObjectName(u"frameCommentBtn")
        self.frameCommentBtn.setCheckable(True)
        self.computeMatchBox = QAction(SEBASTES)
        self.computeMatchBox.setObjectName(u"computeMatchBox")
        self.computeMatchBox.setCheckable(True)
        self.actionMatchThreshold = QAction(SEBASTES)
        self.actionMatchThreshold.setObjectName(u"actionMatchThreshold")
        self.stereoOnlyCheckBox = QAction(SEBASTES)
        self.stereoOnlyCheckBox.setObjectName(u"stereoOnlyCheckBox")
        self.stereoOnlyCheckBox.setCheckable(True)
        self.recomputeBtn = QAction(SEBASTES)
        self.recomputeBtn.setObjectName(u"recomputeBtn")
        self.trainBtn = QAction(SEBASTES)
        self.trainBtn.setObjectName(u"trainBtn")
        self.trainBtn.setCheckable(True)
        self.clearGridBtn = QAction(SEBASTES)
        self.clearGridBtn.setObjectName(u"clearGridBtn")
        self.monoRadio = QAction(SEBASTES)
        self.monoRadio.setObjectName(u"monoRadio")
        self.monoRadio.setCheckable(True)
        self.stereoRadio = QAction(SEBASTES)
        self.stereoRadio.setObjectName(u"stereoRadio")
        self.stereoRadio.setCheckable(True)
        self.stereoRadio.setChecked(True)
        self.centralwidget = QWidget(SEBASTES)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.imageStack = QStackedWidget(self.centralwidget)
        self.imageStack.setObjectName(u"imageStack")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.imageStack.sizePolicy().hasHeightForWidth())
        self.imageStack.setSizePolicy(sizePolicy)
        self.viewPage = QWidget()
        self.viewPage.setObjectName(u"viewPage")
        self.horizontalLayout_19 = QHBoxLayout(self.viewPage)
        self.horizontalLayout_19.setSpacing(6)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalLayout_19.setContentsMargins(6, 6, 6, 6)
        self.frameLeft = QFrame(self.viewPage)
        self.frameLeft.setObjectName(u"frameLeft")
        self.frameLeft.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_9 = QVBoxLayout(self.frameLeft)
        self.verticalLayout_9.setSpacing(2)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setSpacing(4)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(2, 0, 0, 0)
        self.leftCaption = QLabel(self.frameLeft)
        self.leftCaption.setObjectName(u"leftCaption")
        font1 = QFont()
        font1.setBold(True)
        self.leftCaption.setFont(font1)

        self.horizontalLayout_9.addWidget(self.leftCaption)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer)

        self.adjLeftBtn = QToolButton(self.frameLeft)
        self.adjLeftBtn.setObjectName(u"adjLeftBtn")
        self.adjLeftBtn.setFocusPolicy(Qt.NoFocus)
        self.adjLeftBtn.setIconSize(QSize(18, 18))
        self.adjLeftBtn.setAutoRaise(True)

        self.horizontalLayout_9.addWidget(self.adjLeftBtn)


        self.verticalLayout_9.addLayout(self.horizontalLayout_9)

        self.gvLeft = QImageViewer(self.frameLeft)
        self.gvLeft.setObjectName(u"gvLeft")

        self.verticalLayout_9.addWidget(self.gvLeft)


        self.horizontalLayout_19.addWidget(self.frameLeft)

        self.frameRight = QFrame(self.viewPage)
        self.frameRight.setObjectName(u"frameRight")
        self.frameRight.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_8 = QVBoxLayout(self.frameRight)
        self.verticalLayout_8.setSpacing(2)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setSpacing(4)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(2, 0, 0, 0)
        self.rightCaption = QLabel(self.frameRight)
        self.rightCaption.setObjectName(u"rightCaption")
        self.rightCaption.setFont(font1)

        self.horizontalLayout_10.addWidget(self.rightCaption)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_5)

        self.adjRightBtn = QToolButton(self.frameRight)
        self.adjRightBtn.setObjectName(u"adjRightBtn")
        self.adjRightBtn.setFocusPolicy(Qt.NoFocus)
        self.adjRightBtn.setIconSize(QSize(18, 18))
        self.adjRightBtn.setAutoRaise(True)

        self.horizontalLayout_10.addWidget(self.adjRightBtn)


        self.verticalLayout_8.addLayout(self.horizontalLayout_10)

        self.gvRight = QImageViewer(self.frameRight)
        self.gvRight.setObjectName(u"gvRight")

        self.verticalLayout_8.addWidget(self.gvRight)


        self.horizontalLayout_19.addWidget(self.frameRight)

        self.horizontalLayout_19.setStretch(0, 1)
        self.horizontalLayout_19.setStretch(1, 1)
        self.imageStack.addWidget(self.viewPage)
        self.welcomePage = WelcomePage()
        self.welcomePage.setObjectName(u"welcomePage")
        self.imageStack.addWidget(self.welcomePage)

        self.verticalLayout.addWidget(self.imageStack)

        self.navBar = QFrame(self.centralwidget)
        self.navBar.setObjectName(u"navBar")
        self.navBar.setFrameShape(QFrame.NoFrame)
        self.navLayout = QVBoxLayout(self.navBar)
        self.navLayout.setSpacing(2)
        self.navLayout.setObjectName(u"navLayout")
        self.navLayout.setContentsMargins(8, 6, 8, 6)
        self.imageSlider = TimelineSlider(self.navBar)
        self.imageSlider.setObjectName(u"imageSlider")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.imageSlider.sizePolicy().hasHeightForWidth())
        self.imageSlider.setSizePolicy(sizePolicy1)
        self.imageSlider.setMinimumSize(QSize(60, 22))
        self.imageSlider.setOrientation(Qt.Horizontal)

        self.navLayout.addWidget(self.imageSlider)

        self.navRow = QHBoxLayout()
        self.navRow.setSpacing(4)
        self.navRow.setObjectName(u"navRow")
        self.navRow.setContentsMargins(0, 0, 0, 0)
        self.firstBtn = QToolButton(self.navBar)
        self.firstBtn.setObjectName(u"firstBtn")
        self.firstBtn.setFocusPolicy(Qt.NoFocus)
        self.firstBtn.setIconSize(QSize(18, 18))
        self.firstBtn.setAutoRaise(True)

        self.navRow.addWidget(self.firstBtn)

        self.prevSampleBtn = QToolButton(self.navBar)
        self.prevSampleBtn.setObjectName(u"prevSampleBtn")
        self.prevSampleBtn.setFocusPolicy(Qt.NoFocus)
        self.prevSampleBtn.setIconSize(QSize(18, 18))
        self.prevSampleBtn.setAutoRaise(True)

        self.navRow.addWidget(self.prevSampleBtn)

        self.prevFrameBtn = QToolButton(self.navBar)
        self.prevFrameBtn.setObjectName(u"prevFrameBtn")
        self.prevFrameBtn.setFocusPolicy(Qt.NoFocus)
        self.prevFrameBtn.setIconSize(QSize(18, 18))
        self.prevFrameBtn.setAutoRaise(True)

        self.navRow.addWidget(self.prevFrameBtn)

        self.playBtn = QPushButton(self.navBar)
        self.playBtn.setObjectName(u"playBtn")
        self.playBtn.setMinimumSize(QSize(88, 0))
        self.playBtn.setFocusPolicy(Qt.NoFocus)
        self.playBtn.setIconSize(QSize(16, 16))
        self.playBtn.setCheckable(True)

        self.navRow.addWidget(self.playBtn)

        self.nextFrameBtn = QToolButton(self.navBar)
        self.nextFrameBtn.setObjectName(u"nextFrameBtn")
        self.nextFrameBtn.setFocusPolicy(Qt.NoFocus)
        self.nextFrameBtn.setIconSize(QSize(18, 18))
        self.nextFrameBtn.setAutoRaise(True)

        self.navRow.addWidget(self.nextFrameBtn)

        self.nextSampleBtn = QToolButton(self.navBar)
        self.nextSampleBtn.setObjectName(u"nextSampleBtn")
        self.nextSampleBtn.setFocusPolicy(Qt.NoFocus)
        self.nextSampleBtn.setIconSize(QSize(18, 18))
        self.nextSampleBtn.setAutoRaise(True)

        self.navRow.addWidget(self.nextSampleBtn)

        self.lastBtn = QToolButton(self.navBar)
        self.lastBtn.setObjectName(u"lastBtn")
        self.lastBtn.setFocusPolicy(Qt.NoFocus)
        self.lastBtn.setIconSize(QSize(18, 18))
        self.lastBtn.setAutoRaise(True)

        self.navRow.addWidget(self.lastBtn)

        self.lastFrameBtn = QToolButton(self.navBar)
        self.lastFrameBtn.setObjectName(u"lastFrameBtn")
        self.lastFrameBtn.setFocusPolicy(Qt.NoFocus)
        self.lastFrameBtn.setIconSize(QSize(18, 18))
        self.lastFrameBtn.setAutoRaise(True)

        self.navRow.addWidget(self.lastFrameBtn)

        self.navSpacerLeft = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.navRow.addItem(self.navSpacerLeft)

        self.frameInfo = QWidget(self.navBar)
        self.frameInfo.setObjectName(u"frameInfo")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.frameInfo.sizePolicy().hasHeightForWidth())
        self.frameInfo.setSizePolicy(sizePolicy2)
        self.frameInfo.setMinimumSize(QSize(1, 0))
        self.frameLayout = QHBoxLayout(self.frameInfo)
        self.frameLayout.setSpacing(4)
        self.frameLayout.setObjectName(u"frameLayout")
        self.frameLayout.setContentsMargins(0, 0, 0, 0)
        self.frameLabel = QLabel(self.frameInfo)
        self.frameLabel.setObjectName(u"frameLabel")

        self.frameLayout.addWidget(self.frameLabel)

        self.frameBox = QLineEdit(self.frameInfo)
        self.frameBox.setObjectName(u"frameBox")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.frameBox.sizePolicy().hasHeightForWidth())
        self.frameBox.setSizePolicy(sizePolicy3)
        self.frameBox.setMinimumSize(QSize(64, 0))
        self.frameBox.setMaximumSize(QSize(64, 16777215))
        self.frameBox.setAlignment(Qt.AlignCenter)

        self.frameLayout.addWidget(self.frameBox)

        self.maxFrame = QLabel(self.frameInfo)
        self.maxFrame.setObjectName(u"maxFrame")

        self.frameLayout.addWidget(self.maxFrame)

        self.timeLabel = QLabel(self.frameInfo)
        self.timeLabel.setObjectName(u"timeLabel")

        self.frameLayout.addWidget(self.timeLabel)


        self.navRow.addWidget(self.frameInfo)

        self.navSpacerRight = QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.navRow.addItem(self.navSpacerRight)

        self.sampleBox = QWidget(self.navBar)
        self.sampleBox.setObjectName(u"sampleBox")
        sizePolicy2.setHeightForWidth(self.sampleBox.sizePolicy().hasHeightForWidth())
        self.sampleBox.setSizePolicy(sizePolicy2)
        self.sampleBox.setMinimumSize(QSize(1, 0))
        self.sampleLayout = QHBoxLayout(self.sampleBox)
        self.sampleLayout.setSpacing(4)
        self.sampleLayout.setObjectName(u"sampleLayout")
        self.sampleLayout.setContentsMargins(14, 0, 0, 0)
        self.everyLabel = QLabel(self.sampleBox)
        self.everyLabel.setObjectName(u"everyLabel")

        self.sampleLayout.addWidget(self.everyLabel)

        self.sampleRateEdit = QLineEdit(self.sampleBox)
        self.sampleRateEdit.setObjectName(u"sampleRateEdit")
        sizePolicy3.setHeightForWidth(self.sampleRateEdit.sizePolicy().hasHeightForWidth())
        self.sampleRateEdit.setSizePolicy(sizePolicy3)
        self.sampleRateEdit.setMinimumSize(QSize(44, 0))
        self.sampleRateEdit.setMaximumSize(QSize(44, 16777215))
        self.sampleRateEdit.setAlignment(Qt.AlignCenter)

        self.sampleLayout.addWidget(self.sampleRateEdit)

        self.offsetLabel = QLabel(self.sampleBox)
        self.offsetLabel.setObjectName(u"offsetLabel")

        self.sampleLayout.addWidget(self.offsetLabel)

        self.rateOffsetEdit = QLineEdit(self.sampleBox)
        self.rateOffsetEdit.setObjectName(u"rateOffsetEdit")
        sizePolicy3.setHeightForWidth(self.rateOffsetEdit.sizePolicy().hasHeightForWidth())
        self.rateOffsetEdit.setSizePolicy(sizePolicy3)
        self.rateOffsetEdit.setMinimumSize(QSize(44, 0))
        self.rateOffsetEdit.setMaximumSize(QSize(44, 16777215))
        self.rateOffsetEdit.setAlignment(Qt.AlignCenter)

        self.sampleLayout.addWidget(self.rateOffsetEdit)


        self.navRow.addWidget(self.sampleBox)

        self.speedBox = QWidget(self.navBar)
        self.speedBox.setObjectName(u"speedBox")
        sizePolicy2.setHeightForWidth(self.speedBox.sizePolicy().hasHeightForWidth())
        self.speedBox.setSizePolicy(sizePolicy2)
        self.speedBox.setMinimumSize(QSize(1, 0))
        self.speedLayout = QHBoxLayout(self.speedBox)
        self.speedLayout.setSpacing(6)
        self.speedLayout.setObjectName(u"speedLayout")
        self.speedLayout.setContentsMargins(6, 0, 0, 0)
        self.navSeparator = QFrame(self.speedBox)
        self.navSeparator.setObjectName(u"navSeparator")
        self.navSeparator.setFrameShape(QFrame.VLine)
        self.navSeparator.setFrameShadow(QFrame.Sunken)

        self.speedLayout.addWidget(self.navSeparator)

        self.playSpeedLabel = QLabel(self.speedBox)
        self.playSpeedLabel.setObjectName(u"playSpeedLabel")

        self.speedLayout.addWidget(self.playSpeedLabel)

        self.playSpeedSlider = QSlider(self.speedBox)
        self.playSpeedSlider.setObjectName(u"playSpeedSlider")
        self.playSpeedSlider.setMinimumSize(QSize(50, 0))
        self.playSpeedSlider.setMaximumSize(QSize(100, 16777215))
        self.playSpeedSlider.setMinimum(1)
        self.playSpeedSlider.setMaximum(100)
        self.playSpeedSlider.setSingleStep(10)
        self.playSpeedSlider.setOrientation(Qt.Horizontal)

        self.speedLayout.addWidget(self.playSpeedSlider)

        self.playSpeedBox = QSpinBox(self.speedBox)
        self.playSpeedBox.setObjectName(u"playSpeedBox")
        self.playSpeedBox.setMinimumSize(QSize(84, 0))
        self.playSpeedBox.setMaximumSize(QSize(110, 16777215))
        self.playSpeedBox.setMinimum(1)
        self.playSpeedBox.setMaximum(100)

        self.speedLayout.addWidget(self.playSpeedBox)


        self.navRow.addWidget(self.speedBox)


        self.navLayout.addLayout(self.navRow)


        self.verticalLayout.addWidget(self.navBar)

        SEBASTES.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(SEBASTES)
        self.statusBar.setObjectName(u"statusBar")
        SEBASTES.setStatusBar(self.statusBar)
        self.menuBar = QMenuBar(SEBASTES)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 1962, 29))
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuView = QMenu(self.menuBar)
        self.menuView.setObjectName(u"menuView")
        self.menuAnnotate = QMenu(self.menuBar)
        self.menuAnnotate.setObjectName(u"menuAnnotate")
        self.menuSettings = QMenu(self.menuBar)
        self.menuSettings.setObjectName(u"menuSettings")
        self.menuHelp = QMenu(self.menuBar)
        self.menuHelp.setObjectName(u"menuHelp")
        SEBASTES.setMenuBar(self.menuBar)
        self.metadataDockWidget = QDockWidget(SEBASTES)
        self.metadataDockWidget.setObjectName(u"metadataDockWidget")
        self.dockWidgetContents_4 = QWidget()
        self.dockWidgetContents_4.setObjectName(u"dockWidgetContents_4")
        self.verticalLayout_13 = QVBoxLayout(self.dockWidgetContents_4)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.metadataCheckBox = QCheckBox(self.dockWidgetContents_4)
        self.metadataCheckBox.setObjectName(u"metadataCheckBox")

        self.verticalLayout_13.addWidget(self.metadataCheckBox)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.exclusiveRadioBox1 = QGroupBox(self.dockWidgetContents_4)
        self.exclusiveRadioBox1.setObjectName(u"exclusiveRadioBox1")
        font2 = QFont()
        font2.setPointSize(8)
        self.exclusiveRadioBox1.setFont(font2)
        self.verticalLayout_2 = QVBoxLayout(self.exclusiveRadioBox1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.radioButton1_1 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_1.setObjectName(u"radioButton1_1")

        self.verticalLayout_2.addWidget(self.radioButton1_1)

        self.radioButton1_2 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_2.setObjectName(u"radioButton1_2")

        self.verticalLayout_2.addWidget(self.radioButton1_2)

        self.radioButton1_3 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_3.setObjectName(u"radioButton1_3")

        self.verticalLayout_2.addWidget(self.radioButton1_3)

        self.radioButton1_4 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_4.setObjectName(u"radioButton1_4")

        self.verticalLayout_2.addWidget(self.radioButton1_4)

        self.radioButton1_5 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_5.setObjectName(u"radioButton1_5")

        self.verticalLayout_2.addWidget(self.radioButton1_5)

        self.radioButton1_6 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_6.setObjectName(u"radioButton1_6")

        self.verticalLayout_2.addWidget(self.radioButton1_6)

        self.radioButton1_7 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_7.setObjectName(u"radioButton1_7")

        self.verticalLayout_2.addWidget(self.radioButton1_7)

        self.radioButton1_8 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_8.setObjectName(u"radioButton1_8")

        self.verticalLayout_2.addWidget(self.radioButton1_8)

        self.radioButton1_9 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_9.setObjectName(u"radioButton1_9")

        self.verticalLayout_2.addWidget(self.radioButton1_9)

        self.radioButton1_10 = QRadioButton(self.exclusiveRadioBox1)
        self.radioButton1_10.setObjectName(u"radioButton1_10")

        self.verticalLayout_2.addWidget(self.radioButton1_10)


        self.horizontalLayout_8.addWidget(self.exclusiveRadioBox1)

        self.exclusiveRadioBox2 = QGroupBox(self.dockWidgetContents_4)
        self.exclusiveRadioBox2.setObjectName(u"exclusiveRadioBox2")
        self.exclusiveRadioBox2.setFont(font2)
        self.verticalLayout_5 = QVBoxLayout(self.exclusiveRadioBox2)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.radioButton2_1 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_1.setObjectName(u"radioButton2_1")

        self.verticalLayout_5.addWidget(self.radioButton2_1)

        self.radioButton2_2 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_2.setObjectName(u"radioButton2_2")

        self.verticalLayout_5.addWidget(self.radioButton2_2)

        self.radioButton2_3 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_3.setObjectName(u"radioButton2_3")

        self.verticalLayout_5.addWidget(self.radioButton2_3)

        self.radioButton2_4 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_4.setObjectName(u"radioButton2_4")

        self.verticalLayout_5.addWidget(self.radioButton2_4)

        self.radioButton2_5 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_5.setObjectName(u"radioButton2_5")

        self.verticalLayout_5.addWidget(self.radioButton2_5)

        self.radioButton2_6 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_6.setObjectName(u"radioButton2_6")

        self.verticalLayout_5.addWidget(self.radioButton2_6)

        self.radioButton2_7 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_7.setObjectName(u"radioButton2_7")

        self.verticalLayout_5.addWidget(self.radioButton2_7)

        self.radioButton2_8 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_8.setObjectName(u"radioButton2_8")

        self.verticalLayout_5.addWidget(self.radioButton2_8)

        self.radioButton2_9 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_9.setObjectName(u"radioButton2_9")

        self.verticalLayout_5.addWidget(self.radioButton2_9)

        self.radioButton2_10 = QRadioButton(self.exclusiveRadioBox2)
        self.radioButton2_10.setObjectName(u"radioButton2_10")

        self.verticalLayout_5.addWidget(self.radioButton2_10)


        self.horizontalLayout_8.addWidget(self.exclusiveRadioBox2)


        self.verticalLayout_13.addLayout(self.horizontalLayout_8)

        self.exclusiveRadioBox3 = QGroupBox(self.dockWidgetContents_4)
        self.exclusiveRadioBox3.setObjectName(u"exclusiveRadioBox3")
        self.exclusiveRadioBox3.setFont(font2)
        self.horizontalLayout_21 = QHBoxLayout(self.exclusiveRadioBox3)
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.radioButton3_1 = QRadioButton(self.exclusiveRadioBox3)
        self.radioButton3_1.setObjectName(u"radioButton3_1")
        self.radioButton3_1.setFont(font2)

        self.horizontalLayout_21.addWidget(self.radioButton3_1)

        self.radioButton3_2 = QRadioButton(self.exclusiveRadioBox3)
        self.radioButton3_2.setObjectName(u"radioButton3_2")
        self.radioButton3_2.setFont(font2)

        self.horizontalLayout_21.addWidget(self.radioButton3_2)


        self.verticalLayout_13.addWidget(self.exclusiveRadioBox3)

        self.metadataStickyBox = QCheckBox(self.dockWidgetContents_4)
        self.metadataStickyBox.setObjectName(u"metadataStickyBox")
        self.metadataStickyBox.setFont(font)

        self.verticalLayout_13.addWidget(self.metadataStickyBox)

        self.extraMetadataFrame = QFrame(self.dockWidgetContents_4)
        self.extraMetadataFrame.setObjectName(u"extraMetadataFrame")
        self.extraMetadataFrame.setFrameShape(QFrame.StyledPanel)
        self.extraMetadataFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_22 = QHBoxLayout(self.extraMetadataFrame)
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalLayout_11.setContentsMargins(-1, -1, 10, -1)
        self.metadataTypeLabel2 = QLabel(self.extraMetadataFrame)
        self.metadataTypeLabel2.setObjectName(u"metadataTypeLabel2")
        font3 = QFont()
        font3.setPointSize(10)
        font3.setBold(True)
        self.metadataTypeLabel2.setFont(font3)

        self.verticalLayout_11.addWidget(self.metadataTypeLabel2)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setSpacing(0)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label1_1 = QLabel(self.extraMetadataFrame)
        self.label1_1.setObjectName(u"label1_1")

        self.horizontalLayout_14.addWidget(self.label1_1)

        self.lineEdit1_1 = QLineEdit(self.extraMetadataFrame)
        self.lineEdit1_1.setObjectName(u"lineEdit1_1")
        self.lineEdit1_1.setMaximumSize(QSize(41, 16777215))

        self.horizontalLayout_14.addWidget(self.lineEdit1_1)


        self.verticalLayout_11.addLayout(self.horizontalLayout_14)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setSpacing(0)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label1_2 = QLabel(self.extraMetadataFrame)
        self.label1_2.setObjectName(u"label1_2")

        self.horizontalLayout_15.addWidget(self.label1_2)

        self.lineEdit1_2 = QLineEdit(self.extraMetadataFrame)
        self.lineEdit1_2.setObjectName(u"lineEdit1_2")
        self.lineEdit1_2.setMaximumSize(QSize(41, 16777215))

        self.horizontalLayout_15.addWidget(self.lineEdit1_2)


        self.verticalLayout_11.addLayout(self.horizontalLayout_15)

        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setSpacing(0)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label1_3 = QLabel(self.extraMetadataFrame)
        self.label1_3.setObjectName(u"label1_3")

        self.horizontalLayout_16.addWidget(self.label1_3)

        self.lineEdit1_3 = QLineEdit(self.extraMetadataFrame)
        self.lineEdit1_3.setObjectName(u"lineEdit1_3")
        self.lineEdit1_3.setMaximumSize(QSize(41, 16777215))

        self.horizontalLayout_16.addWidget(self.lineEdit1_3)


        self.verticalLayout_11.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setSpacing(0)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label1_4 = QLabel(self.extraMetadataFrame)
        self.label1_4.setObjectName(u"label1_4")

        self.horizontalLayout_17.addWidget(self.label1_4)

        self.lineEdit1_4 = QLineEdit(self.extraMetadataFrame)
        self.lineEdit1_4.setObjectName(u"lineEdit1_4")
        self.lineEdit1_4.setMaximumSize(QSize(41, 16777215))

        self.horizontalLayout_17.addWidget(self.lineEdit1_4)


        self.verticalLayout_11.addLayout(self.horizontalLayout_17)

        self.horizontalLayout_18 = QHBoxLayout()
        self.horizontalLayout_18.setSpacing(0)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.label1_5 = QLabel(self.extraMetadataFrame)
        self.label1_5.setObjectName(u"label1_5")

        self.horizontalLayout_18.addWidget(self.label1_5)

        self.lineEdit1_5 = QLineEdit(self.extraMetadataFrame)
        self.lineEdit1_5.setObjectName(u"lineEdit1_5")
        self.lineEdit1_5.setMaximumSize(QSize(41, 16777215))

        self.horizontalLayout_18.addWidget(self.lineEdit1_5)


        self.verticalLayout_11.addLayout(self.horizontalLayout_18)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_2)


        self.horizontalLayout_22.addLayout(self.verticalLayout_11)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, -1, 10, -1)
        self.metadataTypeLabel3 = QLabel(self.extraMetadataFrame)
        self.metadataTypeLabel3.setObjectName(u"metadataTypeLabel3")
        self.metadataTypeLabel3.setFont(font3)

        self.verticalLayout_6.addWidget(self.metadataTypeLabel3)

        self.checkBox1_1 = QCheckBox(self.extraMetadataFrame)
        self.checkBox1_1.setObjectName(u"checkBox1_1")

        self.verticalLayout_6.addWidget(self.checkBox1_1)

        self.checkBox1_2 = QCheckBox(self.extraMetadataFrame)
        self.checkBox1_2.setObjectName(u"checkBox1_2")

        self.verticalLayout_6.addWidget(self.checkBox1_2)

        self.checkBox1_3 = QCheckBox(self.extraMetadataFrame)
        self.checkBox1_3.setObjectName(u"checkBox1_3")

        self.verticalLayout_6.addWidget(self.checkBox1_3)

        self.checkBox1_4 = QCheckBox(self.extraMetadataFrame)
        self.checkBox1_4.setObjectName(u"checkBox1_4")

        self.verticalLayout_6.addWidget(self.checkBox1_4)

        self.checkBox1_5 = QCheckBox(self.extraMetadataFrame)
        self.checkBox1_5.setObjectName(u"checkBox1_5")

        self.verticalLayout_6.addWidget(self.checkBox1_5)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)


        self.horizontalLayout_22.addLayout(self.verticalLayout_6)


        self.verticalLayout_13.addWidget(self.extraMetadataFrame)

        self.metadataDockWidget.setWidget(self.dockWidgetContents_4)
        SEBASTES.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.metadataDockWidget)
        self.speciesDockWidget = QDockWidget(SEBASTES)
        self.speciesDockWidget.setObjectName(u"speciesDockWidget")
        self.dockWidgetContents_5 = QWidget()
        self.dockWidgetContents_5.setObjectName(u"dockWidgetContents_5")
        self.verticalLayout_14 = QVBoxLayout(self.dockWidgetContents_5)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.speciesTabWidget = QTabWidget(self.dockWidgetContents_5)
        self.speciesTabWidget.setObjectName(u"speciesTabWidget")
        self.speciesTabWidget.setMinimumSize(QSize(201, 0))
        self.speciesTabWidget.setTabPosition(QTabWidget.East)
        self.tab_1 = QWidget()
        self.tab_1.setObjectName(u"tab_1")
        self.verticalLayout_3 = QVBoxLayout(self.tab_1)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.btn1 = QPushButton(self.tab_1)
        self.btn1.setObjectName(u"btn1")
        self.btn1.setMinimumSize(QSize(0, 0))
        self.btn1.setMaximumSize(QSize(16777215, 16777215))
        self.btn1.setFont(font2)
        self.btn1.setCheckable(True)
        self.btn1.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn1)

        self.btn2 = QPushButton(self.tab_1)
        self.btn2.setObjectName(u"btn2")
        self.btn2.setMinimumSize(QSize(0, 0))
        self.btn2.setMaximumSize(QSize(16777215, 16777215))
        self.btn2.setFont(font2)
        self.btn2.setCheckable(True)
        self.btn2.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn2)

        self.btn3 = QPushButton(self.tab_1)
        self.btn3.setObjectName(u"btn3")
        self.btn3.setMinimumSize(QSize(0, 0))
        self.btn3.setMaximumSize(QSize(16777215, 16777215))
        self.btn3.setFont(font2)
        self.btn3.setCheckable(True)
        self.btn3.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn3)

        self.btn4 = QPushButton(self.tab_1)
        self.btn4.setObjectName(u"btn4")
        self.btn4.setMinimumSize(QSize(0, 0))
        self.btn4.setMaximumSize(QSize(16777215, 16777215))
        self.btn4.setFont(font2)
        self.btn4.setCheckable(True)
        self.btn4.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn4)

        self.btn5 = QPushButton(self.tab_1)
        self.btn5.setObjectName(u"btn5")
        self.btn5.setMinimumSize(QSize(0, 0))
        self.btn5.setMaximumSize(QSize(16777215, 16777215))
        self.btn5.setFont(font2)
        self.btn5.setCheckable(True)
        self.btn5.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn5)

        self.btn6 = QPushButton(self.tab_1)
        self.btn6.setObjectName(u"btn6")
        self.btn6.setMinimumSize(QSize(0, 0))
        self.btn6.setMaximumSize(QSize(16777215, 16777215))
        self.btn6.setFont(font2)
        self.btn6.setCheckable(True)
        self.btn6.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn6)

        self.btn7 = QPushButton(self.tab_1)
        self.btn7.setObjectName(u"btn7")
        self.btn7.setMinimumSize(QSize(0, 0))
        self.btn7.setMaximumSize(QSize(16777215, 16777215))
        self.btn7.setFont(font2)
        self.btn7.setCheckable(True)
        self.btn7.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn7)

        self.btn8 = QPushButton(self.tab_1)
        self.btn8.setObjectName(u"btn8")
        self.btn8.setMinimumSize(QSize(0, 0))
        self.btn8.setMaximumSize(QSize(16777215, 16777215))
        self.btn8.setFont(font2)
        self.btn8.setCheckable(True)
        self.btn8.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn8)

        self.btn9 = QPushButton(self.tab_1)
        self.btn9.setObjectName(u"btn9")
        self.btn9.setMinimumSize(QSize(0, 0))
        self.btn9.setMaximumSize(QSize(16777215, 16777215))
        self.btn9.setFont(font2)
        self.btn9.setCheckable(True)
        self.btn9.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn9)

        self.btn10 = QPushButton(self.tab_1)
        self.btn10.setObjectName(u"btn10")
        self.btn10.setMinimumSize(QSize(0, 0))
        self.btn10.setMaximumSize(QSize(16777215, 16777215))
        self.btn10.setFont(font2)
        self.btn10.setCheckable(True)
        self.btn10.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn10)

        self.btn11 = QPushButton(self.tab_1)
        self.btn11.setObjectName(u"btn11")
        self.btn11.setMinimumSize(QSize(0, 0))
        self.btn11.setMaximumSize(QSize(16777215, 16777215))
        self.btn11.setFont(font2)
        self.btn11.setCheckable(True)
        self.btn11.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn11)

        self.btn12 = QPushButton(self.tab_1)
        self.btn12.setObjectName(u"btn12")
        self.btn12.setMinimumSize(QSize(0, 0))
        self.btn12.setMaximumSize(QSize(16777215, 16777215))
        self.btn12.setFont(font2)
        self.btn12.setCheckable(True)
        self.btn12.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn12)

        self.btn13 = QPushButton(self.tab_1)
        self.btn13.setObjectName(u"btn13")
        self.btn13.setMinimumSize(QSize(0, 0))
        self.btn13.setMaximumSize(QSize(16777215, 16777215))
        self.btn13.setFont(font2)
        self.btn13.setCheckable(True)
        self.btn13.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn13)

        self.btn14 = QPushButton(self.tab_1)
        self.btn14.setObjectName(u"btn14")
        self.btn14.setMinimumSize(QSize(0, 0))
        self.btn14.setMaximumSize(QSize(16777215, 16777215))
        self.btn14.setFont(font2)
        self.btn14.setCheckable(True)
        self.btn14.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn14)

        self.btn15 = QPushButton(self.tab_1)
        self.btn15.setObjectName(u"btn15")
        self.btn15.setMinimumSize(QSize(0, 0))
        self.btn15.setMaximumSize(QSize(16777215, 16777215))
        self.btn15.setFont(font2)
        self.btn15.setCheckable(True)
        self.btn15.setAutoExclusive(True)

        self.verticalLayout_3.addWidget(self.btn15)

        self.speciesTabWidget.addTab(self.tab_1, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout_7 = QVBoxLayout(self.tab_2)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.btn16 = QPushButton(self.tab_2)
        self.btn16.setObjectName(u"btn16")
        self.btn16.setMinimumSize(QSize(0, 0))
        self.btn16.setMaximumSize(QSize(16777215, 16777215))
        self.btn16.setFont(font2)
        self.btn16.setCheckable(True)
        self.btn16.setAutoExclusive(True)

        self.verticalLayout_7.addWidget(self.btn16)

        self.btn17 = QPushButton(self.tab_2)
        self.btn17.setObjectName(u"btn17")
        self.btn17.setMinimumSize(QSize(0, 0))
        self.btn17.setMaximumSize(QSize(16777215, 16777215))
        self.btn17.setFont(font2)
        self.btn17.setCheckable(True)
        self.btn17.setAutoExclusive(True)

        self.verticalLayout_7.addWidget(self.btn17)

        self.btn18 = QPushButton(self.tab_2)
        self.btn18.setObjectName(u"btn18")
        self.btn18.setMinimumSize(QSize(0, 0))
        self.btn18.setMaximumSize(QSize(16777215, 16777215))
        self.btn18.setFont(font2)
        self.btn18.setCheckable(True)
        self.btn18.setAutoExclusive(True)

        self.verticalLayout_7.addWidget(self.btn18)

        self.btn19 = QPushButton(self.tab_2)
        self.btn19.setObjectName(u"btn19")
        self.btn19.setMinimumSize(QSize(0, 0))
        self.btn19.setMaximumSize(QSize(16777215, 16777215))
        self.btn19.setFont(font2)
        self.btn19.setCheckable(True)
        self.btn19.setAutoExclusive(True)

        self.verticalLayout_7.addWidget(self.btn19)

        self.btn20 = QPushButton(self.tab_2)
        self.btn20.setObjectName(u"btn20")
        self.btn20.setMinimumSize(QSize(0, 0))
        self.btn20.setMaximumSize(QSize(16777215, 16777215))
        self.btn20.setFont(font2)
        self.btn20.setCheckable(True)
        self.btn20.setAutoExclusive(True)

        self.verticalLayout_7.addWidget(self.btn20)

        self.btn21 = QPushButton(self.tab_2)
        self.btn21.setObjectName(u"btn21")

        self.verticalLayout_7.addWidget(self.btn21)

        self.btn22 = QPushButton(self.tab_2)
        self.btn22.setObjectName(u"btn22")

        self.verticalLayout_7.addWidget(self.btn22)

        self.btn23 = QPushButton(self.tab_2)
        self.btn23.setObjectName(u"btn23")

        self.verticalLayout_7.addWidget(self.btn23)

        self.btn24 = QPushButton(self.tab_2)
        self.btn24.setObjectName(u"btn24")

        self.verticalLayout_7.addWidget(self.btn24)

        self.btn25 = QPushButton(self.tab_2)
        self.btn25.setObjectName(u"btn25")

        self.verticalLayout_7.addWidget(self.btn25)

        self.btn26 = QPushButton(self.tab_2)
        self.btn26.setObjectName(u"btn26")

        self.verticalLayout_7.addWidget(self.btn26)

        self.btn27 = QPushButton(self.tab_2)
        self.btn27.setObjectName(u"btn27")

        self.verticalLayout_7.addWidget(self.btn27)

        self.btn28 = QPushButton(self.tab_2)
        self.btn28.setObjectName(u"btn28")

        self.verticalLayout_7.addWidget(self.btn28)

        self.btn29 = QPushButton(self.tab_2)
        self.btn29.setObjectName(u"btn29")

        self.verticalLayout_7.addWidget(self.btn29)

        self.btn30 = QPushButton(self.tab_2)
        self.btn30.setObjectName(u"btn30")

        self.verticalLayout_7.addWidget(self.btn30)

        self.speciesTabWidget.addTab(self.tab_2, "")

        self.verticalLayout_14.addWidget(self.speciesTabWidget)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_3 = QLabel(self.dockWidgetContents_5)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMaximumSize(QSize(55, 16777215))

        self.horizontalLayout_7.addWidget(self.label_3)

        self.countInFrameLabel = QLabel(self.dockWidgetContents_5)
        self.countInFrameLabel.setObjectName(u"countInFrameLabel")
        self.countInFrameLabel.setFrameShape(QFrame.Box)

        self.horizontalLayout_7.addWidget(self.countInFrameLabel)


        self.verticalLayout_14.addLayout(self.horizontalLayout_7)

        self.speciesDockWidget.setWidget(self.dockWidgetContents_5)
        SEBASTES.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.speciesDockWidget)

        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuView.menuAction())
        self.menuBar.addAction(self.menuAnnotate.menuAction())
        self.menuBar.addAction(self.menuSettings.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionLoad)
        self.menuFile.addAction(self.copyBtn)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuView.addAction(self.labelCheck)
        self.menuView.addAction(self.showDataCheck)
        self.menuView.addAction(self.closeupCheck)
        self.menuView.addAction(self.gridCheck)
        self.menuView.addAction(self.epipolarCheck)
        self.menuAnnotate.addAction(self.recordBtn)
        self.menuAnnotate.addAction(self.measureBtn)
        self.menuAnnotate.addAction(self.linkBtn)
        self.menuAnnotate.addAction(self.delLinkBtn)
        self.menuAnnotate.addAction(self.editSpeciesBtn)
        self.menuAnnotate.addAction(self.targetCommentBtn)
        self.menuAnnotate.addAction(self.frameCommentBtn)
        self.menuAnnotate.addSeparator()
        self.menuAnnotate.addAction(self.computeMatchBox)
        self.menuAnnotate.addAction(self.actionMatchThreshold)
        self.menuAnnotate.addAction(self.stereoOnlyCheckBox)
        self.menuAnnotate.addSeparator()
        self.menuAnnotate.addAction(self.recomputeBtn)
        self.menuAnnotate.addAction(self.trainBtn)
        self.menuAnnotate.addAction(self.clearGridBtn)
        self.menuSettings.addAction(self.actionCreate_New_Project)
        self.menuSettings.addAction(self.actionProfiles)
        self.menuSettings.addAction(self.actionSet_Active_Profiles)
        self.menuSettings.addAction(self.actionImport_Export_Profiles)
        self.menuSettings.addAction(self.actionGUI_settings)
        self.menuSettings.addAction(self.actionGrid_setup)
        self.menuSettings.addSeparator()
        self.menuSettings.addAction(self.actionviewApplicationDB)
        self.menuSettings.addAction(self.actionedit_DB_tables)
        self.menuHelp.addAction(self.actionAbout)

        self.retranslateUi(SEBASTES)

        self.imageStack.setCurrentIndex(1)
        self.speciesTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SEBASTES)
    # setupUi

    def retranslateUi(self, SEBASTES):
        SEBASTES.setWindowTitle(QCoreApplication.translate("SEBASTES", u"SEBASTES", None))
        self.actionLoad.setText(QCoreApplication.translate("SEBASTES", u"Open Deployment\u2026", None))
        self.actionLoad.setIconText(QCoreApplication.translate("SEBASTES", u"Open", None))
#if QT_CONFIG(tooltip)
        self.actionLoad.setToolTip(QCoreApplication.translate("SEBASTES", u"Open a deployment folder", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionLoad.setShortcut(QCoreApplication.translate("SEBASTES", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionExit.setText(QCoreApplication.translate("SEBASTES", u"Exit", None))
#if QT_CONFIG(shortcut)
        self.actionExit.setShortcut(QCoreApplication.translate("SEBASTES", u"Ctrl+Q", None))
#endif // QT_CONFIG(shortcut)
        self.actionProfiles.setText(QCoreApplication.translate("SEBASTES", u"Profiles\u2026", None))
#if QT_CONFIG(tooltip)
        self.actionProfiles.setToolTip(QCoreApplication.translate("SEBASTES", u"Create and edit profiles, species and metadata", None))
#endif // QT_CONFIG(tooltip)
        self.actionGUI_settings.setText(QCoreApplication.translate("SEBASTES", u"GUI Settings\u2026", None))
#if QT_CONFIG(tooltip)
        self.actionGUI_settings.setToolTip(QCoreApplication.translate("SEBASTES", u"Change fonts, line colors, etc.", None))
#endif // QT_CONFIG(tooltip)
        self.actionGrid_setup.setText(QCoreApplication.translate("SEBASTES", u"Grid Setup\u2026", None))
        self.actionSet_Active_Profiles.setText(QCoreApplication.translate("SEBASTES", u"Set Active Profiles\u2026", None))
#if QT_CONFIG(tooltip)
        self.actionSet_Active_Profiles.setToolTip(QCoreApplication.translate("SEBASTES", u"Set which profiles, metadata groups and species groups can be selected", None))
#endif // QT_CONFIG(tooltip)
        self.actionImport_Export_Profiles.setText(QCoreApplication.translate("SEBASTES", u"Import/Export Profiles\u2026", None))
#if QT_CONFIG(tooltip)
        self.actionImport_Export_Profiles.setToolTip(QCoreApplication.translate("SEBASTES", u"Import or export profiles from text files", None))
#endif // QT_CONFIG(tooltip)
        self.actionCreate_New_Project.setText(QCoreApplication.translate("SEBASTES", u"Create New Project\u2026", None))
#if QT_CONFIG(tooltip)
        self.actionCreate_New_Project.setToolTip(QCoreApplication.translate("SEBASTES", u"Create a new project", None))
#endif // QT_CONFIG(tooltip)
        self.actionviewApplicationDB.setText(QCoreApplication.translate("SEBASTES", u"View Application DB\u2026", None))
#if QT_CONFIG(tooltip)
        self.actionviewApplicationDB.setToolTip(QCoreApplication.translate("SEBASTES", u"View the application database (read only)", None))
#endif // QT_CONFIG(tooltip)
        self.actionedit_DB_tables.setText(QCoreApplication.translate("SEBASTES", u"Edit DB Tables\u2026", None))
#if QT_CONFIG(tooltip)
        self.actionedit_DB_tables.setToolTip(QCoreApplication.translate("SEBASTES", u"Edit the tables of the databases", None))
#endif // QT_CONFIG(tooltip)
        self.actionAbout.setText(QCoreApplication.translate("SEBASTES", u"About SEBASTES", None))
#if QT_CONFIG(tooltip)
        self.actionAbout.setToolTip(QCoreApplication.translate("SEBASTES", u"About this program", None))
#endif // QT_CONFIG(tooltip)
        self.copyBtn.setText(QCoreApplication.translate("SEBASTES", u"Copy Images To\u2026", None))
        self.copyBtn.setIconText(QCoreApplication.translate("SEBASTES", u"Copy Images", None))
#if QT_CONFIG(tooltip)
        self.copyBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Copy the images of the current frame to a folder", None))
#endif // QT_CONFIG(tooltip)
        self.labelCheck.setText(QCoreApplication.translate("SEBASTES", u"Show Labels", None))
        self.labelCheck.setIconText(QCoreApplication.translate("SEBASTES", u"Labels", None))
#if QT_CONFIG(tooltip)
        self.labelCheck.setToolTip(QCoreApplication.translate("SEBASTES", u"Show or hide the labels of the marks and measurements", None))
#endif // QT_CONFIG(tooltip)
        self.showDataCheck.setText(QCoreApplication.translate("SEBASTES", u"Show Data Table", None))
        self.showDataCheck.setIconText(QCoreApplication.translate("SEBASTES", u"Data Table", None))
#if QT_CONFIG(tooltip)
        self.showDataCheck.setToolTip(QCoreApplication.translate("SEBASTES", u"Show the table of the targets of this deployment", None))
#endif // QT_CONFIG(tooltip)
        self.closeupCheck.setText(QCoreApplication.translate("SEBASTES", u"Close-up Window", None))
        self.closeupCheck.setIconText(QCoreApplication.translate("SEBASTES", u"Close-up", None))
#if QT_CONFIG(tooltip)
        self.closeupCheck.setToolTip(QCoreApplication.translate("SEBASTES", u"Show a magnified view of the area under the cursor", None))
#endif // QT_CONFIG(tooltip)
        self.gridCheck.setText(QCoreApplication.translate("SEBASTES", u"Grid Overlay", None))
#if QT_CONFIG(tooltip)
        self.gridCheck.setToolTip(QCoreApplication.translate("SEBASTES", u"Draw a counting grid over the image", None))
#endif // QT_CONFIG(tooltip)
        self.epipolarCheck.setText(QCoreApplication.translate("SEBASTES", u"Epipolar Hints", None))
        self.epipolarCheck.setIconText(QCoreApplication.translate("SEBASTES", u"Epipolar", None))
#if QT_CONFIG(tooltip)
        self.epipolarCheck.setToolTip(QCoreApplication.translate("SEBASTES", u"While marking a pair, draw the line of the other image where the matching point must lie", None))
#endif // QT_CONFIG(tooltip)
        self.recordBtn.setText(QCoreApplication.translate("SEBASTES", u"Record", None))
#if QT_CONFIG(tooltip)
        self.recordBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Record: mark and measure fish. Stop recording to review the annotations", None))
#endif // QT_CONFIG(tooltip)
        self.measureBtn.setText(QCoreApplication.translate("SEBASTES", u"Measure Target", None))
        self.measureBtn.setIconText(QCoreApplication.translate("SEBASTES", u"Measure", None))
#if QT_CONFIG(tooltip)
        self.measureBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Draw the length of the selected target in both images", None))
#endif // QT_CONFIG(tooltip)
        self.linkBtn.setText(QCoreApplication.translate("SEBASTES", u"Link Target	Home", None))
        self.linkBtn.setIconText(QCoreApplication.translate("SEBASTES", u"Link", None))
#if QT_CONFIG(tooltip)
        self.linkBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Link the selected target to a target in the next frame (Home)", None))
#endif // QT_CONFIG(tooltip)
        self.delLinkBtn.setText(QCoreApplication.translate("SEBASTES", u"Delete Link", None))
#if QT_CONFIG(tooltip)
        self.delLinkBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Delete the link of the selected target", None))
#endif // QT_CONFIG(tooltip)
        self.editSpeciesBtn.setText(QCoreApplication.translate("SEBASTES", u"Edit Species\u2026", None))
        self.editSpeciesBtn.setIconText(QCoreApplication.translate("SEBASTES", u"Edit Species", None))
#if QT_CONFIG(tooltip)
        self.editSpeciesBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Change the species of targets", None))
#endif // QT_CONFIG(tooltip)
        self.targetCommentBtn.setText(QCoreApplication.translate("SEBASTES", u"Target Comment\u2026", None))
        self.targetCommentBtn.setIconText(QCoreApplication.translate("SEBASTES", u"Target Comment", None))
#if QT_CONFIG(tooltip)
        self.targetCommentBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Add a comment to the selected target", None))
#endif // QT_CONFIG(tooltip)
        self.frameCommentBtn.setText(QCoreApplication.translate("SEBASTES", u"Frame Comment\u2026", None))
        self.frameCommentBtn.setIconText(QCoreApplication.translate("SEBASTES", u"Frame Comment", None))
#if QT_CONFIG(tooltip)
        self.frameCommentBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Show or hide the comment window of this frame", None))
#endif // QT_CONFIG(tooltip)
        self.computeMatchBox.setText(QCoreApplication.translate("SEBASTES", u"Auto Match	A", None))
        self.computeMatchBox.setIconText(QCoreApplication.translate("SEBASTES", u"Auto Match", None))
#if QT_CONFIG(tooltip)
        self.computeMatchBox.setToolTip(QCoreApplication.translate("SEBASTES", u"Find the matching point in the other image automatically (A)", None))
#endif // QT_CONFIG(tooltip)
        self.actionMatchThreshold.setText(QCoreApplication.translate("SEBASTES", u"Match Threshold\u2026", None))
#if QT_CONFIG(tooltip)
        self.actionMatchThreshold.setToolTip(QCoreApplication.translate("SEBASTES", u"Largest error accepted for an automatic match", None))
#endif // QT_CONFIG(tooltip)
        self.stereoOnlyCheckBox.setText(QCoreApplication.translate("SEBASTES", u"Stereo Targets Only", None))
#if QT_CONFIG(tooltip)
        self.stereoOnlyCheckBox.setToolTip(QCoreApplication.translate("SEBASTES", u"Every click marks a stereo target, without holding Shift", None))
#endif // QT_CONFIG(tooltip)
        self.recomputeBtn.setText(QCoreApplication.translate("SEBASTES", u"Recompute 3D", None))
#if QT_CONFIG(tooltip)
        self.recomputeBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Recompute the 3D positions and lengths of all targets with the current calibration", None))
#endif // QT_CONFIG(tooltip)
        self.trainBtn.setText(QCoreApplication.translate("SEBASTES", u"Create Training Set", None))
#if QT_CONFIG(tooltip)
        self.trainBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Draw bounding boxes to create a training set", None))
#endif // QT_CONFIG(tooltip)
        self.clearGridBtn.setText(QCoreApplication.translate("SEBASTES", u"Clear Grid Data", None))
#if QT_CONFIG(tooltip)
        self.clearGridBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Delete the grid data of this frame", None))
#endif // QT_CONFIG(tooltip)
        self.monoRadio.setText(QCoreApplication.translate("SEBASTES", u"Mono", None))
#if QT_CONFIG(tooltip)
        self.monoRadio.setToolTip(QCoreApplication.translate("SEBASTES", u"Work with one camera only", None))
#endif // QT_CONFIG(tooltip)
        self.stereoRadio.setText(QCoreApplication.translate("SEBASTES", u"Stereo", None))
#if QT_CONFIG(tooltip)
        self.stereoRadio.setToolTip(QCoreApplication.translate("SEBASTES", u"Work with both cameras", None))
#endif // QT_CONFIG(tooltip)
        self.leftCaption.setText(QCoreApplication.translate("SEBASTES", u"Left camera", None))
#if QT_CONFIG(tooltip)
        self.adjLeftBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Adjust the left image (brightness, contrast, gamma)", None))
#endif // QT_CONFIG(tooltip)
        self.rightCaption.setText(QCoreApplication.translate("SEBASTES", u"Right camera", None))
#if QT_CONFIG(tooltip)
        self.adjRightBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Adjust the right image (brightness, contrast, gamma)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.imageSlider.setToolTip(QCoreApplication.translate("SEBASTES", u"Timeline: the ticks mark the frames that have measurements (tall) or targets (short)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.firstBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"First frame", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.prevSampleBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Previous sampled frame (Left)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.prevFrameBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Previous frame (Ctrl+Left)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.playBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Play or pause", None))
#endif // QT_CONFIG(tooltip)
        self.playBtn.setText(QCoreApplication.translate("SEBASTES", u"Play", None))
#if QT_CONFIG(tooltip)
        self.nextFrameBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Next frame (Ctrl+Right)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.nextSampleBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Next sampled frame (Right)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lastBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Last frame", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.lastFrameBtn.setToolTip(QCoreApplication.translate("SEBASTES", u"Go to the last sampled frame (the last frame with annotations)", None))
#endif // QT_CONFIG(tooltip)
        self.frameLabel.setText(QCoreApplication.translate("SEBASTES", u"Frame", None))
#if QT_CONFIG(tooltip)
        self.frameBox.setToolTip(QCoreApplication.translate("SEBASTES", u"Frame number: type a number and press Enter", None))
#endif // QT_CONFIG(tooltip)
        self.maxFrame.setText(QCoreApplication.translate("SEBASTES", u"/ 0", None))
#if QT_CONFIG(tooltip)
        self.maxFrame.setToolTip(QCoreApplication.translate("SEBASTES", u"Last frame number", None))
#endif // QT_CONFIG(tooltip)
        self.timeLabel.setText("")
#if QT_CONFIG(tooltip)
        self.timeLabel.setToolTip(QCoreApplication.translate("SEBASTES", u"Time in the video (hours:minutes:seconds.hundredths)", None))
#endif // QT_CONFIG(tooltip)
        self.everyLabel.setText(QCoreApplication.translate("SEBASTES", u"Every", None))
#if QT_CONFIG(tooltip)
        self.sampleRateEdit.setToolTip(QCoreApplication.translate("SEBASTES", u"Sample interval: the sample buttons and the Left and Right keys move this many frames", None))
#endif // QT_CONFIG(tooltip)
        self.offsetLabel.setText(QCoreApplication.translate("SEBASTES", u"frames, offset", None))
#if QT_CONFIG(tooltip)
        self.rateOffsetEdit.setToolTip(QCoreApplication.translate("SEBASTES", u"Offset of the sampled frames within the interval", None))
#endif // QT_CONFIG(tooltip)
        self.rateOffsetEdit.setPlaceholderText(QCoreApplication.translate("SEBASTES", u"0", None))
        self.playSpeedLabel.setText(QCoreApplication.translate("SEBASTES", u"Speed", None))
#if QT_CONFIG(tooltip)
        self.playSpeedLabel.setToolTip(QCoreApplication.translate("SEBASTES", u"Playback speed (frames per second)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.playSpeedSlider.setToolTip(QCoreApplication.translate("SEBASTES", u"Playback speed (frames per second)", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.playSpeedBox.setToolTip(QCoreApplication.translate("SEBASTES", u"Playback speed (frames per second). Type a value to move the slider.", None))
#endif // QT_CONFIG(tooltip)
        self.playSpeedBox.setSuffix(QCoreApplication.translate("SEBASTES", u" fps", None))
        self.menuFile.setTitle(QCoreApplication.translate("SEBASTES", u"File", None))
        self.menuView.setTitle(QCoreApplication.translate("SEBASTES", u"View", None))
        self.menuAnnotate.setTitle(QCoreApplication.translate("SEBASTES", u"Annotate", None))
        self.menuSettings.setTitle(QCoreApplication.translate("SEBASTES", u"Settings", None))
        self.menuHelp.setTitle(QCoreApplication.translate("SEBASTES", u"Help", None))
        self.metadataDockWidget.setWindowTitle(QCoreApplication.translate("SEBASTES", u"Habitat", None))
#if QT_CONFIG(tooltip)
        self.metadataCheckBox.setToolTip(QCoreApplication.translate("SEBASTES", u"Collect habitat metadata for every frame while recording", None))
#endif // QT_CONFIG(tooltip)
        self.metadataCheckBox.setText(QCoreApplication.translate("SEBASTES", u"Collect metadata", None))
        self.exclusiveRadioBox1.setTitle(QCoreApplication.translate("SEBASTES", u"Primary", None))
        self.radioButton1_1.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_2.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_3.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_4.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_5.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_6.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_7.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_8.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_9.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton1_10.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.exclusiveRadioBox2.setTitle(QCoreApplication.translate("SEBASTES", u"Secondary", None))
        self.radioButton2_1.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_2.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_3.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_4.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_5.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_6.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_7.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_8.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_9.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton2_10.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.exclusiveRadioBox3.setTitle(QCoreApplication.translate("SEBASTES", u"GroupBox", None))
        self.radioButton3_1.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.radioButton3_2.setText(QCoreApplication.translate("SEBASTES", u"RadioButton", None))
        self.metadataStickyBox.setText(QCoreApplication.translate("SEBASTES", u"retain selection", None))
        self.metadataTypeLabel2.setText(QCoreApplication.translate("SEBASTES", u"Coverage", None))
        self.label1_1.setText(QCoreApplication.translate("SEBASTES", u"TextLabel", None))
        self.label1_2.setText(QCoreApplication.translate("SEBASTES", u"TextLabel", None))
        self.label1_3.setText(QCoreApplication.translate("SEBASTES", u"TextLabel", None))
        self.label1_4.setText(QCoreApplication.translate("SEBASTES", u"TextLabel", None))
        self.label1_5.setText(QCoreApplication.translate("SEBASTES", u"TextLabel", None))
        self.metadataTypeLabel3.setText(QCoreApplication.translate("SEBASTES", u"Presence/abscence", None))
        self.checkBox1_1.setText(QCoreApplication.translate("SEBASTES", u"CheckBox", None))
        self.checkBox1_2.setText(QCoreApplication.translate("SEBASTES", u"CheckBox", None))
        self.checkBox1_3.setText(QCoreApplication.translate("SEBASTES", u"CheckBox", None))
        self.checkBox1_4.setText(QCoreApplication.translate("SEBASTES", u"CheckBox", None))
        self.checkBox1_5.setText(QCoreApplication.translate("SEBASTES", u"CheckBox", None))
        self.speciesDockWidget.setWindowTitle(QCoreApplication.translate("SEBASTES", u"Species", None))
        self.btn1.setText("")
        self.btn2.setText("")
        self.btn3.setText("")
        self.btn4.setText("")
        self.btn5.setText("")
        self.btn6.setText("")
        self.btn7.setText("")
        self.btn8.setText("")
        self.btn9.setText("")
        self.btn10.setText("")
        self.btn11.setText("")
        self.btn12.setText("")
        self.btn13.setText("")
        self.btn14.setText("")
        self.btn15.setText("")
        self.speciesTabWidget.setTabText(self.speciesTabWidget.indexOf(self.tab_1), QCoreApplication.translate("SEBASTES", u"Species List 1", None))
        self.btn16.setText("")
        self.btn17.setText("")
        self.btn18.setText("")
        self.btn19.setText("")
        self.btn20.setText("")
        self.btn21.setText("")
        self.btn22.setText("")
        self.btn23.setText("")
        self.btn24.setText("")
        self.btn25.setText("")
        self.btn26.setText("")
        self.btn27.setText("")
        self.btn28.setText("")
        self.btn29.setText("")
        self.btn30.setText("")
        self.speciesTabWidget.setTabText(self.speciesTabWidget.indexOf(self.tab_2), QCoreApplication.translate("SEBASTES", u"Species List 2", None))
        self.label_3.setText(QCoreApplication.translate("SEBASTES", u"Count in \n"
"frame", None))
        self.countInFrameLabel.setText("")
    # retranslateUi

