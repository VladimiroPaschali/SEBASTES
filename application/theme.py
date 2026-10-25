"""Theme for SEBASTES: colour tokens, a small application style sheet and the icon set.

The theme follows the operating system light/dark mode and updates live when the user
switches it. The platform style is kept (windows11 on Windows, Fusion elsewhere) so the
widgets stay native; the style sheet only touches the parts listed in buildStyleSheet().

Usage (once, after creating the QApplication and before the main window):

    import theme
    theme.apply(app)
    theme.notifier.changed.connect(refreshIcons)    # emitted after the scheme changed
    button.setIcon(theme.icon('open-folder'))

The icons are SVG files in resources/icons, drawn with currentColor. They are rendered with
the colours of the current scheme, so they have to be requested again when notifier.changed
fires (the cache is cleared at that moment). The same goes for widgets that carry their own
style sheet from recordButtonStyle() / playButtonStyle().
"""
import os
import sys
from string import Template

from PySide6.QtCore import QByteArray, QObject, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QStyleFactory

iconDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'icons')
iconSizes = (16, 20, 24, 32, 48)

# base tokens; derived ones (hover, tints, ...) are added by tokens()
lightBase = dict(
    window='#f3f3f3', surface='#ffffff', border='#d6d6d6',
    text='#1b1b1b', textMuted='#616161',
    accent='#0067c0', accentSoft='#0067c0', accentText='#ffffff',
    record='#d32f2f', success='#2e7d32', warning='#b26a00', error='#c62828',
    overlay='#ffffff', overlayBg='#000000')

darkBase = dict(
    window='#1e1e1e', surface='#2b2b2b', border='#444444',
    text='#f0f0f0', textMuted='#a0a0a0',
    accent='#0078d4', accentSoft='#4aa3f2', accentText='#ffffff',
    record='#e53935', success='#5cb860', warning='#f2b134', error='#f0605d',
    overlay='#ffffff', overlayBg='#000000')


class ThemeNotifier(QObject):
    """Emits changed after the theme was re-applied for a new colour scheme."""
    changed = Signal()


notifier = ThemeNotifier()

iconCache = {}
connected = False
pending = False
appliedKey = None


def mix(first, second, amount):
    """Blend two colours: amount=1 gives first, amount=0 gives second. Returns '#rrggbb'."""
    a = QColor(first)
    b = QColor(second)
    r = round(a.red() * amount + b.red() * (1 - amount))
    g = round(a.green() * amount + b.green() * (1 - amount))
    bl = round(a.blue() * amount + b.blue() * (1 - amount))
    return QColor(r, g, bl).name()


def rgba(color, alpha):
    """QSS rgba() string for a colour and an alpha from 0 to 255."""
    c = QColor(color)
    return 'rgba(%d, %d, %d, %d)' % (c.red(), c.green(), c.blue(), alpha)


def isDark():
    """True when the system (or the Qt override) is in dark mode."""
    hints = QGuiApplication.styleHints()
    scheme = hints.colorScheme() if hints is not None else Qt.ColorScheme.Unknown
    if scheme == Qt.ColorScheme.Dark:
        return True
    if scheme == Qt.ColorScheme.Light:
        return False
    return QGuiApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128


def tokens(dark):
    """All colour tokens for a scheme: the base ones plus the derived ones."""
    c = dict(darkBase if dark else lightBase)
    c['dark'] = dark
    c['hover'] = mix(c['text'], c['window'], 0.08)
    c['pressed'] = mix(c['text'], c['window'], 0.14)
    c['accentTint'] = mix(c['accent'], c['window'], 0.30 if dark else 0.16)
    c['accentTintHover'] = mix(c['accent'], c['window'], 0.40 if dark else 0.24)
    c['accentBorder'] = mix(c['accent'], c['window'], 0.55)
    c['accentHover'] = mix(c['accent'], c['text'], 0.85)
    c['recordTint'] = mix(c['record'], c['window'], 0.14)
    c['recordHover'] = mix(c['record'], c['text'], 0.85)
    c['neutral'] = mix(c['text'], c['window'], 0.16)
    c['neutralHover'] = mix(c['text'], c['window'], 0.22)
    for level in ('success', 'warning', 'error'):
        c[level + 'Bg'] = mix(c[level], c['surface'], 0.18)
    return c


def colors():
    """Colour tokens for the current scheme: window, surface, border, text, textMuted, accent,
    accentText, record, success, warning, error, overlay (text over images), overlayBg, plus
    the derived hover, pressed, accentTint, ... used by the style sheet."""
    return tokens(isDark())


