# Imports
import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QSpinBox,
    QHBoxLayout
)

from PySide6.QtCore import QTimer ,Qt ,QDateTime
from PySide6.QtGui import QShortcut, QKeySequence

# Variables
seconds = 0
time_running = False
mode = "focus"
session_started = False
session_count = 1
end_time = None

# Functions

def switch_session():
    global seconds
    global time_running
    global session_started
    global session_count
    global mode
    global end_time

    end_time = None

    if mode == "focus":
        QMessageBox.information(
            window,
            "Focus Complete",
            "Time for a Break",
        )
        mode = "break"
        mode_label.setText("Break")
        value_changer()
        update_display()
        start_button.setText("Take a break")

    else:
        QMessageBox.information(
            window,
            "Break Complete",
            "Time to Lock In",
        )
        mode = "focus"
        session_count += 1
        session_label.setText(f"Session #{session_count}")
        mode_label.setText("Focus")
        value_changer()
        update_display()
        start_button.setText("Start Focus")

def value_changer():
    global mode
    global seconds

    if mode == "focus":
        seconds = focus_input.value() * 60
    else:
        seconds = break_input.value() * 60
    

def update_timer():
    global seconds
    global mode
    global time_running
    global session_started
    global session_count
    
    now = QDateTime.currentDateTime()
    seconds = now.secsTo(end_time)

    if seconds <= 0:
        seconds = 0
        timer.stop()
        time_running = False
        session_started = False

        switch_session()

        return

    update_display()    

def update_display():
    global seconds

    minutes = seconds // 60
    remaining_seconds = seconds % 60
    title.setText(f"{minutes:02}:{remaining_seconds:02}")

def settings_changed():
    global seconds

    if not time_running:
        value_changer()

        update_display()

def toggle_focus():
    global time_running
    global seconds
    global session_started
    global end_time

    if time_running:
        timer.stop()
        time_running = False
        start_button.setText("Resume")
    
    else:
        if not session_started:
            value_changer()

            update_display()
            session_started = True
        
        end_time = QDateTime.currentDateTime().addSecs(seconds)

        timer.start(250)
        time_running = True
        start_button.setText("Pause")
    
def stop_func():
    global time_running
    global session_started
    global end_time
    global seconds

    timer.stop()
    time_running = False
    session_started = False
    end_time = None

    value_changer()
    update_display()

    start_button.setText("Start Focus" if mode == "focus" else "Take a break")

def reset_focus():
    global seconds
    global time_running
    global mode
    global session_started
    global session_count
    global end_time

    timer.stop()
    end_time = None

    time_running = False
    session_started = False
    session_count = 1
    mode = "focus"

    seconds = focus_input.value() * 60

    update_display()
    
    session_label.setText(f"Session #{session_count}")
    mode_label.setText("Focus")
    start_button.setText("Start Focus")


# Application
app = QApplication(sys.argv)


# Window
window = QWidget()

window.setStyleSheet("""
    QWidget {
            background-color: #202020;
            color: white;
    }
""")

window.setWindowTitle("Rainy")
window.resize(500, 400)


# Widgets
title = QLabel("00:00")
title.setStyleSheet("""
    QLabel {
        font-size: 60px;
        font-weight: bold;
    }
""")
title.setAlignment(Qt.AlignCenter)

settings_title = QLabel("Settings")
settings_title.setAlignment(Qt.AlignCenter)
settings_title.setStyleSheet("""
    QLabel{
        font-size: 15px;
        font-weight: bold;
    }
""")

mode_label = QLabel("Focus")
mode_label.setStyleSheet("font-size: 40px;")
mode_label.setAlignment(Qt.AlignCenter)

start_button = QPushButton("Start Focus")
start_button.setStyleSheet("""
    QPushButton {
        font-size: 18px;
        padding: 10px;
        border-radius: 10px;
        min-width: 200px;
        font-weight: bold;
        background-color: #3a3a3a;
        border: 1px solid #555555;
    }
    QPushButton:hover {
        background-color: #4a4a4a;
    }
    QPushButton:pressed{
        background-color: #2a2a2a;
    }
""")
start_button.setToolTip("Start or pause the timer")

