import os
import random
import sys
import signal
from PyQt6 import QtCore, QtGui, QtWidgets
from messages import MESSAGES

def resource_path(filename: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def _collect_bunny_image_paths() -> list[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")
    candidates = [
        os.path.join(base_dir, "bunny1.png"),
    ]

    if os.path.isdir(assets_dir):
        for name in sorted(os.listdir(assets_dir)):
            if name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                candidates.append(os.path.join(assets_dir, name))

    existing = [p for p in candidates if os.path.isfile(p)]
    # Remove duplicates while preserving order.
    return list(dict.fromkeys(existing))

class BunnyWindow(QtWidgets.QWidget):
    RESIZE_ZONE = 24
    # Fixed bunny1 belly zone as (x, y, w, h) ratios in scaled image space.
    BUNNY1_TEXT_ZONE = (0.19, 0.50, 0.62, 0.27)

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint | 
            QtCore.Qt.WindowType.WindowStaysOnTopHint | 
            QtCore.Qt.WindowType.Tool
        )
        # Key for transparency
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Load the bunny image (but defer display updates until widgets exist)
        self._current_bunny_name = ""
        self.pixmap_orig = self._load_random_bunny_pixmap()
        self._scale = 1.0

        # 1. Bunny Image Layer
        self.bg_label = QtWidgets.QLabel(self)
        self.bg_label.setScaledContents(False)

        # 2. Text Overlay Layer
        self.message_label = QtWidgets.QLabel(self)
        self.message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setMargin(10)
        self.message_label.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        # Style the text for Rebecca
        font = QtGui.QFont("Segoe UI", 12, QtGui.QFont.Weight.Bold)
        self.message_label.setFont(font)
        self.message_label.setStyleSheet(
            "color: #7e3fb3; background: rgba(255, 255, 255, 140); border-radius: 12px; padding: 12px 6px;"
        )

        # Add a shadow to the text for readability
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QtGui.QColor(0, 0, 0, 200))  # Dark shadow for contrast
        shadow.setOffset(1, 1)
        self.message_label.setGraphicsEffect(shadow)

        self.message_label.raise_()

        # Close button (Top Right)
        self.close_btn = QtWidgets.QPushButton("×", self)
        self.close_btn.raise_()
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton { 
                background: rgba(200, 200, 200, 150); 
                border-radius: 12px; 
                color: black; 
                font-weight: bold;
            }
            QPushButton:hover { background: #ff7675; color: white; }
        """)
        self.close_btn.clicked.connect(self.close)

        self._old_pos = None
        self._resize_anchor = None
        self._start_scale = 1.0
        self._start_span = 1

        self._tint_color = None  # QColor or None for no tint

        # Initial display update (after widgets exist)
        self._update_pixmap_display()
        self._refresh_message()

    def _refresh_message(self):
        base_msg = self._get_random_message()
        # Ensures a clean signature at the bottom
        self.message_label.setText(f"\n{base_msg}\n\n-Michael")
        self._fit_message_font()

    def _fit_message_font(self):
        # Use exact rendered text (including intentional leading newline)
        # so fit calculations match what QLabel will actually draw.
        text = self.message_label.text()
        if not text:
            return

        area = self.message_label.contentsRect()
        # Leave extra room for QLabel margin + stylesheet padding + shadow blur.
        avail_w = max(20, area.width() - 16)
        avail_h = max(20, area.height() - 28)

        base_font = self.message_label.font()
        max_pt = max(10, min(36, int(min(avail_w, avail_h) * 0.22)))
        min_pt = 6

        for pt in range(max_pt, min_pt - 1, -1):
            test_font = QtGui.QFont(base_font)
            test_font.setPointSize(pt)
            fm = QtGui.QFontMetrics(test_font)
            rect = fm.boundingRect(
                QtCore.QRect(0, 0, avail_w, 10000),
                int(QtCore.Qt.AlignmentFlag.AlignCenter) | int(QtCore.Qt.TextFlag.TextWordWrap),
                text,
            )
            if rect.height() <= avail_h:
                self.message_label.setFont(test_font)
                return

        fallback_font = QtGui.QFont(base_font)
        fallback_font.setPointSize(min_pt)
        self.message_label.setFont(fallback_font)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Next message", self._refresh_message)
        menu.addSeparator()
        menu.addAction("Change color…", self._pick_tint_color)
        if self._tint_color is not None:
            menu.addAction("Reset color", self._reset_tint_color)
        menu.addSeparator()
        menu.addAction("Close", self.close)
        menu.exec(event.globalPos())

    def _pick_tint_color(self):
        initial = self._tint_color if self._tint_color is not None else QtGui.QColor(200, 150, 255)
        color = QtWidgets.QColorDialog.getColor(initial, self, "Choose bunny color")
        if color.isValid():
            self._tint_color = color
            self._update_pixmap_display()

    def _reset_tint_color(self):
        self._tint_color = None
        self._update_pixmap_display()

    def _apply_tint(self, pixmap: QtGui.QPixmap) -> QtGui.QPixmap:
        """Overlay a semi-transparent color on the bunny while preserving alpha."""
        if self._tint_color is None:
            return pixmap
        tinted = QtGui.QPixmap(pixmap.size())
        tinted.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_SourceAtop)
        overlay = QtGui.QColor(self._tint_color)
        overlay.setAlpha(150)
        painter.fillRect(tinted.rect(), overlay)
        painter.end()
        return tinted

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)
        # Keep the close button in the top-right corner
        self.close_btn.move(self.width() - self.close_btn.width() - 8, 8)

    def _load_random_bunny_pixmap(self) -> QtGui.QPixmap:
        image_paths = _collect_bunny_image_paths()
        if not image_paths:
            img = QtGui.QPixmap(300, 300)
            img.fill(QtCore.Qt.GlobalColor.transparent)
            self._current_bunny_name = ""
            return img

        path = random.choice(image_paths)
        self._current_bunny_name = os.path.basename(path)
        return QtGui.QPixmap(path)

    def _update_pixmap_display(self):
        if self.pixmap_orig.isNull():
            return

        # 1. Calculate new window size based on scale
        new_size = self.pixmap_orig.size() * self._scale
        self.resize(new_size)

        # 2. Scale the bunny image to match the window
        scaled = self.pixmap_orig.scaled(
            new_size,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.bg_label.setGeometry(0, 0, new_size.width(), new_size.height())
        self.bg_label.setPixmap(self._apply_tint(scaled))

        # 3. Update the mask and derive a tighter text-safe zone from bunny belly rows
        alpha_img = scaled.toImage().convertToFormat(QtGui.QImage.Format.Format_ARGB32)
        mask = QtGui.QBitmap.fromImage(alpha_img.createAlphaMask())
        region = QtGui.QRegion(mask)

        belly_rect = self._get_text_rect_for_current_bunny(alpha_img)
        if belly_rect.isValid() and belly_rect.width() > 40 and belly_rect.height() > 30:
            self.message_label.setGeometry(belly_rect)
            self.message_label.setMinimumSize(0, 0)
            self.message_label.setMaximumSize(16777215, 16777215)
        else:
            # Fallback when image alpha data is sparse/unusual.
            opaque_rect = region.boundingRect()
            left = opaque_rect.left() + int(opaque_rect.width() * 0.24)
            right = new_size.width() - opaque_rect.right() - 1 + int(opaque_rect.width() * 0.24)
            top = opaque_rect.top() + int(opaque_rect.height() * 0.38)
            bottom = new_size.height() - opaque_rect.bottom() - 1 + int(opaque_rect.height() * 0.26)
            w = max(80, new_size.width() - left - right)
            h = max(60, new_size.height() - top - bottom)
            self.message_label.setGeometry(max(0, left), max(0, top), w, h)

        btn_rect = self.close_btn.geometry().adjusted(-5, -5, 5, 5)
        region = region.united(QtGui.QRegion(btn_rect))

        msg_rect = self.message_label.geometry().adjusted(-4, -4, 4, 4)
        region = region.united(QtGui.QRegion(msg_rect))

        grip_rect = QtCore.QRect(
            self.width() - self.RESIZE_ZONE,
            self.height() - self.RESIZE_ZONE,
            self.RESIZE_ZONE,
            self.RESIZE_ZONE,
        )
        region = region.united(QtGui.QRegion(grip_rect))

        self.setMask(region)

        # Fit text to current message box dimensions.
        self._fit_message_font()

        self.message_label.raise_()
        self.close_btn.raise_()
        self.update()

    def _get_text_rect_for_current_bunny(self, img: QtGui.QImage) -> QtCore.QRect:
        if self._current_bunny_name == "bunny1.png":
            x, y, w, h = self.BUNNY1_TEXT_ZONE
            rect = QtCore.QRect(
                int(img.width() * x),
                int(img.height() * y),
                int(img.width() * w),
                int(img.height() * h),
            )
            if rect.width() > 40 and rect.height() > 30:
                return rect

        return self._compute_belly_text_rect(img)

    def _compute_belly_text_rect(self, img: QtGui.QImage) -> QtCore.QRect:
        w = img.width()
        h = img.height()
        if w <= 0 or h <= 0:
            return QtCore.QRect()

        y_start = int(h * 0.35)
        y_end = int(h * 0.88)

        best_y = -1
        best_left = 0
        best_right = 0
        best_width = -1

        for y in range(y_start, y_end):
            left = -1
            right = -1
            for x in range(w):
                if img.pixelColor(x, y).alpha() > 20:
                    left = x
                    break
            if left == -1:
                continue

            for x in range(w - 1, -1, -1):
                if img.pixelColor(x, y).alpha() > 20:
                    right = x
                    break

            if right > left:
                span = right - left + 1
                if span > best_width:
                    best_width = span
                    best_left = left
                    best_right = right
                    best_y = y

        if best_y == -1:
            return QtCore.QRect()

        center_x = (best_left + best_right) // 2
        rect_w = int(best_width * 0.64)
        rect_h = int(h * 0.26)

        x = center_x - rect_w // 2
        y = best_y - int(rect_h * 0.40)

        x = max(0, min(w - rect_w, x))
        y = max(0, min(h - rect_h, y))

        return QtCore.QRect(x, y, max(60, rect_w), max(50, rect_h))

    def wheelEvent(self, event: QtGui.QWheelEvent):
        # Simply scroll to resize (zoom)
        delta = event.angleDelta().y() / 120
        self._scale = max(0.4, min(3.0, self._scale + delta * 0.1))
        self._update_pixmap_display()
        event.accept()

    def paintEvent(self, event: QtGui.QPaintEvent):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 180), 2)
        painter.setPen(pen)
        x2 = self.width() - 6
        y2 = self.height() - 6
        painter.drawLine(x2 - 14, y2, x2, y2 - 14)
        painter.drawLine(x2 - 10, y2, x2, y2 - 10)
        painter.drawLine(x2 - 6, y2, x2, y2 - 6)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (QtCore.Qt.Key.Key_Space, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            self._refresh_message()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent):
        QtWidgets.QApplication.quit()
        sys.exit(0) # Force the terminal process to terminate

    def _get_random_message(self) -> str:
        # Pulls from your messages.py
        if not MESSAGES:
            return "This Bunny Loves You!"
        return random.choice(MESSAGES)

    # Mouse Events for dragging the bunny
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if pos.x() >= self.width() - self.RESIZE_ZONE and pos.y() >= self.height() - self.RESIZE_ZONE:
                self._resize_anchor = event.globalPosition().toPoint()
                self._start_scale = self._scale
                self._start_span = max(self.width(), self.height())
            else:
                self._old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._resize_anchor is not None:
            delta = event.globalPosition().toPoint() - self._resize_anchor
            d = max(delta.x(), delta.y())
            factor = 1.0 + (d / max(1, self._start_span))
            self._scale = max(0.4, min(3.0, self._start_scale * factor))
            self._update_pixmap_display()
            return

        pos = event.position().toPoint()
        if pos.x() >= self.width() - self.RESIZE_ZONE and pos.y() >= self.height() - self.RESIZE_ZONE:
            self.setCursor(QtCore.Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

        if self._old_pos is not None:
            delta = event.globalPosition().toPoint() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._old_pos = None
        self._resize_anchor = None

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL) 
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = BunnyWindow()
    window.show()

    sys.exit(app.exec())
