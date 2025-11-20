import sys
import json
import base64
import threading
import io
import speech_recognition as sr
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLineEdit, QTextEdit, QPushButton, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, QThread, pyqtSignal, QBuffer, QByteArray
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QScreen, QImage, QCursor

# --- CONFIGURATION ---
API_KEY = "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"
GPT_MODEL = "gpt-5.1"

# Try imports
try:
    import win32com.client

    SW_AVAILABLE = True
except ImportError:
    SW_AVAILABLE = False

try:
    from openai import OpenAI

    client = OpenAI(api_key=API_KEY)
    AI_AVAILABLE = True
except ImportError:
    print("OpenAI library not found. Please run: pip install openai")
    AI_AVAILABLE = False

# --- HIGH DPI SCALING FIX ---
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class AIWorker(QThread):
    response_received = pyqtSignal(str)  # Signal now returns just the text string

    def __init__(self, chat_history):
        super().__init__()
        self.chat_history = chat_history

    def run(self):
        if not AI_AVAILABLE:
            self.response_received.emit("Error: 'openai' library not installed.")
            return

        try:
            # System Prompt: Simple instruction, no JSON requirements anymore
            system_message = {
                "role": "system",
                "content": "You are an expert SolidWorks assistant. Help the user with CAD problems. Be concise."
            }

            # Combine system message with the full conversation history
            messages = [system_message] + self.chat_history

            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_completion_tokens=300
            )

            content = response.choices[0].message.content
            self.response_received.emit(content)

        except Exception as e:
            self.response_received.emit(f"AI Error: {str(e)}")


