# Imports
import sys
import subprocess
import json
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QSpinBox,
    QCheckBox,
    QHBoxLayout,
    QDialog,
    QFormLayout,
    QSystemTrayIcon,
    QMenu,
    QScrollArea,    
    QFrame,
    QLineEdit,
    QTextEdit
)
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QPieSeries,
    QPieSlice,
    QBarCategoryAxis,
    QValueAxis,
)
from PySide6.QtCore import QTimer ,Qt ,QDateTime ,QUrl
from PySide6.QtGui import QShortcut, QKeySequence, QIcon, QPainter
from PySide6.QtMultimedia import QSoundEffect
from pathlib import Path
import database
from datetime import datetime

# Variables
seconds = 0
time_running = False
mode = "Focus"
session_started = False
session_count = 1
end_time = None
session_before_long_break = 3
long_break_duration = 15
lb_count = 0
button_pressed_sound_rule = True
send_notification_rule = True
auto_start_focus = False
auto_start_break = False
tray_rule = False

# Activity tracking
activity_name = ""
activity_description = ""
activity_focus_seconds = 0
activity_focus_periods = 0
activity_breaks_completed = 0
activity_started_at = None

#Paths
def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent

    return base_path / relative_path

def settings_path():
    if sys.platform == "win32":
        settings_dir = Path.home() / "AppData" / "Roaming" / "Rainy"

    elif sys.platform == "darwin":
        settings_dir = Path.home() / "Library" / "Application Support" / "Rainy"

    else:
        settings_dir = Path.home() / ".config" / "Rainy"

    settings_dir.mkdir(parents=True, exist_ok=True)

    return settings_dir / "settings.json"

ICON_PATH = resource_path("icon.png")
SETTINGS_FILE = settings_path()
DATABASE_FILE = SETTINGS_FILE.with_name("rainy.db")

database.initialize_database(DATABASE_FILE)

# Functions

def switch_session():
    global seconds
    global time_running
    global session_started
    global session_count
    global mode
    global end_time
    global lb_count
    global session_before_long_break
    global activity_focus_periods
    global activity_focus_seconds
    global activity_breaks_completed

    end_time = None

    if mode == "Focus":
        focus_end_sound.play()
        lb_count += 1
        activity_focus_seconds += focus_input.value() * 60
        activity_focus_periods += 1

        if lb_count % session_before_long_break == 0:
            mode = "Long_Break"
            mode_label.setText("Long Break")
            start_button.setText("Take a long break")
        else:
            mode = "Break"
            mode_label.setText("Break")
            start_button.setText("Take a break")
        
        if mode == "Break":
            send_notification_rule_func(
                    "Focus Complete",
                    "Time for a Break"
                )
            if auto_start_break:
                toggle_focus()
        else:
            send_notification_rule_func(
                    "Focus Complete",
                    "Time for a Long Break"
                )
            if auto_start_break:
                toggle_focus()


        value_changer()
        update_display()

    else:
        activity_breaks_completed += 1
        break_end_sound.play()
        send_notification_rule_func(
                "Break Complete",
                "Time to Lock In"
            )

        mode = "Focus"
        session_count += 1
        session_label.setText(f"Session #{session_count}")
        mode_label.setText(mode)
        value_changer()
        update_display()
        start_button.setText("Start Focus")
        if auto_start_focus:
            toggle_focus()

def value_changer():
    global mode
    global seconds

    if mode == "Focus":
        seconds = focus_input.value() * 60
    elif mode == "Break":
        seconds = break_input.value() * 60
    else:
        seconds = long_break_duration * 60

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
    global time_running, seconds, session_started, end_time, activity_started_at

    if time_running:
        timer.stop()
        time_running = False
        start_button.setText("Resume")

    else:
        if not session_started:
            if mode == "Focus" and activity_started_at is None:
                activity_started_at = datetime.now().isoformat(
                    timespec="seconds"
                )

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

    if mode == "Focus":
        start_button.setText("Start Focus")
    elif mode == "Break":
        start_button.setText("Take a break")
    elif mode == "Long_Break":
        start_button.setText("Take a long break")

def reset_focus():
    global seconds
    global time_running
    global mode
    global session_started
    global session_count
    global end_time
    global lb_count

    timer.stop()
    end_time = None

    time_running = False
    session_started = False
    session_count = 1
    lb_count = 0
    mode = "Focus"

    seconds = focus_input.value() * 60

    update_display()
    
    session_label.setText(f"Session #{session_count}")
    mode_label.setText("Focus")
    start_button.setText("Start Focus")

