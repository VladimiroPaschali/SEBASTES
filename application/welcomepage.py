'''
welcomepage is the page shown in place of the two images until a deployment is loaded: the fish photo, the
name of the program, a button to open a deployment, the deployments opened last and the first steps.
The colours and fonts come from the style sheet in theme.py (objects welcome*, recentList).
'''

import os
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import theme

PHOTO_MAX_WIDTH = 520
RECENT_ROWS = 8

STEPS = ['Open a deployment: the folder with the left and right camera videos or images.',
         'Press Record and pick a species.',
         'Shift+click the head of a fish in the left image, then the same point in the right image. '
         'Click the tail the same way and the length is saved.']


class PhotoWidget(QWidget):
    '''
    PhotoWidget draws a picture as large as fits in the widget, with rounded corners.
    '''

    def __init__(self, path, parent=None):
        super(PhotoWidget, self).__init__(parent)
        self.photo = QPixmap(path)
        self.radius = 14
        self.scaledPhoto = None
        self.setMaximumWidth(PHOTO_MAX_WIDTH)
        self.setMinimumSize(200, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self):
        if self.photo.isNull():
            return QSize(PHOTO_MAX_WIDTH, 400)
        return QSize(PHOTO_MAX_WIDTH, int(PHOTO_MAX_WIDTH * self.photo.height() / self.photo.width()))

    def photoRect(self):
        '''
        photoRect returns where the picture goes: the largest rectangle with its proportions that fits.
        '''
        if self.photo.isNull():
            return QRectF()
        size = QSizeF(self.photo.width(), self.photo.height())
        size.scale(QSizeF(self.width(), self.height()), Qt.AspectRatioMode.KeepAspectRatio)
        rect = QRectF(QPointF(0, 0), size)
        rect.moveCenter(QPointF(self.width() / 2.0, self.height() / 2.0))
        return rect

    def paintEvent(self, event):
        rect = self.photoRect()
        if rect.isEmpty():
            return
        dpr = self.devicePixelRatioF()
        size = QSize(max(1, round(rect.width() * dpr)), max(1, round(rect.height() * dpr)))
        if self.scaledPhoto is None or self.scaledPhoto.size() != size:
            self.scaledPhoto = self.photo.scaled(size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.scaledPhoto.setDevicePixelRatio(dpr)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(rect, self.radius, self.radius)
        painter.setClipPath(path)
        painter.drawPixmap(rect.topLeft(), self.scaledPhoto)
        painter.end()


class RecentDelegate(QStyledItemDelegate):
    '''
    RecentDelegate draws a recent deployment as its name over the folder it is in.
    '''

    def sizeHint(self, option, index):
        metrics = option.fontMetrics
        return QSize(100, 2 * metrics.height() + 14)

    def paint(self, painter, option, index):
        item = QStyleOptionViewItem(option)
        self.initStyleOption(item, index)
        item.text = ''
        item.icon = QIcon()
        widget = option.widget
        style = widget.style() if widget is not None else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, item, painter, widget)
        colors = theme.colors()
        rect = option.rect.adjusted(10, 6, -10, -6)
        painter.save()
        nameFont = QFont(option.font)
        nameFont.setWeight(QFont.Weight.DemiBold)
        painter.setFont(nameFont)
        painter.setPen(QColor(colors['text']))
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         painter.fontMetrics().elidedText(index.data(Qt.ItemDataRole.DisplayRole), Qt.TextElideMode.ElideRight, rect.width()))
        folderFont = QFont(option.font)
        folderFont.setPointSizeF(max(option.font.pointSizeF() - 1, 7))
        painter.setFont(folderFont)
        painter.setPen(QColor(colors['textMuted']))
        folder = os.path.dirname(str(index.data(Qt.ItemDataRole.UserRole)).rstrip('/\\'))
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                         painter.fontMetrics().elidedText(folder, Qt.TextElideMode.ElideMiddle, rect.width()))
        painter.restore()