class DraggableChatWidget(QWidget):
    """The floating AI Chat window."""

    def __init__(self, ai_callback=None, drawing_callback=None, screenshot_callback=None):
        super().__init__(None)
        self.ai_callback = ai_callback
        self.drawing_callback = drawing_callback
        self.screenshot_callback = screenshot_callback
        self.is_minimized = False
        self.expanded_height = 500

        # MEMORY: Store the full conversation here
        self.chat_history = []

        self.initUI()
        self.oldPos = self.pos()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Styling: Dark Background, White Text
        self.setStyleSheet("""
            QWidget#ContentContainer {
                background-color: #282c34; 
                border: 2px solid #61afef;
                border-radius: 10px;
            }
            QLabel { color: white; font-weight: bold; background: transparent; border: none; }
            /* Chat History: Dark Grey Background, White Text */
            QTextEdit { background-color: #21252b; color: white; border: none; border-radius: 5px; padding: 5px; font-size: 14px;}
            QLineEdit { background-color: #3e4451; color: white; border: 1px solid #555; padding: 5px; border-radius: 5px; font-size: 14px;}
            QPushButton { background-color: #61afef; color: black; border-radius: 5px; padding: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #528bff; }
            QPushButton:checked { background-color: #ff6b6b; color: white; }
            QPushButton#MinBtn { background-color: transparent; color: white; border: none; font-size: 18px; }
            QPushButton#MinBtn:hover { color: #61afef; }
        """)

        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setObjectName("ContentContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        header_widget = QWidget()
        header_widget.setFixedHeight(40)
        header_widget.setStyleSheet(
            "background-color: #21252b; border-top-left-radius: 8px; border-top-right-radius: 8px; border-bottom: 1px solid #444;")

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 0, 10, 0)

        self.header = QLabel(f"AI Assistant ({GPT_MODEL})")
        self.min_btn = QPushButton("-")
        self.min_btn.setObjectName("MinBtn")
        self.min_btn.setFixedWidth(30)
        self.min_btn.clicked.connect(self.toggle_minimize)

        header_layout.addWidget(self.header)
        header_layout.addStretch()
        header_layout.addWidget(self.min_btn)
        container_layout.addWidget(header_widget)

        # Content
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(
            "background-color: #282c34; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; border-top: none;")

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        content_layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask AI...")
        self.input_field.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)

        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedWidth(30)
        self.mic_btn.clicked.connect(self.start_listening)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.mic_btn)
        content_layout.addLayout(input_layout)

        # Tools Layout
        tools_layout = QHBoxLayout()

        self.draw_btn = QPushButton("🖊️ Draw")
        self.draw_btn.setCheckable(True)
        self.draw_btn.clicked.connect(self.toggle_draw)

        self.snap_btn = QPushButton("📸 Snapshot")
        self.snap_btn.clicked.connect(self.take_snapshot)

        tools_layout.addWidget(self.draw_btn)
        tools_layout.addWidget(self.snap_btn)
        content_layout.addLayout(tools_layout)

        container_layout.addWidget(self.content_widget)
        outer_layout.addWidget(self.container)
        self.setLayout(outer_layout)

        self.resize(400, self.expanded_height)
        self.move(50, 50)

    def toggle_minimize(self):
        if self.is_minimized:
            self.content_widget.show()
            self.resize(400, self.expanded_height)
            self.min_btn.setText("-")
            self.is_minimized = False
        else:
            self.expanded_height = self.height()
            self.content_widget.hide()
            self.resize(400, 40)
            self.min_btn.setText("+")
            self.is_minimized = True

    def send_message(self, image_data=None):
        text = self.input_field.text()
        if not text and not image_data: return

        # 1. Display User Message in Chat UI (White Text)
        if image_data:
            self.chat_display.append(f"<span style='color:#61afef'><b>[Snapshot Sent]</b></span>")

        if text:
            self.chat_display.append(f"<span style='color:#98c379'><b>You:</b> {text}</span>")

        self.input_field.clear()
        self.chat_display.append("<span style='color:gray'><i>AI is analyzing...</i></span>")

        # 2. Build API Message Payload
        user_content = []
        if text:
            user_content.append({"type": "text", "text": text})
        if image_data:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_data}"}
            })

        # 3. Add to Memory
        new_message = {"role": "user", "content": user_content}
        self.chat_history.append(new_message)

        # 4. Send full history to AI
        if self.ai_callback:
            self.ai_callback(self.chat_history)

    def take_snapshot(self):
        if self.screenshot_callback:
            self.hide()
            QApplication.processEvents()
            import time;
            time.sleep(0.2)

            pixmap = self.screenshot_callback()

            self.show()

            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QBuffer.WriteOnly)
            pixmap.save(buffer, "PNG")
            base64_data = base64.b64encode(byte_array.data()).decode()

            self.send_message(image_data=base64_data)

    def receive_response(self, text):
        # Display AI response (White Text)
        self.chat_display.append(f"<span style='color:white'><b>AI:</b> {text}</span>")
        sb = self.chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())

        # Add AI response to memory so it remembers for next time
        self.chat_history.append({"role": "assistant", "content": text})

    def toggle_draw(self):
        if self.drawing_callback:
            self.drawing_callback(self.draw_btn.isChecked())

    def start_listening(self):
        threading.Thread(target=self._listen_thread).start()

    def _listen_thread(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                QTimer.singleShot(0, lambda: self.chat_display.append(
                    "<span style='color:#e5c07b'><i>Listening...</i></span>"))
                audio = r.listen(source, timeout=5)
                text = r.recognize_google(audio)
                QTimer.singleShot(0, lambda: self.input_field.setText(text))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.chat_display.append(
                f"<span style='color:#e06c75'><i>Audio Error: {e}</i></span>"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()


class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sw_bridge = None
        self.drawing_mode = False
        self.scribbles = []
        self.last_point = QPoint()

        self.initWindow()
        self.initChat()

    def initWindow(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setGeometry(QApplication.desktop().geometry())
        self.show()

    def initChat(self):
        self.chat_widget = DraggableChatWidget(ai_callback=self.process_ai_request,
                                               drawing_callback=self.set_drawing_mode,
                                               screenshot_callback=self.capture_screen)
        self.chat_widget.show()

    def set_drawing_mode(self, active):
        self.drawing_mode = active
        if active:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.setCursor(Qt.CrossCursor)
            self.raise_()
            self.activateWindow()
            self.update()
        else:
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.setCursor(Qt.ArrowCursor)
            self.scribbles = []
            self.update()

    def capture_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            return screen.grabWindow(0)
        return None

    def process_ai_request(self, chat_history):
        # Pass the full history to the worker
        self.worker = AIWorker(chat_history)
        self.worker.response_received.connect(self.handle_ai_response)
        self.worker.start()

    def handle_ai_response(self, response_text):
        self.chat_widget.receive_response(response_text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.drawing_mode:
            self.set_drawing_mode(False)
            if self.chat_widget:
                self.chat_widget.draw_btn.setChecked(False)

        elif event.key() == Qt.Key_Tab and self.drawing_mode:
            if self.chat_widget:
                self.chat_widget.take_snapshot()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Ghost background to catch clicks
        if self.drawing_mode:
            painter.setBrush(QBrush(QColor(0, 0, 0, 1)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())

        # Draw User Scribbles (No Highlight Box anymore)
        if self.scribbles:
            pen = QPen(QColor(255, 0, 0), 4)
            painter.setPen(pen)
            for line in self.scribbles:
                painter.drawLine(line[0], line[1])

    def mousePressEvent(self, event):
        if self.drawing_mode and event.button() == Qt.LeftButton:
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing_mode and event.buttons() & Qt.LeftButton:
            current_point = event.pos()
            self.scribbles.append((self.last_point, current_point))
            self.last_point = current_point
            self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OverlayWindow()
    sys.exit(app.exec_())
