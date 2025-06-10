import os
os.environ["TK_SILENCE_DEPRECATION"] = "1"

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
from datetime import datetime, timedelta
import tkinter.font as tkFont

try:
    from tkcalendar import Calendar
except ImportError:
    Calendar = None  # Calendar will not be available if tkcalendar is not installed

TODO_FILE = "todo.json"
DONE_FILE = "done.json"

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🗓️ Professioneller To-Do-Manager mit Fälligkeitsauswahl")
        self.root.configure(bg="#e8ecf3")

        self.font = tkFont.Font(family="Segoe UI", size=14)
        self.bold_font = tkFont.Font(family="Segoe UI", size=15, weight="bold")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#f9fafb")
        style.configure("TLabel", font=self.font, background="#f9fafb", foreground="#222")
        style.configure("TEntry", font=self.font, padding=8, relief="flat")
        style.configure("TButton",
                        font=self.bold_font,
                        padding=10,
                        relief="flat",
                        background="#4f8cff",
                        foreground="#fff",
                        borderwidth=0)
        style.map("TButton",
                  background=[("active", "#2563eb"), ("!active", "#4f8cff")],
                  foreground=[("active", "#fff")])

        # Menü für Multi-Window
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fenster", menu=window_menu)
        window_menu.add_command(label="Kalender öffnen", command=self.open_calendar_window)
        window_menu.add_command(label="Neues Aufgabenfenster", command=self.open_new_task_window)

        # Haupt-Frame als ttk.Frame
        main_frame = ttk.Frame(root, style="TFrame")
        main_frame.pack(padx=30, pady=30, fill=tk.BOTH, expand=True)

        card = ttk.Frame(main_frame, style="TFrame")
        card.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        input_frame = ttk.Frame(card, padding=20, style="TFrame")
        input_frame.pack(pady=(0, 10), fill=tk.X)

        self.task_entry = ttk.Entry(input_frame, width=45, style="TEntry")
        self.task_entry.grid(row=0, column=0, padx=(0, 10), pady=5, columnspan=3, sticky="ew")

        self.create_due_date_widgets(input_frame)

        self.add_button = ttk.Button(input_frame, text="➕ Hinzufügen", command=self.add_task, style="TButton")
        self.add_button.grid(row=1, column=0, pady=10, sticky="ew")
        self.edit_button = ttk.Button(input_frame, text="✏️ Bearbeiten", command=self.edit_task, style="TButton")
        self.edit_button.grid(row=1, column=1, pady=10, sticky="ew", padx=5)
        self.save_edit_button = ttk.Button(input_frame, text="💾 Speichern", command=self.save_edited_task, style="TButton")
        self.save_edit_button.grid(row=1, column=2, pady=10, sticky="ew")
        self.calendar_button = ttk.Button(input_frame, text="Kalender anzeigen", command=self.show_task_calendar, style="TButton")
        self.calendar_button.grid(row=1, column=3, pady=10, sticky="ew", padx=5)

        ttk.Label(card, text="📋 Offene Aufgaben", style="TLabel").pack(anchor="w", padx=20, pady=(10, 0))
        listbox_frame = ttk.Frame(card, style="TFrame")
        listbox_frame.pack(padx=20, pady=(0, 10), fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(listbox_frame, width=80, height=8, font=self.font, selectbackground="#b3e5fc",
                                  relief=tk.FLAT, bd=0, highlightthickness=0, bg="#f3f6fa", fg="#222")
        self.listbox.pack(side=tk.LEFT, pady=5, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(card, style="TFrame")
        btn_frame.pack(padx=20, pady=(0, 10), fill=tk.X)
        self.done_button = ttk.Button(btn_frame, text="✅ Erledigt", command=self.mark_done, style="TButton")
        self.done_button.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        self.delete_button = ttk.Button(btn_frame, text="🗑️ Löschen", command=self.delete_task, style="TButton")
        self.delete_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(card, text="📁 Erledigte Aufgaben", style="TLabel").pack(anchor="w", padx=20, pady=(10, 0))
        done_listbox_frame = ttk.Frame(card, style="TFrame")
        done_listbox_frame.pack(padx=20, pady=(0, 10), fill=tk.BOTH)
        self.done_listbox = tk.Listbox(done_listbox_frame, width=80, height=4, font=self.font, selectbackground="#c8e6c9",
                                       relief=tk.FLAT, bd=0, highlightthickness=0, bg="#f3f6fa", fg="#888")
        self.done_listbox.pack(side=tk.LEFT, pady=5, fill=tk.BOTH, expand=True)
        done_scrollbar = ttk.Scrollbar(done_listbox_frame, orient="vertical", command=self.done_listbox.yview)
        done_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.done_listbox.config(yscrollcommand=done_scrollbar.set)

        self.status_var = tk.StringVar()
        self.status_var.set("Willkommen bei To-Do 2025!")
        status_bar = ttk.Label(root, textvariable=self.status_var, anchor=tk.W, background="#e8ecf3", relief=tk.FLAT, font=self.font)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=(0, 0))

        self.tasks = self.load_tasks(TODO_FILE)
        self.done_tasks = self.load_tasks(DONE_FILE)
        self.edit_index = None

        self.update_listboxes()

    def create_due_date_widgets(self, parent=None):
        if parent is None:
            parent = self.root
        # Heute + 14 Tage Auswahl
        self.dates = [(datetime.today() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(15)]
        today_str = datetime.today().strftime("%Y-%m-%d")
        self.selected_date = tk.StringVar(value=today_str)
        ttk.Label(parent, text="Fälligkeitsdatum:").grid(row=2, column=0, sticky="w", padx=5)
        date_menu = ttk.OptionMenu(parent, self.selected_date, today_str, *self.dates)
        date_menu.grid(row=2, column=1, sticky="ew", padx=5)

        # Uhrzeit (Std/Min) – aktuelle Uhrzeit vorausfüllen
        now = datetime.now()
        time_frame = ttk.Frame(parent, style="TFrame")
        time_frame.grid(row=2, column=2, sticky="ew", padx=5)
        ttk.Label(time_frame, text="Uhrzeit: ").pack(side=tk.LEFT)
        self.hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.hour_spinbox.pack(side=tk.LEFT)
        self.hour_spinbox.delete(0, tk.END)
        self.hour_spinbox.insert(0, now.strftime("%H"))
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.minute_spinbox.pack(side=tk.LEFT)
        self.minute_spinbox.delete(0, tk.END)
        self.minute_spinbox.insert(0, now.strftime("%M"))

    def open_calendar_window(self):
        if Calendar is None:
            messagebox.showerror("Fehler", "tkcalendar ist nicht installiert.\nInstalliere es mit: pip install tkcalendar")
            return
        cal_win = tk.Toplevel(self.root)
        cal_win.title("Kalender")
        cal_win.geometry("400x400")
        cal = Calendar(cal_win, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        def set_date():
            selected = cal.get_date()
            self.selected_date.set(selected)
            cal_win.destroy()
        ttk.Button(cal_win, text="Datum übernehmen", command=set_date).pack(pady=10)

    def open_new_task_window(self):
        win = tk.Toplevel(self.root)
        win.title("Neues Aufgabenfenster")
        win.geometry("500x300")
        font = tkFont.Font(family="Segoe UI", size=14)
        entry = ttk.Entry(win, width=40, font=font)
        entry.pack(pady=20)

        # Kalender-Button im neuen Aufgabenfenster
        if Calendar is not None:
            def open_win_calendar():
                cal_win = tk.Toplevel(win)
                cal_win.title("Kalender")
                cal_win.geometry("400x400")
                cal = Calendar(cal_win, selectmode='day', date_pattern='yyyy-mm-dd')
                cal.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
                def set_date():
                    selected = cal.get_date()
                    entry.delete(0, tk.END)
                    entry.insert(0, selected)
                    cal_win.destroy()
                ttk.Button(cal_win, text="Datum übernehmen", command=set_date).pack(pady=10)
            ttk.Button(win, text="Kalender öffnen", command=open_win_calendar).pack(pady=5)

        ttk.Button(win, text="Hinzufügen", command=lambda: self.add_task_from_window(entry, win)).pack(pady=10)

    def add_task_from_window(self, entry, win):
        title = entry.get()
        if not title:
            messagebox.showwarning("Warnung", "Bitte eine Aufgabe eingeben!", parent=win)
            return
        due_str = self.get_due_datetime_str()
        if not due_str:
            messagebox.showwarning("Fehler", "Ungültige Fälligkeit!", parent=win)
            return
        task = {"title": title, "due": due_str}
        self.tasks.append(task)
        self.save_tasks(self.tasks, TODO_FILE)
        self.edit_index = None
        self.update_listboxes()
        win.destroy()

    def load_tasks(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    return json.load(f)
            except Exception:
                return []
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
        self.edit_index = None
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
            self.update_listboxes()
        except IndexError:
            messagebox.showwarning("Warnung", "Bitte eine Aufgabe auswählen!")

    def save_edited_task(self):
        # Prüfen, ob eine Aufgabe zum Bearbeiten ausgewählt ist
        if self.edit_index is None:
            messagebox.showinfo("Info", "Keine Aufgabe im Bearbeitungsmodus.")
            return

        new_title = self.task_entry.get()
        due_str = self.get_due_datetime_str()

        # Prüfen, ob Titel oder Fälligkeitsdatum leer oder ungültig sind
        if not new_title or not due_str:
            messagebox.showwarning("Warnung", "Titel oder Fälligkeitsdatum ungültig!")
            return

        # Aufgabe in der Liste aktualisieren
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
            self.edit_index = None
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
            self.edit_index = None
            self.update_listboxes()
        except IndexError:
            messagebox.showwarning("Warnung", "Bitte eine Aufgabe auswählen!")

    def update_listboxes(self):
        self.listbox.delete(0, tk.END)
        now = datetime.now()
        for idx, task in enumerate(self.tasks):
            due_dt = datetime.strptime(task['due'], "%Y-%m-%d %H:%M")
            if due_dt < now:
                color = "#ff5252"
                prefix = "⏰ "
            elif due_dt.date() == now.date():
                color = "#fff176"
                prefix = "🟡 "
            else:
                color = "#69f0ae"
                prefix = "🟢 "
            display = f"{prefix}{self.format_task(task)}"
            self.listbox.insert(tk.END, display)
            self.listbox.itemconfig(idx, {'bg': color, 'fg': "#222"})

        self.done_listbox.delete(0, tk.END)
        for idx, task in enumerate(self.done_tasks):
            display = f"✅ {self.format_task(task)}"
            self.done_listbox.insert(tk.END, display)
            self.done_listbox.itemconfig(idx, {'bg': "#e0e0e0", 'fg': "#888"})

        self.status_var.set(f"{len(self.tasks)} offene Aufgaben, {len(self.done_tasks)} erledigt.")

        # Buttons steuern
        if self.edit_index is not None:
            self.add_button.state(['disabled'])
            self.save_edit_button.state(['!disabled'])
        else:
            self.add_button.state(['!disabled'])
            self.save_edit_button.state(['disabled'])

    def show_task_calendar(self):
        if Calendar is None:
            messagebox.showerror("Fehler", "tkcalendar ist nicht installiert.\nInstalliere es mit: pip install tkcalendar")
            return
        cal_win = tk.Toplevel(self.root)
        cal_win.title("Aufgaben-Kalender")
        cal_win.geometry("500x500")
        cal = Calendar(cal_win, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # Aufgaben-Tage markieren
        task_dates = {}
        for task in self.tasks:
            date = task['due'][:10]
            if date not in task_dates:
                task_dates[date] = []
            task_dates[date].append(task['title'])
            # Markiere das Datum im Kalender
            cal.calevent_create(datetime.strptime(date, "%Y-%m-%d"), "Aufgabe", "task")

        cal.tag_config('task', background="#4f8cff", foreground="white")

        # Aufgabenliste für gewählten Tag anzeigen
        task_listbox = tk.Listbox(cal_win, font=self.font)
        task_listbox.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0, 20))

        def show_tasks_for_day(event):
            sel_date = cal.get_date()
            task_listbox.delete(0, tk.END)
            if sel_date in task_dates:
                for t in task_dates[sel_date]:
                    task_listbox.insert(tk.END, t)
            else:
                task_listbox.insert(tk.END, "Keine Aufgaben an diesem Tag.")

        cal.bind("<<CalendarSelected>>", show_tasks_for_day)
        # Zeige Aufgaben für das heutige Datum direkt an
        show_tasks_for_day(None)

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