def finish_activity():
    global activity_name, activity_description, activity_focus_seconds, activity_focus_periods, activity_breaks_completed, activity_started_at

    if activity_focus_periods == 0:
        QMessageBox.information(
            window,
            "No Activity",
            "Complete at least one focus period before saving an activity."
        )
        return

    dialog = QDialog(window)
    dialog.setWindowTitle("Finish Activity")
    dialog.setMinimumWidth(350)

    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel("What did you work on?"))

    name_input = QLineEdit()
    name_input.setPlaceholderText("e.g. Physics - Electrostatics")
    layout.addWidget(name_input)

    layout.addWidget(QLabel("Description (optional)"))

    description_input = QTextEdit()
    description_input.setPlaceholderText(
        "Describe what you worked on..."
    )
    description_input.setFixedHeight(100)
    layout.addWidget(description_input)

    layout.addWidget(QLabel(
        f"Focus periods: {activity_focus_periods} | "
        f"Breaks: {activity_breaks_completed}"
    ))

    buttons = QHBoxLayout()
    save_button = QPushButton("Save Activity")
    cancel_button = QPushButton("Cancel")

    buttons.addWidget(cancel_button)
    buttons.addWidget(save_button)
    layout.addLayout(buttons)

    cancel_button.clicked.connect(dialog.reject)

    def save():
        global activity_name, activity_description, activity_focus_seconds, activity_focus_periods, activity_breaks_completed, activity_started_at

        name = name_input.text().strip()

        if not name:
            QMessageBox.warning(
                dialog,
                "Missing Name",
                "Please enter an activity name."
            )
            return

        activity_name = name
        activity_description = description_input.toPlainText().strip()
        started_at = activity_started_at or datetime.now().isoformat(
            timespec="seconds"
        )
        database.save_activity(
            DATABASE_FILE,
            activity_name,
            activity_description,
            activity_focus_seconds,
            activity_focus_periods,
            activity_breaks_completed,
            started_at,
            datetime.now().isoformat(timespec="seconds"),
        )

        activity_name = ""
        activity_description = ""
        activity_focus_seconds = 0
        activity_focus_periods = 0
        activity_breaks_completed = 0
        activity_started_at = None

        QMessageBox.information(
            dialog,
            "Activity Saved",
            f"'{name}' was saved successfully!"
        )
        dialog.accept()

    save_button.clicked.connect(save)
    dialog.exec()

def create_daily_focus_chart():
    daily_data = database.get_daily_focus(DATABASE_FILE)

    chart = QChart()
    chart.setTitle("Daily Focus Time")
    chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
    chart.setBackgroundRoundness(12)
    chart.setBackgroundBrush(
    window.palette().window()
    )

    chart.setTitleBrush(
        window.palette().windowText()
    )

    bar_set = QBarSet("Focus Time (minutes)")

    categories = []

    for day, minutes in daily_data:
        categories.append(day)
        bar_set.append(minutes)

    series = QBarSeries()
    series.append(bar_set)
    chart.addSeries(series)

    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    series.attachAxis(axis_x)

    axis_y = QValueAxis()
    axis_y.setTitleText("Minutes")
    axis_y.setLabelFormat("%d")
    axis_y.setMin(0)
    axis_y.setMax(max(
        (minutes for _, minutes in daily_data),
        default=60
    ) + 10)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(axis_y)

    chart_view = QChartView(chart)
    chart_view.setStyleSheet("background: transparent; border: none;")
    chart_view.setBackgroundBrush(
        window.palette().window()
    )
    chart_view.setRenderHint(
        QPainter.RenderHint.Antialiasing
    )

    return chart_view

def create_session_chart():
    totals = database.get_session_totals(DATABASE_FILE)

    chart = QChart()
    chart.setTitle("Focus vs. Breaks")
    chart.setBackgroundRoundness(12)
    chart.setBackgroundBrush(window.palette().window())
    chart.setTitleBrush(window.palette().windowText())

    chart.legend().setLabelColor(
        window.palette().windowText().color()
    )

    series = QPieSeries()

    focus = totals["focus_periods"]
    breaks = totals["breaks"]

    if focus == 0 and breaks == 0:
        return None

    focus_slice = series.append(
        f"Focus ({focus})",
        focus
    )

    break_slice = series.append(
        f"Breaks ({breaks})",
        breaks
    )

    focus_slice.setLabelVisible(True)
    break_slice.setLabelVisible(True)

    text_color = window.palette().windowText().color()

    focus_slice.setLabelColor(text_color)
    break_slice.setLabelColor(text_color)

    chart.addSeries(series)
    chart.legend().setVisible(True)
    chart.legend().setAlignment(
        Qt.AlignmentFlag.AlignBottom
    )

    chart_view = QChartView(chart)
    chart_view.setMinimumHeight(280)
    chart_view.setRenderHint(
        QPainter.RenderHint.Antialiasing
    )

    return chart_view

