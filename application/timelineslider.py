'''
timelineslider is the slider under the images. It is a QSlider that also draws small ticks along its
groove at the frames that have data: a tall tick for a frame with a measurement, a short one for a
frame that only has targets. Clicking and dragging work as in any QSlider.
'''

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class TimelineSlider(QSlider):

    def __init__(self, parent=None):
        super(TimelineSlider, self).__init__(parent)
        #  slider positions of the frames with a measurement, and of the ones with targets only
        self.measuredMarks = []
        self.countedMarks = []
        self.measuredColor = QColor(178, 106, 0)
        self.countedColor = QColor(130, 130, 130)
        #  a thin outline in the color of the page keeps a tick visible on the groove and on the part already played
        self.outlineColor = QColor(255, 255, 255)

    def setMarks(self, measured, counted):
        '''
        setMarks sets the slider positions that get a tall tick (measured) and a short one (counted).
        '''
        measured = sorted(set(measured))
        counted = sorted(set(counted) - set(measured))
        if measured != self.measuredMarks or counted != self.countedMarks:
            self.measuredMarks = measured
            self.countedMarks = counted
            self.update()

    def setMarkColors(self, measured, counted, outline):
        self.measuredColor = QColor(measured)
        self.countedColor = QColor(counted)
        self.outlineColor = QColor(outline)
        self.update()

    def grooveGeometry(self):
        '''
        grooveGeometry returns the groove rectangle and the width of the handle: the center of the handle
        goes from the left end of the groove plus half the handle to the right end minus half the handle.
        '''
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        groove = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderGroove, self)
        handle = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderHandle, self)
        return groove, handle.width(), option.upsideDown

    def tickX(self, position, geometry=None):
        '''
        tickX returns the x coordinate (in the widget) of the center of the handle at a slider position.
        '''
        groove, handleWidth, upsideDown = geometry or self.grooveGeometry()
        span = max(groove.width() - handleWidth, 0)
        return groove.x() + handleWidth / 2.0 + QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), position, span, upsideDown)

    def paintEvent(self, event):
        super(TimelineSlider, self).paintEvent(event)
        if not self.measuredMarks and not self.countedMarks:
            return
        geometry = self.grooveGeometry()
        groove, handleWidth, upsideDown = geometry
        handleX = self.tickX(self.sliderPosition(), geometry)
        middle = groove.center().y() + 0.5
        #  ticks are placed on whole device pixels, so they stay sharp on a screen with scaling
        scale = self.devicePixelRatioF()
        snap = lambda value: round(value * scale) / scale
        pixel = 1.0 / scale
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        for marks, color, half in [(self.countedMarks, self.countedColor, 3.0), (self.measuredMarks, self.measuredColor, 6.0)]:
            last = None
            for position in marks:
                x = snap(self.tickX(position, geometry))
                if x == last:
                    continue
                last = x
                #  the handle is drawn over the tick it is on
                if abs(x - handleX) < handleWidth / 2.0 + 1:
                    continue
                top = snap(middle - half)
                bottom = snap(middle + half)
                painter.setBrush(self.outlineColor)
                painter.drawRect(QRectF(x - 2 * pixel, top - pixel, 4 * pixel, bottom - top + 2 * pixel))
                painter.setBrush(color)
                painter.drawRect(QRectF(x - pixel, top, 2 * pixel, bottom - top))
        painter.end()
