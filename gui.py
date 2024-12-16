import sys
import subprocess
import json
import os
import signal
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QWidget, QLineEdit, QCheckBox, QFormLayout, QDialog, QSpinBox, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class TaskEditor(QDialog):
    def __init__(self, task=None):
        super().__init__()
        self.task = task or {
            "subreddit": "",
            "titles": [],
            "links": [],
            "upvotes": 0,
            "post_at": [],
            "post_every_n_days": 1
        }
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.subreddit_input = QLineEdit(self.task['subreddit'])

        # Use QTextEdit for titles and links to handle longer text
        self.titles_input = QTextEdit(", ".join(self.task['titles']))
        self.titles_input.setMinimumHeight(100)  # Set minimum height for better visibility
        self.links_input = QTextEdit(", ".join(self.task['links']))
        self.links_input.setMinimumHeight(100)  # Set minimum height for better visibility

        self.upvotes_input = QSpinBox()
        self.upvotes_input.setValue(self.task['upvotes'])
        self.upvotes_input.setRange(0, 1000)

        # Post at input with tooltip for clarity
        self.post_at_input = QLineEdit(", ".join(map(str, self.task['post_at'])))
        self.post_at_input.setToolTip("Enter the hour(s) to post (0-23 for hours of the day)")

        self.post_every_input = QSpinBox()
        self.post_every_input.setValue(self.task['post_every_n_days'])
        self.post_every_input.setRange(1, 30)

        # Adding all inputs to the form layout
        layout.addRow("Subreddit:", self.subreddit_input)
        layout.addRow("Titles (comma-separated):", self.titles_input)
        layout.addRow("Links (comma-separated):", self.links_input)
        layout.addRow("Upvotes:", self.upvotes_input)
        layout.addRow("Post At (comma-separated hours):", self.post_at_input)
        layout.addRow("Post Every N Days:", self.post_every_input)

        # Save button to store changes
        save_button = QPushButton("Save 💖")
        save_button.clicked.connect(self.save_task)
        layout.addRow(save_button)

        self.setLayout(layout)

    def save_task(self):
        self.task['subreddit'] = self.subreddit_input.text()
        self.task['titles'] = self.titles_input.toPlainText().split(", ")
        self.task['links'] = self.links_input.toPlainText().split(", ")
        self.task['upvotes'] = self.upvotes_input.value()
        self.task['post_at'] = list(map(int, self.post_at_input.text().split(",")))
        self.task['post_every_n_days'] = self.post_every_input.value()
        self.accept()

class RedditScheduler(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reddit Bot Scheduler 💕")
        self.setGeometry(100, 100, 800, 600)

        self.schedule_file = 'schedule.json'
        self.tasks = []

        self.load_tasks()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Set the background color to pink
        self.setStyleSheet("background-color: #ffccff;")  # Pink background

        # Table for tasks
        self.table = QTableWidget()
        self.table.setRowCount(len(self.tasks))
        self.table.setColumnCount(6)  # Adding one column for links
        self.table.setHorizontalHeaderLabels(['Subreddit', 'Titles', 'Links', 'Post At', 'Post Every N Days', 'Included'])
        self.layout.addWidget(self.table)

        # Populate the table with tasks
        self.populate_table()

        # Buttons for task management
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Task 💖")
        self.add_button.setStyleSheet("background-color: #ff66cc; color: white; font-size: 16px; border-radius: 8px;")
        self.add_button.clicked.connect(self.add_task)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Task ✨")
        self.edit_button.setStyleSheet("background-color: #ff66cc; color: white; font-size: 16px; border-radius: 8px;")
        self.edit_button.clicked.connect(self.edit_task)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Task 💔")
        self.delete_button.setStyleSheet("background-color: #ff66cc; color: white; font-size: 16px; border-radius: 8px;")
        self.delete_button.clicked.connect(self.delete_task)
        button_layout.addWidget(self.delete_button)

        self.save_button = QPushButton("Save Schedule 💕")
        self.save_button.setStyleSheet("background-color: #ff66cc; color: white; font-size: 16px; border-radius: 8px;")
        self.save_button.clicked.connect(self.save_schedule)
        button_layout.addWidget(self.save_button)

        self.layout.addLayout(button_layout)

        # Add the bot control buttons
        bot_button_layout = QHBoxLayout()

        self.run_button = QPushButton("Run Bot 💖")
        self.run_button.setStyleSheet("background-color: #ff66cc; color: white; padding: 10px; font-size: 16px; border-radius: 8px;")
        self.run_button.clicked.connect(self.run_bot)
        bot_button_layout.addWidget(self.run_button)

        self.stop_button = QPushButton("Stop Bot 💔")
        self.stop_button.setStyleSheet("background-color: #ff66cc; color: white; padding: 10px; font-size: 16px; border-radius: 8px;")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)  # Initially disabled
        bot_button_layout.addWidget(self.stop_button)

        self.layout.addLayout(bot_button_layout)

        # Central widget
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

    def load_tasks(self):
        if os.path.exists(self.schedule_file):
            with open(self.schedule_file, 'r') as f:
                self.tasks = json.load(f)
        else:
            self.tasks = []

    def populate_table(self):
        self.table.setRowCount(len(self.tasks))
        for row, task in enumerate(self.tasks):
            self.table.setItem(row, 0, QTableWidgetItem(task['subreddit']))
            self.table.setItem(row, 1, QTableWidgetItem(", ".join(task['titles'])))
            self.table.setItem(row, 2, QTableWidgetItem(", ".join(task['links'])))
            self.table.setItem(row, 3, QTableWidgetItem(", ".join(map(str, task['post_at']))))
            self.table.setItem(row, 4, QTableWidgetItem(str(task['post_every_n_days'])))
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.Checked if task.get('included', False) else Qt.Unchecked)
            self.table.setItem(row, 5, checkbox_item)

    def add_task(self):
        task_editor = TaskEditor()
        if task_editor.exec_() == QDialog.Accepted:
            self.tasks.append(task_editor.task)
            self.populate_table()

    def edit_task(self):
        selected_row = self.table.currentRow()
        if selected_row != -1:
            task = self.tasks[selected_row]
            task_editor = TaskEditor(task)
            if task_editor.exec_() == QDialog.Accepted:
                self.tasks[selected_row] = task_editor.task
                self.populate_table()

    def delete_task(self):
        selected_row = self.table.currentRow()
        if selected_row != -1:
            del self.tasks[selected_row]
            self.populate_table()

    def save_schedule(self):
        with open(self.schedule_file, 'w') as f:
            json.dump(self.tasks, f, indent=4)
        print("Schedule saved successfully!")

    def run_bot(self):
        try:
            print("Running bot...")
            self.process = subprocess.Popen(['run.bat'], shell=True)
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        except Exception as e:
            print(f"Error starting the bot: {e}")

    def stop_bot(self):
        if hasattr(self, 'process') and self.process.poll() is None:
            os.kill(self.process.pid, signal.SIGTERM)
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        if hasattr(self, 'process') and self.process.poll() is None:
            os.kill(self.process.pid, signal.SIGTERM)
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = RedditScheduler()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