def buildPalette(c):
    """Explicit palette for styles that do not follow the system scheme (Fusion)."""
    p = QPalette(QColor(c['surface']), QColor(c['window']))
    roles = {
        QPalette.ColorRole.Window: c['window'],
        QPalette.ColorRole.WindowText: c['text'],
        QPalette.ColorRole.Base: c['surface'],
        QPalette.ColorRole.AlternateBase: mix(c['surface'], c['window'], 0.5),
        QPalette.ColorRole.Text: c['text'],
        QPalette.ColorRole.Button: c['surface'] if not c['dark'] else mix(c['surface'], c['text'], 0.93),
        QPalette.ColorRole.ButtonText: c['text'],
        QPalette.ColorRole.ToolTipBase: c['surface'],
        QPalette.ColorRole.ToolTipText: c['text'],
        QPalette.ColorRole.PlaceholderText: c['textMuted'],
        QPalette.ColorRole.Highlight: c['accent'],
        QPalette.ColorRole.HighlightedText: c['accentText'],
        QPalette.ColorRole.Link: c['accent'],
        QPalette.ColorRole.LinkVisited: mix(c['accent'], c['text'], 0.6),
    }
    for role, color in roles.items():
        p.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, role, QColor(c['textMuted']))
    return p


styleSheetTemplate = Template('''
QToolBar { spacing: 2px; padding: 2px 4px; border: none; border-bottom: 1px solid $border; }
QToolBar::separator { background: $border; width: 1px; height: 1px; margin: 5px 6px; }
QToolBar QToolButton { padding: 4px 8px; border: 1px solid transparent; border-radius: 6px;
                       background: transparent; color: $text; }
QToolBar QToolButton:hover { background: $hover; }
QToolBar QToolButton:pressed { background: $pressed; }
QToolBar QToolButton:checked { background: $accentTint; border-color: $accentBorder; }
QToolBar QToolButton:checked:hover { background: $accentTintHover; }
QToolBar QToolButton:disabled { color: $textMuted; background: transparent; border-color: transparent; }

QDockWidget::title { padding: 5px 8px; text-align: left; border-bottom: 1px solid $border; }

QStatusBar { border: none; border-top: 1px solid $border; }
QStatusBar::item { border: none; }
QStatusBar QLabel { color: $textMuted; }

QLabel#measureChip { background: $successBg; color: $success; border-radius: 9px; padding: 2px 10px;
                     font-weight: 600; }
QLabel#measureChip[level="ok"] { background: $successBg; color: $success; }
QLabel#measureChip[level="warn"] { background: $warningBg; color: $warning; }
QLabel#measureChip[level="bad"] { background: $errorBg; color: $error; }

QFrame#navBar { background: $surface; border: none; border-top: 1px solid $border; }

QSlider#imageSlider::groove:horizontal { height: 4px; background: $border; border-radius: 2px; }
QSlider#imageSlider::sub-page:horizontal { background: $accent; border-radius: 2px; }
QSlider#imageSlider::handle:horizontal { background: $accent; border: 2px solid $surface;
                                         width: 12px; height: 12px; margin: -6px 0; border-radius: 8px; }
QSlider#imageSlider::handle:horizontal:hover { background: $accentHover; }
QSlider#imageSlider::sub-page:horizontal:disabled { background: $textMuted; }
QSlider#imageSlider::handle:horizontal:disabled { background: $textMuted; }

QLabel#welcomeLabel { color: $overlay; background: $overlayRgba; border-radius: 10px;
                      padding: 14px 22px; font-size: 14pt; }
''')


def buildStyleSheet(c):
    """The application style sheet for a token set. Plain QPushButtons are not styled here:
    the species buttons carry their own style sheets."""
    values = dict(c)
    values['overlayRgba'] = rgba(c['overlayBg'], 150)
    return styleSheetTemplate.substitute(values)


def recordButtonStyle(c=None):
    """Style sheet for the Record button (QPushButton or QToolButton): outlined red,
    filled red with white text while checked (recording)."""
    c = c or colors()
    return Template('''
QAbstractButton { color: $record; font-weight: 600; padding: 4px 12px; background: transparent;
                  border: 2px solid $record; border-radius: 6px; }
QAbstractButton:hover { background: $recordTint; }
QAbstractButton:checked { color: #ffffff; background: $record; }
QAbstractButton:checked:hover { background: $recordHover; border-color: $recordHover; }
QAbstractButton:disabled { color: $textMuted; background: transparent; border-color: $border; }
''').substitute(c)