reset_button = QPushButton("Reset")
reset_button.setStyleSheet("""
    QPushButton{
        font-size: 16px;
        padding: 8px;
        border-radius: 10px;
        min-width: 200px;
        background-color: #CF252E;
        border: 1px solid #555555;
    }
    QPushButton:hover{
        background-color: #F72D37;
    }
    QPushButton:pressed {
        background-color: #A11D24;
    }
""")
reset_button.setToolTip("Reset to Session #1")

focus_input = QSpinBox()
focus_input.setStyleSheet("""
    QSpinBox{
        font-size: 16px;
        padding: 6px;
        border-radius: 6px;
        min-width: 100px;
        background-color: #2B2B2B;
        border: 1px solid #555555;
    }
""")
focus_input.setToolTip("Enter minutes for Focus")
focus_label = QLabel("Focus (minutes)")
focus_label.setAlignment(Qt.AlignCenter)

break_input = QSpinBox()
break_input.setStyleSheet("""
    QSpinBox{
        font-size: 16px;
        padding: 6px;
        border-radius: 6px;
        min-width: 100px;
        background-color: #2B2B2B;
        border: 1px solid #555555;
    }
""")
break_input.setToolTip("Enter minutes for Break")
break_label = QLabel("Break (minutes)")
break_label.setAlignment(Qt.AlignCenter)

focus_input.setRange(1,120)
break_input.setRange(1,60)
focus_input.setValue(25)
break_input.setValue(5)

session_label = QLabel(f"Session #{session_count}")
session_label.setAlignment(Qt.AlignCenter)
session_label.setToolTip("Amount of cycles u completed")

stop_button = QPushButton("Stop")
stop_button.setStyleSheet("""
    QPushButton{
        font-size: 16px;
        padding: 8px;
        border-radius: 10px;
        min-width: 200px;
        background-color: #3a3a3a;
        border: 1px solid #555555;
    }
    QPushButton:hover{
        background-color: #4a4a4a;
    }
    QPushButton:pressed {
        background-color: #2a2a2a;
    }
""")
stop_button.setToolTip("Restart current session")


#Connections
start_button.clicked.connect(toggle_focus)
stop_button.clicked.connect(stop_func)
reset_button.clicked.connect(reset_focus)

shortcut_space = QShortcut(QKeySequence("Space"), window)
shortcut_space.activated.connect(toggle_focus)

focus_input.valueChanged.connect(settings_changed)
break_input.valueChanged.connect(settings_changed)

# Timer
timer = QTimer()
timer.timeout.connect(update_timer)


# Layout
settings_layout = QHBoxLayout()
layout = QVBoxLayout()
focus_layout = QVBoxLayout()
break_layout = QVBoxLayout()
stopReset_layout = QHBoxLayout()

layout.setContentsMargins(50 ,40 , 50, 40)
layout.setSpacing(15)


layout.addWidget(mode_label)
layout.addWidget(session_label)
layout.addWidget(title)

layout.addWidget(start_button)
stopReset_layout.addWidget(stop_button)
stopReset_layout.addWidget(reset_button)

focus_layout.addWidget(focus_label)
focus_layout.addWidget(focus_input)
layout.addLayout(stopReset_layout)

break_layout.addWidget(break_label)
break_layout.addWidget(break_input)

settings_layout.addLayout(focus_layout)
settings_layout.addLayout(break_layout)

layout.addWidget(settings_title)
layout.addLayout(settings_layout)

layout.addStretch()

window.setLayout(layout)
window.setStyleSheet("""
    QToolTip {
        font-size: 5px;
        background-color: #303030;
        color: white;
        border: 1px solid #555555;
        padding: 5px;
    }
    QWidget {
        background-color: #202020;
        color: white;
    }
""")


# Run
window.show()

sys.exit(app.exec())