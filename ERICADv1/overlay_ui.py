import sys
import time
import threading
from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QLabel, 
                             QTextEdit, QHBoxLayout, QProgressBar, QApplication, QFrame, QGraphicsDropShadowEffect, QCheckBox, QComboBox)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor
import config

class SleekPanel(QWidget):
    """A professional, minimal, draggable floating panel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_overlay = parent
        self.is_dragging = False
        self.drag_start_position = QPoint()
        self.is_collapsed = False
        
        self.expanded_h = 650 
        self.collapsed_h = 40
        self.width_size = 320
        
        self.setStyleSheet("""
            QWidget#MainPanel {
                background-color: #2D2D2D;
                border: 1px solid #444;
                border-radius: 8px;
            }
            QLabel { color: #E0E0E0; border: none; font-family: 'Segoe UI', sans-serif; }
            QPushButton {
                background-color: #3E3E3E;
                border: 1px solid #555;
                border-radius: 4px;
                color: #DDD;
                padding: 4px;
            }
            QPushButton:hover { background-color: #4E4E4E; }
            QCheckBox { color: #AAA; spacing: 5px; font-size: 11px; }
            QCheckBox::indicator { width: 14px; height: 14px; }
            QComboBox {
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-radius: 4px;
                color: #EEE;
                padding: 4px;
            }
            QComboBox::drop-down { border: none; }
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-radius: 4px;
                color: #FFFFFF;
                padding: 5px;
                font-size: 12px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self.setObjectName("MainPanel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 10)
        self.layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        self.status_dot = QLabel("🟢")
        self.title = QLabel("ERICAD")
        self.title.setStyleSheet("font-weight: bold; font-size: 13px; letter-spacing: 1px; color: #4285F4;")
        
        self.btn_collapse = QPushButton("_")
        self.btn_collapse.setFixedSize(20, 20)
        self.btn_collapse.clicked.connect(self.toggle_collapse)
        self.btn_collapse.setStyleSheet("border: none; font-weight: bold;")
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.clicked.connect(parent.close_app)
        self.btn_close.setStyleSheet("border: none; color: #999; font-size: 10px;")
        
        header.addWidget(self.status_dot)
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.btn_collapse)
        header.addWidget(self.btn_close)
        self.layout.addLayout(header)
        
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        self.layout.addWidget(self.content)
        
        self.resize(self.width_size, self.expanded_h)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.pos().y() < 40:
                self.is_dragging = True
                self.drag_start_position = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.pos() - self.drag_start_position
            self.move(self.pos() + delta)

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.setCursor(Qt.ArrowCursor)

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.content.hide()
            self.resize(self.width_size, self.collapsed_h)
            self.btn_collapse.setText("□")
        else:
            self.content.show()
            self.resize(self.width_size, self.expanded_h)
            self.btn_collapse.setText("_")


class EricadOverlay(QWidget):
    update_status = pyqtSignal(str)
    update_chat = pyqtSignal(str, str) # (Sender, Message)
    enable_controls = pyqtSignal(bool)
    capture_done = pyqtSignal(bool)
    upload_ready = pyqtSignal(bool)

    def __init__(self, recorder, ai_client):
        super().__init__()
        self.recorder = recorder
        self.ai_client = ai_client
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setGeometry(QApplication.desktop().screenGeometry())
        
        self.drawing_lines = [] 
        self.is_drawing = False
        self.drawing_mode_enabled = False
        self.last_pt = QPoint()
        
        self.fade_duration = 3.0 
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        
        self.colors = [
            QColor("#FF00FF"),   # Magenta
            QColor("#00FFFF"),   # Cyan
            QColor("#FF4500"),   # Orange
            QColor("#39FF14"),   # Lime
            QColor("#FFFF00")    # Yellow
        ]
        self.color_index = 0
        self.current_stroke_color = self.colors[0]
        
        # State
        self.has_captured_context = False
        self.captured_duration = 0
        self.is_uploading = False 
        
        self.init_ui()
        
        self.update_status.connect(self.handle_status_update)
        self.update_chat.connect(self.append_chat_message)
        self.enable_controls.connect(self.set_controls_enabled)
        self.capture_done.connect(self.on_capture_complete)
        self.upload_ready.connect(self.on_upload_complete)

    def init_ui(self):
        self.panel = SleekPanel(self)
        screen_geo = self.geometry()
        self.panel.move(screen_geo.width() - 370, screen_geo.height() - 700)
        layout = self.panel.content_layout
        
        # 1. Drawing Toggle
        self.btn_mode = QPushButton("DRAWING: OFF  (`)")
        self.btn_mode.setCheckable(True)
        self.btn_mode.clicked.connect(self.toggle_mode)
        self.btn_mode.setStyleSheet("""
            QPushButton { background-color: #333; border: 1px solid #555; color: #888; padding: 8px; font-weight: bold; }
            QPushButton:checked { background-color: #880088; border: 1px solid #FF00FF; color: white; }
        """)
        layout.addWidget(self.btn_mode)
        
        # Options
        options_layout = QHBoxLayout()
        self.chk_fade = QCheckBox("Fading Ink")
        self.chk_fade.setChecked(True)
        self.chk_fade.stateChanged.connect(self.update)
        
        self.chk_cycle = QCheckBox("Cycle Colors")
        self.chk_cycle.setChecked(True)
        self.chk_cycle.stateChanged.connect(self.reset_color_if_unchecked)
        
        options_layout.addWidget(self.chk_fade)
        options_layout.addWidget(self.chk_cycle)
        layout.addLayout(options_layout)

        # 2. Context Selector
        self.lbl_history = QLabel("Select History:")
        layout.addWidget(self.lbl_history)
        self.combo_time = QComboBox()
        self.combo_time.addItems(["Screenshot Only", "Last 15 Seconds", "Last 45 Seconds", "Last 2 Minutes", "Last 5 Minutes"])
        self.combo_time.setCurrentIndex(2) # Default 45s
        layout.addWidget(self.combo_time)

        # 3. Capture Button
        self.btn_capture = QPushButton("1. Capture Context")
        self.btn_capture.clicked.connect(self.trigger_capture)
        self.btn_capture.setStyleSheet("""
            QPushButton { background-color: #4285F4; color: white; font-weight: bold; padding: 12px; font-size: 14px; }
            QPushButton:hover { background-color: #3367D6; }
        """)
        layout.addWidget(self.btn_capture)

        # 4. CHAT AREA (Visible after capture)
        self.chat_group = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_group)
        self.chat_layout.setContentsMargins(0,0,0,0)
        
        # Chat History (Read Only)
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_box.setStyleSheet("background-color: #222; color: #ddd; font-family: Consolas; font-size: 12px; border: none;")
        self.chat_layout.addWidget(self.chat_box)
        
        # Input Area
        input_row = QHBoxLayout()
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Ask a question...")
        self.prompt_input.setFixedHeight(50)
        input_row.addWidget(self.prompt_input)
        
        self.btn_send = QPushButton("Send")
        self.btn_send.setFixedSize(60, 50)
        self.btn_send.clicked.connect(self.trigger_send)
        self.btn_send.setStyleSheet("background-color: #228B22; color: white; font-weight: bold;")
        input_row.addWidget(self.btn_send)
        
        self.chat_layout.addLayout(input_row)
        layout.addWidget(self.chat_group)
        self.chat_group.hide() # Hide initially

        # Progress
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(2)
        self.progress.setStyleSheet("background: transparent; QProgressBar::chunk { background-color: #4285F4; }")
        layout.addWidget(self.progress)

        # Reset (New Chat)
        self.btn_reset = QPushButton("Start New Session (Reset)")
        self.btn_reset.clicked.connect(self.reset_workflow)
        self.btn_reset.setStyleSheet("background-color: #442222; color: #AA6666; font-size: 10px; padding: 4px; border: none;")
        layout.addWidget(self.btn_reset)

    def handle_status_update(self, text):
        if "Error" in text:
            self.panel.status_dot.setText("🔴")
            self.chat_box.append(f"\n[System]: {text}")
        elif "Done" in text or "Complete" in text:
            self.panel.status_dot.setText("🟢")
            self.panel.title.setText("ERICAD")
        elif "Wiped" in text:
            self.panel.status_dot.setText("🔵")
            self.chat_box.setText("[System] Memory Wiped. New Session Started.")
        elif "Uploading" in text:
            self.panel.status_dot.setText("☁️")
        else:
            self.panel.status_dot.setText("🟡")
            self.panel.title.setText(text.upper())

    def append_chat_message(self, sender, message):
        color = "#4285F4" if sender == "You" else "#39FF14"
        self.chat_box.append(f"<b style='color:{color}'>{sender}:</b> {message}<br>")

    def reset_workflow(self):
        """Resets the UI for a fresh capture."""
        self.has_captured_context = False
        self.is_uploading = False
        
        # Show Capture UI
        self.chat_group.hide()
        self.btn_capture.show()
        self.combo_time.show()
        self.lbl_history.show()
        
        # Clear Data
        self.chat_box.clear()
        self.prompt_input.clear()
        self.drawing_lines = []
        self.update() # Clear drawing
        
        # Reset Backend
        if hasattr(self.recorder, 'clear_memory'):
            self.recorder.clear_memory()
        self.ai_client.clear_session() # NEW method in ai_client
        
        self.handle_status_update("Wiped")
        # Re-enable Capture button explicitly
        self.btn_capture.setEnabled(True) 
        self.set_controls_enabled(True)

    def toggle_mode(self):
        self.drawing_mode_enabled = not self.drawing_mode_enabled
        self.btn_mode.setChecked(self.drawing_mode_enabled)
        
        if self.drawing_mode_enabled:
            self.btn_mode.setText("DRAWING: ON  (`)")
            self.setCursor(Qt.CrossCursor)
        else:
            self.btn_mode.setText("DRAWING: OFF  (`)")
            self.setCursor(Qt.ArrowCursor)
        self.update()

    def reset_color_if_unchecked(self):
        if not self.chk_cycle.isChecked():
            self.color_index = 0
            self.current_stroke_color = self.colors[0]

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_QuoteLeft: 
            self.toggle_mode()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if self.panel.geometry().contains(event.pos()): return
        
        if self.drawing_mode_enabled:
            if event.button() == Qt.LeftButton:
                self.is_drawing = True
                self.last_pt = event.pos()
                if self.chk_cycle.isChecked():
                    self.current_stroke_color = self.colors[self.color_index]
                else:
                    self.current_stroke_color = self.colors[0]
                if not self.animation_timer.isActive():
                    self.animation_timer.start(33)
            elif event.button() == Qt.RightButton:
                self.drawing_lines = []
                self.update()

    def mouseMoveEvent(self, event):
        if self.drawing_mode_enabled and self.is_drawing:
            curr_pt = event.pos()
            self.drawing_lines.append({
                'line': (self.last_pt, curr_pt),
                'time': time.time(),
                'color': self.current_stroke_color
            })
            self.last_pt = curr_pt

    def mouseReleaseEvent(self, event):
        if self.drawing_mode_enabled and event.button() == Qt.LeftButton:
            self.is_drawing = False
            if self.chk_cycle.isChecked():
                self.color_index = (self.color_index + 1) % len(self.colors)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.drawing_mode_enabled:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
            
        current_time = time.time()
        is_fading = self.chk_fade.isChecked()

        if is_fading:
            self.drawing_lines = [l for l in self.drawing_lines 
                                  if current_time - l['time'] < self.fade_duration]
        
        if is_fading and not self.drawing_lines and not self.is_drawing:
             self.animation_timer.stop()
        elif not is_fading and not self.is_drawing:
             self.animation_timer.stop()

        pen = QPen(Qt.SolidLine)
        pen.setWidth(4)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        for item in self.drawing_lines:
            line = item['line']
            alpha = 255
            if is_fading:
                age = current_time - item['time']
                life_remaining = 1.0 - (age / self.fade_duration)
                alpha = int(255 * life_remaining)
            
            final_color = QColor(item['color'])
            final_color.setAlpha(alpha)
            pen.setColor(final_color)
            painter.setPen(pen)
            painter.drawLine(line[0], line[1])

    # --- STEP 1: CAPTURE + START UPLOAD ---
    def trigger_capture(self):
        selection = self.combo_time.currentText()
        self.captured_duration = 45 
        
        if "Screenshot" in selection: self.captured_duration = 0 
        elif "15" in selection: self.captured_duration = 15
        elif "45" in selection: self.captured_duration = 45
        elif "2" in selection: self.captured_duration = 120
        elif "5" in selection: self.captured_duration = 300
        
        self.btn_capture.setEnabled(False)
        self.progress.setRange(0, 0)
        self.update_status.emit(f"Capturing...")
        threading.Thread(target=self._capture_and_upload_backend, args=(self.captured_duration,)).start()

    def _capture_and_upload_backend(self, duration):
        try:
            # 1. Save Files Locally
            context_path = config.TEMP_VIDEO_PATH
            if duration == 0:
                context_path = "ericad_snapshot.jpg"
                success = self.recorder.save_snapshot(context_path)
            else:
                success = self.recorder.save_video(duration, context_path)

            if not success: raise Exception("Buffer empty")

            screen = QApplication.primaryScreen()
            screenshot = screen.grabWindow(0)
            screenshot.save(config.TEMP_DRAWING_PATH)
            
            self.capture_done.emit(True)
            
            # 2. Start Upload Immediately (Optimistic)
            self.update_status.emit("Uploading...")
            self.is_uploading = True
            
            video_to_upload = context_path if duration > 0 else None
            self.ai_client.upload_context(video_to_upload, config.TEMP_DRAWING_PATH)
            
            self.upload_ready.emit(True)
            self.update_status.emit("Context Ready")

        except Exception as e:
            self.update_status.emit("Error")
            self.update_chat.emit("System", str(e))
            self.capture_done.emit(False)

    def on_capture_complete(self, success):
        if success:
            self.has_captured_context = True
            # Hide capture controls to make room for chat
            self.btn_capture.hide()
            self.combo_time.hide()
            self.lbl_history.hide()
            
            self.chat_group.show()
            self.prompt_input.setFocus()
            self.btn_send.setEnabled(True) 
        else:
            self.btn_capture.setEnabled(True)
            self.progress.hide()

    def on_upload_complete(self, success):
        self.is_uploading = False
        self.progress.hide()

    # --- STEP 2: SEND PROMPT (CHAT) ---
    def trigger_send(self):
        user_q = self.prompt_input.toPlainText()
        if not user_q and not self.drawing_lines: 
             self.response_box.setText("Please type a question or draw something.")
             return

        # UPDATE CHAT AND CLEAR INPUT IMMEDIATELY
        self.append_chat_message("You", user_q)
        self.prompt_input.clear()

        self.btn_send.setEnabled(False)
        self.progress.show()
        self.progress.setRange(0, 0)
        
        threading.Thread(target=self._send_backend, args=(user_q,)).start()

    def _send_backend(self, user_q):
        try:
            self.update_status.emit("Thinking...")
            # Uses the persistent chat session
            response = self.ai_client.ask_question(user_q)
            
            self.update_chat.emit("Ericad", response)
            self.update_status.emit("Done")
            
        except Exception as e:
            self.update_status.emit("Error")
            self.update_chat.emit("System", str(e))
        finally:
            self.enable_controls.emit(True)

    def set_controls_enabled(self, enabled):
        self.btn_send.setEnabled(enabled)
        if enabled: self.progress.hide()

    def close_app(self):
        self.recorder.stop()
        self.close()