class WelcomePage(QWidget):

    #  the Open Deployment button was pressed
    openRequested = Signal()
    #  a recent deployment was double-clicked, or Enter was pressed on it: its folder
    recentRequested = Signal(str)

    def __init__(self, parent=None):
        super(WelcomePage, self).__init__(parent)
        baseDir = os.path.dirname(os.path.abspath(__file__))
        self.photo = PhotoWidget(os.path.join(baseDir, 'resources', 'help.jpg'), self)

        column = QWidget(self)
        column.setMinimumWidth(300)
        column.setMaximumWidth(420)
        box = QVBoxLayout(column)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)
        box.addStretch(1)

        self.title = QLabel('SEBASTES', column)
        self.title.setObjectName('welcomeTitle')
        self.subtitle = QLabel('Stereo video measurement of fish', column)
        self.subtitle.setObjectName('welcomeSubtitle')
        box.addWidget(self.title)
        box.addWidget(self.subtitle)
        box.addSpacing(22)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.openBtn = QPushButton('Open Deployment…', column)
        self.openBtn.setObjectName('welcomeOpen')
        self.openBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.openBtn.setToolTip('Choose the folder of a deployment')
        self.openBtn.clicked.connect(self.openRequested)
        hint = QLabel('Ctrl+O', column)
        hint.setObjectName('welcomeHint')
        row.addWidget(self.openBtn)
        row.addWidget(hint)
        row.addStretch(1)
        box.addLayout(row)
        box.addSpacing(22)

        self.recentHeading = QLabel('Recent deployments', column)
        self.recentHeading.setObjectName('welcomeHeading')
        box.addWidget(self.recentHeading)
        box.addSpacing(6)
        self.recentList = QListWidget(column)
        self.recentList.setObjectName('recentList')
        self.recentList.setItemDelegate(RecentDelegate(self.recentList))
        self.recentList.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.recentList.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.recentList.setMouseTracking(True)
        self.recentList.setToolTip('Double-click, or press Enter, to open it')
        self.recentList.itemActivated.connect(self.recentActivated)
        self.noRecent = QLabel('The deployments you open will be listed here.', column)
        self.noRecent.setObjectName('welcomeHint')
        self.noRecent.setWordWrap(True)
        box.addWidget(self.recentList)
        box.addWidget(self.noRecent)
        box.addSpacing(22)

        heading = QLabel('How to measure a fish', column)
        heading.setObjectName('welcomeHeading')
        box.addWidget(heading)
        box.addSpacing(6)
        steps = QGridLayout()
        steps.setContentsMargins(0, 0, 0, 0)
        steps.setHorizontalSpacing(10)
        steps.setVerticalSpacing(8)
        for number, text in enumerate(STEPS):
            badge = QLabel(str(number + 1), column)
            badge.setObjectName('welcomeStepNumber')
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedSize(24, 24)
            label = QLabel(text, column)
            label.setObjectName('welcomeStep')
            label.setWordWrap(True)
            steps.addWidget(badge, number, 0, Qt.AlignmentFlag.AlignTop)
            steps.addWidget(label, number, 1)
        steps.setColumnStretch(1, 1)
        box.addLayout(steps)
        box.addStretch(1)

        page = QHBoxLayout(self)
        page.setContentsMargins(32, 24, 32, 24)
        page.setSpacing(0)
        page.addStretch(1)
        page.addWidget(self.photo, 5)
        page.addSpacing(40)
        page.addWidget(column, 4)
        page.addStretch(1)
        self.setRecent([])

    def setRecent(self, folders):
        '''
        setRecent shows the folders of the deployments opened last, the newest first.
        '''
        self.recentList.clear()
        for folder in folders:
            item = QListWidgetItem(os.path.basename(folder.rstrip('/\\')) or folder)
            item.setData(Qt.ItemDataRole.UserRole, folder)
            item.setToolTip(folder)
            self.recentList.addItem(item)
        count = len(folders)
        #  the height of a row is the one RecentDelegate asks for; the frame and the list's padding come on top
        rowHeight = 2 * self.recentList.fontMetrics().height() + 14
        frame = 2 * self.recentList.frameWidth() + 10
        self.recentList.setMinimumHeight(min(count, 2) * rowHeight + frame)
        self.recentList.setMaximumHeight(count * rowHeight + frame)
        self.recentList.setVisible(count > 0)
        self.noRecent.setVisible(count == 0)

    def recentActivated(self, item):
        self.recentRequested.emit(item.data(Qt.ItemDataRole.UserRole))
