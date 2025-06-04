import tkinter as tk
from tkinter import messagebox
import json
import os
from datetime import datetime, timedelta

TODO_FILE = "todo.json"
DONE_FILE = "done.json"

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🗓️ Professioneller To-Do-Manager mit Fälligkeitsauswahl")

        self.tasks = self.load_tasks(TODO_FILE)
        self.done_tasks = self.load_tasks(DONE_FILE)
        self.edit_index = None

        # Eingabe Feld für Aufgaben
        self.task_entry = tk.Entry(root, width=50)
        self.task_entry.pack(pady=5)

        # Fälligkeitsauswahl
        self.create_due_date_widgets()

        # Buttons
        self.add_button = tk.Button(root, text="➕ Aufgabe hinzufügen", command=self.add_task)
        self.add_button.pack(pady=2)

        self.edit_button = tk.Button(root, text="✏️ Aufgabe bearbeiten", command=self.edit_task)
        self.edit_button.pack(pady=2)

        self.save_edit_button = tk.Button(root, text="💾 Änderung speichern", command=self.save_edited_task)
        self.save_edit_button.pack(pady=2)

        # Offene Aufgaben
        tk.Label(root, text="📋 Offene Aufgaben").pack()
        self.listbox = tk.Listbox(root, width=80, height=10)
        self.listbox.pack(pady=5)

        self.done_button = tk.Button(root, text="✅ Als erledigt markieren", command=self.mark_done)
        self.done_button.pack(pady=2)

        self.delete_button = tk.Button(root, text="🗑️ Aufgabe löschen", command=self.delete_task)
        self.delete_button.pack(pady=5)

        # Erledigte Aufgaben
        tk.Label(root, text="📁 Erledigte Aufgaben").pack()
        self.done_listbox = tk.Listbox(root, width=80, height=5)
        self.done_listbox.pack(pady=5)

        self.update_listboxes()

    def create_due_date_widgets(self):
        # Heute + 14 Tage Auswahl
        self.dates = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(15)]
        self.selected_date = tk.StringVar(value=self.dates[0])
        tk.Label(self.root, text="Fälligkeit Datum:").pack()
        tk.OptionMenu(self.root, self.selected_date, *self.dates).pack()

        # Uhrzeit (Std/Min)
        time_frame = tk.Frame(self.root)
        time_frame.pack()
        tk.Label(time_frame, text="Uhrzeit: ").pack(side=tk.LEFT)
        self.hour_spinbox = tk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.hour_spinbox.pack(side=tk.LEFT)
        tk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.minute_spinbox = tk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.minute_spinbox.pack(side=tk.LEFT)

    def load_tasks(self, filename):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return []

    def save_tasks(self, tasks, filename):
        with open(filename, "w") as f:
            json.dump(tasks, f, indent=4)

    def format_task(self, task):
        return f"{task['title']} (Fällig: {task['due']})"

    def get_due_datetime_str(self):
        date = self.selected_date.get()
        hour = self.hour_spinbox.get()
        minute = self.minute_spinbox.get()
        try:
            due_dt = datetime.strptime(f"{date} {hour}:{minute}", "%Y-%m-%d %H:%M")
            return due_dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return None

    def add_task(self):
        title = self.task_entry.get()
        if not title:
            messagebox.showwarning("Warnung", "Bitte eine Aufgabe eingeben!")
            return

        due_str = self.get_due_datetime_str()
        if not due_str:
            messagebox.showwarning("Fehler", "Ungültige Fälligkeit!")
            return

        task = {"title": title, "due": due_str}
        self.tasks.append(task)
        self.task_entry.delete(0, tk.END)
        self.save_tasks(self.tasks, TODO_FILE)
        self.update_listboxes()

    def edit_task(self):
        try:
            index = self.listbox.curselection()[0]
            self.edit_index = index
            task = self.tasks[index]
            self.task_entry.delete(0, tk.END)
            self.task_entry.insert(0, task["title"])

            # Datum setzen
            due_dt = datetime.strptime(task["due"], "%Y-%m-%d %H:%M")
            if due_dt.strftime("%Y-%m-%d") in self.dates:
                self.selected_date.set(due_dt.strftime("%Y-%m-%d"))
            self.hour_spinbox.delete(0, tk.END)
            self.hour_spinbox.insert(0, due_dt.strftime("%H"))
            self.minute_spinbox.delete(0, tk.END)
            self.minute_spinbox.insert(0, due_dt.strftime("%M"))
        except IndexError:
            messagebox.showwarning("Warnung", "Bitte eine Aufgabe auswählen!")

    def save_edited_task(self):
        if self.edit_index is None:
            messagebox.showinfo("Info", "Keine Aufgabe im Bearbeitungsmodus.")
            return

        new_title = self.task_entry.get()
        due_str = self.get_due_datetime_str()

        if not new_title or not due_str:
            messagebox.showwarning("Warnung", "Titel oder Fälligkeitsdatum ungültig!")
            return

        self.tasks[self.edit_index] = {"title": new_title, "due": due_str}
        self.edit_index = None
        self.task_entry.delete(0, tk.END)
        self.save_tasks(self.tasks, TODO_FILE)
        self.update_listboxes()

    def delete_task(self):
        try:
            index = self.listbox.curselection()[0]
            del self.tasks[index]
            self.save_tasks(self.tasks, TODO_FILE)
            self.update_listboxes()
        except IndexError:
            messagebox.showwarning("Warnung", "Bitte eine Aufgabe auswählen!")

    def mark_done(self):
        try:
            index = self.listbox.curselection()[0]
            task = self.tasks.pop(index)
            self.done_tasks.append(task)
            self.save_tasks(self.tasks, TODO_FILE)
            self.save_tasks(self.done_tasks, DONE_FILE)
            self.update_listboxes()
        except IndexError:
            messagebox.showwarning("Warnung", "Bitte eine Aufgabe auswählen!")

    def update_listboxes(self):
        self.listbox.delete(0, tk.END)
        for task in self.tasks:
            self.listbox.insert(tk.END, self.format_task(task))

        self.done_listbox.delete(0, tk.END)
        for task in self.done_tasks:
            self.done_listbox.insert(tk.END, self.format_task(task))

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