def open_stats():
    stats_window = QDialog(window)
    stats_window.setWindowTitle("Your Stats")
    stats_window.setMinimumSize(700, 800)

    layout = QVBoxLayout(stats_window)

    chart_container = QFrame()
    chart_container.setObjectName("chartContainer")
    chart_container.setStyleSheet("""
        QFrame#chartContainer {
            border: 1px solid palette(mid);
            border-radius: 10px;
        }
    """)

    chart_layout = QHBoxLayout(chart_container)
    chart_layout.setContentsMargins(8, 8, 8, 8)

    heading = QLabel("Activity History")
    heading.setStyleSheet("font-size: 20px; font-weight: bold;")
    layout.addWidget(heading)

    activities = database.get_activities(DATABASE_FILE)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.Shape.NoFrame)

    activity_container = QWidget()
    activity_layout = QVBoxLayout(activity_container)
    activity_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    scroll_area.setWidget(activity_container)

    if activities:
        chart_view = create_daily_focus_chart()
        chart_view.setMinimumHeight(300)
        chart_layout.addWidget(chart_view)

        session_chart = create_session_chart()
        if session_chart is not None:
            chart_layout.addWidget(session_chart)

        layout.addWidget(chart_container)
    else:
        layout.addWidget(
            QLabel("Complete an activity to see your focus chart!")
        )

    if not activities:
        activity_layout.addWidget(
            QLabel("No activities saved yet. Finish an activity to see it here!")
        )
    else:
        for activity in activities:
            activity_card = QFrame()
            activity_card.setObjectName("activityCard")
            activity_card.setStyleSheet("""
                QFrame#activityCard {
                    border: 1px solid palette(mid);
                    border-radius: 12px;
                    padding: 8px;
                }
            """)

            card_layout = QVBoxLayout(activity_card)

            name_label = QLabel(activity["activity_name"])
            name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            card_layout.addWidget(name_label)

            if activity["description"]:
                description_label = QLabel(activity["description"])
                description_label.setWordWrap(True)
                card_layout.addWidget(description_label)

            focus_minutes = activity["focus_seconds"] // 60

            details_label = QLabel(
                f"Focus time: {focus_minutes} minutes | "
                f"Focus periods: {activity['focus_periods']} | "
                f"Breaks: {activity['breaks_completed']}"
            )
            card_layout.addWidget(details_label)

            date_label = QLabel(f"Completed: {activity['ended_at']}")
            date_label.setStyleSheet("color: gray; font-size: 11px;")
            card_layout.addWidget(date_label)

            activity_layout.addWidget(activity_card)
    layout.addWidget(scroll_area)
    layout.addStretch()
    stats_window.exec()

def open_settings():
    global long_break_duration
    global session_before_long_break
    global send_notification_rule

    settings_window = QDialog(window)
    settings_window.setWindowTitle("Rainy Settings")
    settings_window.setFixedSize(300, 250)

    layout = QFormLayout()

    #Inputs
    long_break_spinbox = QSpinBox()
    long_break_spinbox.setRange(1,120)
    long_break_spinbox.setValue(long_break_duration)

    session_before_lb_spinbox = QSpinBox()
    session_before_lb_spinbox.setRange(1,6)
    session_before_lb_spinbox.setValue(session_before_long_break)

    button_pressed_sound_rule_cb = QCheckBox()
    button_pressed_sound_rule_cb.setChecked(button_pressed_sound_rule)
    
    send_notification_rule_cb = QCheckBox()
    send_notification_rule_cb.setChecked(send_notification_rule)

    auto_start_focus_cb = QCheckBox()
    auto_start_focus_cb.setChecked(auto_start_focus)

    auto_start_break_cb = QCheckBox()
    auto_start_break_cb.setChecked(auto_start_break)

    tray_cb = QCheckBox()
    tray_cb.setChecked(tray_rule)

    save_button = QPushButton("Save 💾")

    layout.addRow("Long Break:", long_break_spinbox)
    layout.addRow("Long Break Limit:", session_before_lb_spinbox)
    layout.addRow("Sound on button press", button_pressed_sound_rule_cb)
    layout.addRow("Send Notifications", send_notification_rule_cb)
    layout.addRow("Auto start Focus:", auto_start_focus_cb)
    layout.addRow("Auto start Break:", auto_start_break_cb)
    layout.addRow("Minimize to system tray when closed:", tray_cb)
    layout.addRow("Save:", save_button)

    def save_settings():
        global long_break_duration
        global session_before_long_break
        global button_pressed_sound_rule
        global send_notification_rule
        global auto_start_focus
        global auto_start_break
        global tray_rule

        long_break_duration = long_break_spinbox.value()
        session_before_long_break = session_before_lb_spinbox.value()
        button_pressed_sound_rule = button_pressed_sound_rule_cb.isChecked()
        send_notification_rule = send_notification_rule_cb.isChecked()
        auto_start_focus = auto_start_focus_cb.isChecked()
        auto_start_break = auto_start_break_cb.isChecked()
        tray_rule = tray_cb.isChecked()

        save_user_settings()

        if not time_running:
            value_changer()
            update_display()

        

        settings_window.close()

    save_button.clicked.connect(save_settings)

    settings_window.setLayout(layout)
    settings_window.exec()