def playButtonStyle(c=None):
    """Style sheet for the Play button: accent filled, neutral while checked (playing)."""
    c = c or colors()
    return Template('''
QAbstractButton { color: $accentText; font-weight: 600; padding: 4px 12px; background: $accent;
                  border: 2px solid $accent; border-radius: 6px; }
QAbstractButton:hover { background: $accentHover; border-color: $accentHover; }
QAbstractButton:checked { color: $text; background: $neutral; border-color: $neutral; }
QAbstractButton:checked:hover { background: $neutralHover; border-color: $neutralHover; }
QAbstractButton:disabled { color: $textMuted; background: $window; border-color: $border; }
''').substitute(c)


def setChipLevel(label, level):
    """Set the level (ok, warn or bad) of a QLabel#measureChip and refresh its style."""
    label.setProperty('level', level)
    style = label.style()
    style.unpolish(label)
    style.polish(label)
    label.update()


def buildIcon(name, c, color='text', onColor='accentSoft'):
    """QIcon from resources/icons/<name>.svg for a token set. color and onColor are token
    names or '#rrggbb' strings for the normal and the checked state; disabled icons use
    textMuted. Empty icon if the file does not exist."""
    try:
        with open(os.path.join(iconDir, name + '.svg'), encoding='utf-8') as f:
            svg = f.read()
    except OSError:
        return QIcon()

    def renderer(colorName):
        hexColor = QColor(c.get(colorName, colorName)).name()
        return QSvgRenderer(QByteArray(svg.replace('currentColor', hexColor).encode('utf-8')))

    def pixmap(svgRenderer, size):
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        svgRenderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        return pm

    result = QIcon()
    muted = renderer('textMuted')
    for state, colorName in ((QIcon.State.Off, color), (QIcon.State.On, onColor)):
        normal = renderer(colorName)
        for size in iconSizes:
            pm = pixmap(normal, size)
            result.addPixmap(pm, QIcon.Mode.Normal, state)
            result.addPixmap(pm, QIcon.Mode.Active, state)
            result.addPixmap(pm, QIcon.Mode.Selected, state)
            result.addPixmap(pixmap(muted, size), QIcon.Mode.Disabled, state)
    return result


def icon(name, color='text', onColor='accentSoft'):
    """QIcon for an icon name in the colours of the current scheme (cached). color is the
    colour token of the normal state, onColor the one of the checked state (accentSoft by
    default, so checked toolbar buttons get a blue icon); both also accept '#rrggbb'."""
    dark = isDark()
    key = (name, dark, color, onColor)
    result = iconCache.get(key)
    if result is None:
        result = buildIcon(name, tokens(dark), color, onColor)
        iconCache[key] = result
    return result


def setPlatformStyle(app):
    """Keep the native look: windows11 on Windows, Fusion elsewhere."""
    if sys.platform == 'win32':
        if 'windows11' in QStyleFactory.keys() and app.style().objectName().lower() != 'windows11':
            app.setStyle('windows11')
    elif app.style().objectName().lower() != 'fusion':
        app.setStyle('Fusion')


def stateKey():
    """What the applied theme depends on: the scheme and, on Windows, the native palette."""
    palette = QGuiApplication.palette().color(QPalette.ColorRole.Window).name() if sys.platform == 'win32' else ''
    return (isDark(), palette)


def reapply(app, notify):
    global appliedKey
    c = colors()
    if sys.platform != 'win32':
        app.setPalette(buildPalette(c))
    app.setStyleSheet(buildStyleSheet(c))
    iconCache.clear()
    appliedKey = stateKey()
    if notify:
        notifier.changed.emit()


def refresh():
    """Re-apply the theme if the scheme (or the native palette) changed since the last time."""
    global pending
    pending = False
    app = QGuiApplication.instance()
    if app is not None and stateKey() != appliedKey:
        reapply(app, True)


def schedule(*args):
    """Qt emits colorSchemeChanged before it updates the native palette, and a style sheet
    polished with the old palette keeps the old colours. So the re-apply is deferred to the
    event loop and also triggered by the palette change (Windows)."""
    global pending
    if not pending:
        pending = True
        QTimer.singleShot(0, refresh)


def apply(app):
    """Set the style, palette (non-Windows) and style sheet for the current scheme and keep
    them in sync with the system scheme from now on."""
    global connected
    setPlatformStyle(app)
    reapply(app, False)
    if not connected:
        app.styleHints().colorSchemeChanged.connect(schedule)
        if sys.platform == 'win32':
            app.paletteChanged.connect(schedule)
        connected = True