def debug_timer():
    global seconds
    global session_started
    global end_time
    global time_running

    timer.stop()

    seconds = 2
    session_started = True
    time_running = False
    end_time = None

    update_display()
    start_button.setText("Start")

def button_pressed():
    if button_pressed_sound_rule:
        button_pressed_sound.play()

def send_notif(title, message):
    if sys.platform == "linux":
        subprocess.run([
            "notify-send",
            "--app-name=Rainy",
            f"--icon={ICON_PATH}",
            title,
            message
        ])

    elif sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        subprocess.run(
            [
                "powershell",
                "-Command",
                f'''
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                $notification = New-Object System.Windows.Forms.NotifyIcon
                $notification.Icon = [System.Drawing.SystemIcons]::Information
                $notification.Visible = $true
                $notification.ShowBalloonTip(5000, "{title}", "{message}", "Info")
                Start-Sleep -Seconds 5
                $notification.Dispose()
                '''
            ],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    elif sys.platform == "darwin":
        subprocess.run([
            "osascript",
            "-e",
            f'display notification "{message}" with title "{title}"'
        ])

def send_notification_rule_func(title, message):
    if send_notification_rule:
        send_notif(
            title,
            message,
        )
    else:
        QMessageBox.information(
            window,
            title,
            message,
        )

def save_user_settings():
    settings = {
        "focus_duration" : focus_input.value(),
        "break_duration" : break_input.value(),
        "long_break_duration" : long_break_duration,
        "session_before_long_break" : session_before_long_break,
        "button_pressed_sound_rule" : button_pressed_sound_rule,
        "send_notifications_rule" : send_notification_rule,
        "auto_start_focus_rule" : auto_start_focus,
        "auto_start_break_rule" : auto_start_break,
        "tray_rule" : tray_rule,
    }

    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)

def load_settings():
    global long_break_duration
    global session_before_long_break
    global button_pressed_sound_rule
    global send_notification_rule
    global auto_start_focus
    global auto_start_break
    global tray_rule

    if not SETTINGS_FILE.exists():
        return

    try:
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file)
    except (json.JSONDecodeError, OSError):
        return

    focus_input.setValue(
        settings.get("focus_duration", 25)
    )

    break_input.setValue(
        settings.get("break_duration", 5)
    )

    long_break_duration = settings.get(
        "long_break_duration", 15
    )

    session_before_long_break = settings.get(
        "session_before_long_break", 3
    )

    button_pressed_sound_rule = settings.get(
        "button_pressed_sound_rule", True
    )

    send_notification_rule  = settings.get(
        "send_notifications_rule", True
    )

    auto_start_focus = settings.get(
        "auto_start_focus_rule", False
    )

    auto_start_break = settings.get(
        "auto_start_break_rule", False
    )

    tray_rule = settings.get(
        "tray_rule", False
    )


def show_window():
    window.showNormal()
    window.raise_()
    window.activateWindow()

#Classes
class RainyWindow(QWidget):
    def closeEvent(self, event):
        if tray_rule:
            event.ignore()
            self.hide()
        else:
            event.accept()

# Application
app = QApplication(sys.argv)

#Sounds
focus_end_sound = QSoundEffect()
focus_end_sound.setSource(
    QUrl.fromLocalFile(str(resource_path("sounds/focus_end.wav")))
)
focus_end_sound.setVolume(0.5)

break_end_sound = QSoundEffect()
break_end_sound.setSource(
    QUrl.fromLocalFile(str(resource_path("sounds/break_end.wav")))
)
break_end_sound.setVolume(0.5)

button_pressed_sound = QSoundEffect()
button_pressed_sound.setSource(
    QUrl.fromLocalFile(str(resource_path("sounds/button_pressed.wav")))
)
button_pressed_sound.setVolume(0.3)



# Window
window = RainyWindow()
window.setStyleSheet("""
    QWidget {
            background-color: #202020;
            color: white;
    }
""")

window.setWindowTitle("Rainy")
window.resize(500, 400)

window.setWindowIcon(QIcon(str(ICON_PATH)))


# Widgets
title = QLabel("00:00")
title.setStyleSheet("""
    QLabel {
        font-size: 60px;
        font-weight: bold;
    }
""")
title.setAlignment(Qt.AlignCenter)


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

reset_button = QPushButton("↻ Reset")
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

settings_button = QPushButton("⚙️")
settings_button.setStyleSheet("""
    QPushButton{
        font-size: 10px;
        padding: 10px;
        border-radius: 16px;
        max-width: 10px;
        border: 1px solid #555555;
    }
""")
settings_button.setToolTip("Change settings")

debug_button = QPushButton("🐛 2s")
debug_button.setToolTip("Set current timer to 5 seconds")

stats_button = QPushButton("📊")
stats_button.setStyleSheet("""
    QPushButton{
        font-size: 10px;
        padding: 10px;
        border-radius: 16px;
        max-width: 10px;
        border: 1px solid #555555;
    }
""")
stats_button.setToolTip("Peek at yout stats")

finish_activity_button = QPushButton("Finish Activity")
finish_activity_button.setToolTip("Finish your activity to save a record")
finish_activity_button.setStyleSheet("""
    QPushButton {
        font-size: 16px;
        padding: 8px;
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


#Connections
start_button.clicked.connect(toggle_focus)
start_button.clicked.connect(button_pressed)

stop_button.clicked.connect(stop_func)
stop_button.clicked.connect(button_pressed)

reset_button.clicked.connect(reset_focus)
reset_button.clicked.connect(button_pressed)

settings_button.clicked.connect(open_settings)
settings_button.clicked.connect(button_pressed)

shortcut_space = QShortcut(QKeySequence("Space"), window)
shortcut_space.activated.connect(toggle_focus)

focus_input.valueChanged.connect(settings_changed)
break_input.valueChanged.connect(settings_changed)

debug_button.clicked.connect(debug_timer)

stats_button.clicked.connect(open_stats)
finish_activity_button.clicked.connect(finish_activity)


# Timer
timer = QTimer()
timer.timeout.connect(update_timer)



# Layout
settings_layout = QHBoxLayout()
layout = QVBoxLayout()
focus_layout = QVBoxLayout()
break_layout = QVBoxLayout()
stopReset_layout = QHBoxLayout()
button_layout = QHBoxLayout()

layout.setContentsMargins(50 ,40 , 50, 40)
layout.setSpacing(15)

layout.addLayout(button_layout)

button_layout.addWidget(settings_button)
button_layout.addWidget(mode_label)
button_layout.addWidget(stats_button)

layout.addWidget(session_label)
layout.addWidget(title)

layout.addWidget(start_button)

#stopReset_layout.addWidget(debug_button)
stopReset_layout.addWidget(debug_button)
stopReset_layout.addWidget(stop_button)
stopReset_layout.addWidget(reset_button)

focus_layout.addWidget(focus_label)
focus_layout.addWidget(focus_input)
layout.addLayout(stopReset_layout)

break_layout.addWidget(break_label)
break_layout.addWidget(break_input)

layout.addWidget(finish_activity_button)
settings_layout.addLayout(focus_layout)
settings_layout.addLayout(break_layout)

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

load_settings()

#System tray
tray_icon = QSystemTrayIcon(window)
tray_icon.setIcon(window.windowIcon())
tray_icon.setToolTip("Rainy")

tray_menu = QMenu()
open_action = tray_menu.addAction("Open Rainy")
start_pause_action = tray_menu.addAction("Start or Pause")
stop_action = tray_menu.addAction("Stop")
reset_action = tray_menu.addAction("Reset")

tray_menu.addSeparator()

quit_action = tray_menu.addAction("Quit")

tray_icon.setContextMenu(tray_menu)

#tray_icon.activated.connect()

open_action.triggered.connect(show_window)
open_action.triggered.connect(button_pressed)

start_pause_action.triggered.connect(toggle_focus)
start_pause_action.triggered.connect(button_pressed)

stop_action.triggered.connect(stop_func)
stop_action.triggered.connect(button_pressed)

reset_action.triggered.connect(reset_focus)
reset_action.triggered.connect(button_pressed)

quit_action.triggered.connect(app.quit)
quit_action.triggered.connect(button_pressed)

if tray_rule:
    tray_icon.show()


# Run
window.show()


#Close
sys.exit(app.exec())