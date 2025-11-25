#!/usr/bin/env python3
"""
Tima - Activity Timer
A desktop productivity timer that cycles through your projects with customizable durations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta
import winsound  # For Windows alarm sound (use 'playsound' library for cross-platform)


class TimaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tima - Activity Timer")
        self.root.geometry("600x800")
        self.root.configure(bg='#f4f7f6')

        # App state
        self.projects = []
        self.current_project_index = 0
        self.default_duration = 3600  # 1 hour in seconds
        self.project_times = {}  # Track remaining time for each project
        self.project_paused = {}  # Track pause state for each project
        self.timer_running = False
        self.data_file = "tima_projects.json"

        # Timer state
        self.last_update_time = None
        self.after_id = None

        # Undo stack for delete/rename operations
        self.undo_stack = []
        self.max_undo_stack_size = 10

        # Load saved projects
        self.load_projects()

        # Create GUI
        self.setup_gui()

        # Start the timer
        self.start_timer()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bind global keyboard shortcuts
        self.setup_global_shortcuts()

    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#f4f7f6', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Duration settings frame
        duration_frame = tk.LabelFrame(
            main_frame,
            text="Timer Settings",
            font=('Arial', 12, 'bold'),
            bg='#f4f7f6',
            fg='#2c3e50',
            padx=10,
            pady=5
        )
        duration_frame.pack(fill=tk.X, pady=(0, 10))

        duration_controls = tk.Frame(duration_frame, bg='#f4f7f6')
        duration_controls.pack(fill=tk.X)

        tk.Label(duration_controls, text="Default Duration:", bg='#f4f7f6', font=('Arial', 10)).pack(side=tk.LEFT)

        # Set initial values based on loaded default_duration
        initial_hours = self.default_duration // 3600
        initial_minutes = (self.default_duration % 3600) // 60
        self.hours_var = tk.StringVar(value=str(initial_hours))
        self.minutes_var = tk.StringVar(value=str(initial_minutes))

        tk.Entry(duration_controls, textvariable=self.hours_var, width=3, font=('Arial', 10)).pack(side=tk.LEFT,
                                                                                                   padx=(5, 2))
        tk.Label(duration_controls, text="h", bg='#f4f7f6', font=('Arial', 10)).pack(side=tk.LEFT)

        tk.Entry(duration_controls, textvariable=self.minutes_var, width=3, font=('Arial', 10)).pack(side=tk.LEFT,
                                                                                                     padx=(5, 2))
        tk.Label(duration_controls, text="m", bg='#f4f7f6', font=('Arial', 10)).pack(side=tk.LEFT)

        tk.Button(
            duration_controls,
            text="Update",
            font=('Arial', 10),
            bg='#3498db',
            fg='white',
            padx=10,
            command=self.update_default_duration
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Current activity display
        self.activity_frame = tk.Frame(main_frame, bg='#3498db', relief=tk.RAISED, bd=2)
        self.activity_frame.pack(fill=tk.X, pady=(0, 10))

        self.activity_label = tk.Label(
            self.activity_frame,
            text="Loading...",
            font=('Arial', 16, 'bold'),
            bg='#3498db',
            fg='white',
            pady=15
        )
        self.activity_label.pack()

        # Timer display
        self.timer_label = tk.Label(
            main_frame,
            text="01:00:00",
            font=('Arial', 48, 'bold'),
            bg='#f4f7f6',
            fg='#2c3e50'
        )
        self.timer_label.pack(pady=20)

        # Project status
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 12),
            bg='#f4f7f6',
            fg='#7f8c8d'
        )
        self.status_label.pack()

        # Timer controls
        controls_frame = tk.Frame(main_frame, bg='#f4f7f6')
        controls_frame.pack(pady=15)

        self.pause_btn = tk.Button(
            controls_frame,
            text="Pause Current",
            font=('Arial', 12),
            bg='#e74c3c',
            fg='white',
            padx=20,
            pady=8,
            command=self.toggle_current_project
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(
            controls_frame,
            text="Reset Current",
            font=('Arial', 12),
            bg='#e67e22',
            fg='white',
            padx=20,
            pady=8,
            command=self.reset_current_project
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            controls_frame,
            text="Next Project",
            font=('Arial', 12),
            bg='#27ae60',
            fg='white',
            padx=20,
            pady=8,
            command=self.next_project
        ).pack(side=tk.LEFT, padx=5)

        # Project management section
        project_frame = tk.LabelFrame(
            main_frame,
            text="Manage Projects",
            font=('Arial', 14, 'bold'),
            bg='#f4f7f6',
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        project_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # Add project controls
        add_frame = tk.Frame(project_frame, bg='#f4f7f6')
        add_frame.pack(fill=tk.X, pady=(0, 10))

        self.project_entry = tk.Entry(
            add_frame,
            font=('Arial', 12),
            relief=tk.SOLID,
            bd=1
        )
        self.project_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.project_entry.bind('<Return>', lambda e: self.add_project())

        tk.Button(
            add_frame,
            text="Add",
            font=('Arial', 12),
            bg='#3498db',
            fg='white',
            padx=20,
            command=self.add_project
        ).pack(side=tk.RIGHT)

        # Project list with scrollbar
        list_frame = tk.Frame(project_frame, bg='#f4f7f6')
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.project_listbox = tk.Listbox(
            list_frame,
            font=('Arial', 11),
            height=10,
            relief=tk.SOLID,
            bd=1,
            selectmode=tk.SINGLE
        )
        self.project_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.project_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.project_listbox.yview)

        # Bind keyboard shortcuts for project management
        self.project_listbox.bind('<Delete>', lambda e: self.delete_project())
        self.project_listbox.bind('<F2>', lambda e: self.rename_project())
        self.project_listbox.bind('<Return>', lambda e: self.rename_project())
        self.project_listbox.bind('<Double-Button-1>', lambda e: self.rename_project())

        # Project control buttons
        project_btn_frame = tk.Frame(project_frame, bg='#f4f7f6')
        project_btn_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            project_btn_frame,
            text="Rename Selected",
            font=('Arial', 12),
            bg='#3498db',
            fg='white',
            command=self.rename_project
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            project_btn_frame,
            text="Delete Selected",
            font=('Arial', 12),
            bg='#e74c3c',
            fg='white',
            command=self.delete_project
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            project_btn_frame,
            text="Reset Selected",
            font=('Arial', 12),
            bg='#e67e22',
            fg='white',
            command=self.reset_selected_project
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            project_btn_frame,
            text="Pause/Resume Selected",
            font=('Arial', 12),
            bg='#f39c12',
            fg='white',
            command=self.toggle_selected_project
        ).pack(side=tk.LEFT, padx=5)

        # File controls
        file_frame = tk.Frame(project_frame, bg='#f4f7f6')
        file_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(
            file_frame,
            text="Import from .txt",
            font=('Arial', 12),
            bg='#27ae60',
            fg='white',
            padx=20,
            command=self.import_projects
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            file_frame,
            text="Export to .txt",
            font=('Arial', 12),
            bg='#27ae60',
            fg='white',
            padx=20,
            command=self.export_projects
        ).pack(side=tk.LEFT)

        # Initial render
        self.render_projects()

    def setup_global_shortcuts(self):
        """Setup global keyboard shortcuts"""
        # Space: Pause/Resume current project
        self.root.bind('<space>', lambda e: self.toggle_current_project())

        # Page Up/Down: Navigate projects
        self.root.bind('<Prior>', lambda e: self.previous_project())  # Page Up
        self.root.bind('<Next>', lambda e: self.next_project())  # Page Down

        # Ctrl+Z: Undo last delete/rename
        self.root.bind('<Control-z>', lambda e: self.undo_last_operation())

        # ?: Show help
        self.root.bind('?', lambda e: self.show_help())

    def show_help(self):
        """Show keyboard shortcuts help dialog"""
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Keyboard Shortcuts")
        help_dialog.geometry("500x450")
        help_dialog.configure(bg='#f4f7f6')
        help_dialog.transient(self.root)
        help_dialog.grab_set()

        # Center the dialog
        help_dialog.update_idletasks()
        x = (help_dialog.winfo_screenwidth() // 2) - (help_dialog.winfo_width() // 2)
        y = (help_dialog.winfo_screenheight() // 2) - (help_dialog.winfo_height() // 2)
        help_dialog.geometry(f"+{x}+{y}")

        # Dialog content
        frame = tk.Frame(help_dialog, bg='#f4f7f6', padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Keyboard Shortcuts",
            bg='#f4f7f6',
            font=('Arial', 16, 'bold'),
            fg='#2c3e50'
        ).pack(pady=(0, 15))

        # Create shortcuts text
        shortcuts_text = tk.Text(
            frame,
            font=('Courier New', 10),
            bg='white',
            relief=tk.SOLID,
            bd=1,
            wrap=tk.WORD,
            height=18,
            width=55
        )
        shortcuts_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        help_content = """GLOBAL SHORTCUTS:
  Space              Pause/Resume current project
  Page Up            Previous project
  Page Down          Next project
  Ctrl+Z             Undo last delete/rename
  ?                  Show this help screen

PROJECT LIST SHORTCUTS:
  Enter              Rename selected project
  F2                 Rename selected project
  Delete             Delete selected project
  Double-click       Rename selected project

ADD PROJECT:
  Enter              Add project (in text entry field)

RENAME DIALOG:
  Enter              Save new name
  Escape             Cancel rename
"""

        shortcuts_text.insert('1.0', help_content)
        shortcuts_text.config(state=tk.DISABLED)

        # Close button
        tk.Button(
            frame,
            text="Close",
            font=('Arial', 11),
            bg='#3498db',
            fg='white',
            padx=30,
            command=help_dialog.destroy
        ).pack()

        # Bind Escape to close
        help_dialog.bind('<Escape>', lambda e: help_dialog.destroy())

    def previous_project(self):
        """Move to the previous project"""
        if self.projects:
            self.current_project_index = (self.current_project_index - 1) % len(self.projects)
            self.save_projects()
            self.update_display()

    def push_undo(self, operation_type, data):
        """Push an undo operation onto the stack"""
        self.undo_stack.append({
            'type': operation_type,
            'data': data
        })
        # Limit stack size
        if len(self.undo_stack) > self.max_undo_stack_size:
            self.undo_stack.pop(0)

    def undo_last_operation(self):
        """Undo the last delete or rename operation"""
        if not self.undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo!")
            return

        operation = self.undo_stack.pop()
        op_type = operation['type']
        data = operation['data']

        if op_type == 'delete':
            # Restore deleted project
            index = data['index']
            project_name = data['name']
            project_time = data['time']
            project_paused = data['paused']

            # Insert project back at its original position
            self.projects.insert(index, project_name)
            self.project_times[project_name] = project_time
            self.project_paused[project_name] = project_paused

            # Adjust current project index if needed
            if index <= self.current_project_index:
                self.current_project_index += 1

            self.save_projects()
            self.render_projects()
            self.update_current_activity()
            messagebox.showinfo("Undo", f"Restored project: {project_name}")

        elif op_type == 'rename':
            # Restore old project name
            index = data['index']
            old_name = data['old_name']
            new_name = data['new_name']

            # Rename back to old name
            self.projects[index] = old_name

            # Restore project data with old name
            if new_name in self.project_times:
                self.project_times[old_name] = self.project_times.pop(new_name)
            if new_name in self.project_paused:
                self.project_paused[old_name] = self.project_paused.pop(new_name)

            self.save_projects()
            self.render_projects()
            self.update_current_activity()
            messagebox.showinfo("Undo", f"Renamed back to: {old_name}")

    def update_default_duration(self):
        """Update the default duration for new projects"""
        try:
            hours = int(self.hours_var.get() or 0)
            minutes = int(self.minutes_var.get() or 0)
            self.default_duration = hours * 3600 + minutes * 60

            if self.default_duration <= 0:
                messagebox.showwarning("Invalid Duration", "Duration must be greater than 0!")
                self.hours_var.set("1")
                self.minutes_var.set("0")
                self.default_duration = 3600
            else:
                messagebox.showinfo("Updated", f"Default duration set to {hours}h {minutes}m")

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for hours and minutes!")
            self.hours_var.set("1")
            self.minutes_var.set("0")

    def get_current_time_left(self):
        """Get the time left for the current project"""
        if not self.projects or self.current_project_index >= len(self.projects):
            return 0

        project_name = self.projects[self.current_project_index]
        return self.project_times.get(project_name, self.default_duration)

    def set_current_time_left(self, time_left):
        """Set the time left for the current project"""
        if self.projects and self.current_project_index < len(self.projects):
            project_name = self.projects[self.current_project_index]
            self.project_times[project_name] = time_left

    def is_current_project_paused(self):
        """Check if the current project is paused"""
        if not self.projects or self.current_project_index >= len(self.projects):
            return False

        project_name = self.projects[self.current_project_index]
        return self.project_paused.get(project_name, False)

    def set_current_project_paused(self, paused):
        """Set the pause state for the current project"""
        if self.projects and self.current_project_index < len(self.projects):
            project_name = self.projects[self.current_project_index]
            self.project_paused[project_name] = paused

    def load_projects(self):
        """Load projects from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.projects = data.get('projects', [])
                    self.current_project_index = data.get('current_index', 0)
                    self.default_duration = data.get('default_duration', 3600)
                    self.project_times = data.get('project_times', {})
                    self.project_paused = data.get('project_paused', {})

        except Exception as e:
            print(f"Error loading projects: {e}")

        # Default projects if none loaded
        if self.projects is None:
            self.projects = ['Develop new feature', 'Review research papers', 'Team meeting prep']
            self.current_project_index = 0
            # Initialize project times and pause states
            for project in self.projects:
                if project not in self.project_times:
                    self.project_times[project] = self.default_duration
                if project not in self.project_paused:
                    self.project_paused[project] = False

    def save_projects(self):
        """Save projects to JSON file"""
        try:
            data = {
                'projects': self.projects,
                'current_index': self.current_project_index,
                'default_duration': self.default_duration,
                'project_times': self.project_times,
                'project_paused': self.project_paused
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving projects: {e}")

    def format_time(self, seconds):
        """Format seconds into HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def render_projects(self):
        """Update the project listbox"""
        self.project_listbox.delete(0, tk.END)
        for i, project in enumerate(self.projects):
            time_left = self.project_times.get(project, self.default_duration)
            is_paused = self.project_paused.get(project, False)
            is_current = i == self.current_project_index

            status = ""
            if is_current:
                status += "► "
            else:
                status += "   "

            if is_paused:
                status += "[PAUSED] "

            time_str = self.format_time(time_left)
            display_text = f"{status}{project} ({time_str})"

            self.project_listbox.insert(tk.END, display_text)

        # Highlight current project
        if 0 <= self.current_project_index < len(self.projects):
            self.project_listbox.selection_set(self.current_project_index)

    def add_project(self):
        """Add a new project"""
        project_name = self.project_entry.get().strip()
        if project_name:
            self.projects.append(project_name)
            self.project_times[project_name] = self.default_duration
            self.project_paused[project_name] = False
            self.project_entry.delete(0, tk.END)
            self.save_projects()
            self.render_projects()

            # If this is the first project, start the timer
            if len(self.projects) == 1:
                self.current_project_index = 0
                self.update_current_activity()

    def delete_project(self):
        """Delete the selected project"""
        selection = self.project_listbox.curselection()
        if selection:
            actual_index = selection[0]

            if 0 <= actual_index < len(self.projects):
                deleted_project = self.projects[actual_index]

                # Save undo information before deleting
                self.push_undo('delete', {
                    'index': actual_index,
                    'name': deleted_project,
                    'time': self.project_times.get(deleted_project, self.default_duration),
                    'paused': self.project_paused.get(deleted_project, False)
                })

                # Now perform the delete
                self.projects.pop(actual_index)

                # Clean up associated data
                if deleted_project in self.project_times:
                    del self.project_times[deleted_project]
                if deleted_project in self.project_paused:
                    del self.project_paused[deleted_project]

                # Adjust current project index
                if actual_index == self.current_project_index:
                    if self.current_project_index >= len(self.projects):
                        self.current_project_index = max(0, len(self.projects) - 1)
                elif actual_index < self.current_project_index:
                    self.current_project_index -= 1

                self.save_projects()
                self.render_projects()
                self.update_current_activity()

                messagebox.showinfo("Deleted", f"Deleted project: {deleted_project}")

    def rename_project(self):
        """Rename the selected project"""
        selection = self.project_listbox.curselection()
        if selection:
            index = selection[0]

            if 0 <= index < len(self.projects):
                old_name = self.projects[index]

                # Create a simple dialog window for renaming
                dialog = tk.Toplevel(self.root)
                dialog.title("Rename Project")
                dialog.geometry("400x120")
                dialog.configure(bg='#f4f7f6')
                dialog.transient(self.root)
                dialog.grab_set()

                # Center the dialog
                dialog.update_idletasks()
                x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
                y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
                dialog.geometry(f"+{x}+{y}")

                # Dialog content
                frame = tk.Frame(dialog, bg='#f4f7f6', padx=20, pady=20)
                frame.pack(fill=tk.BOTH, expand=True)

                tk.Label(
                    frame,
                    text="New project name:",
                    bg='#f4f7f6',
                    font=('Arial', 11)
                ).pack(anchor=tk.W, pady=(0, 5))

                entry = tk.Entry(frame, font=('Arial', 12), width=40)
                entry.pack(fill=tk.X, pady=(0, 10))
                entry.insert(0, old_name)
                entry.select_range(0, tk.END)
                entry.focus_set()

                def save_rename():
                    new_name = entry.get().strip()
                    if new_name and new_name != old_name:
                        # Save undo information before renaming
                        self.push_undo('rename', {
                            'index': index,
                            'old_name': old_name,
                            'new_name': new_name
                        })

                        # Update project name
                        self.projects[index] = new_name

                        # Update project times and paused state
                        if old_name in self.project_times:
                            self.project_times[new_name] = self.project_times.pop(old_name)
                        if old_name in self.project_paused:
                            self.project_paused[new_name] = self.project_paused.pop(old_name)

                        self.save_projects()
                        self.render_projects()
                        self.update_current_activity()
                        dialog.destroy()
                    elif not new_name:
                        messagebox.showwarning("Invalid Name", "Project name cannot be empty!")
                    else:
                        dialog.destroy()

                def cancel_rename():
                    dialog.destroy()

                # Buttons
                btn_frame = tk.Frame(frame, bg='#f4f7f6')
                btn_frame.pack(fill=tk.X)

                tk.Button(
                    btn_frame,
                    text="Save",
                    font=('Arial', 10),
                    bg='#3498db',
                    fg='white',
                    padx=20,
                    command=save_rename
                ).pack(side=tk.LEFT, padx=(0, 5))

                tk.Button(
                    btn_frame,
                    text="Cancel",
                    font=('Arial', 10),
                    bg='#95a5a6',
                    fg='white',
                    padx=20,
                    command=cancel_rename
                ).pack(side=tk.LEFT)

                # Bind Enter and Escape keys
                entry.bind('<Return>', lambda e: save_rename())
                dialog.bind('<Escape>', lambda e: cancel_rename())

    def reset_current_project(self):
        """Reset the current project's timer"""
        if self.projects and 0 <= self.current_project_index < len(self.projects):
            project_name = self.projects[self.current_project_index]
            self.project_times[project_name] = self.default_duration
            self.project_paused[project_name] = False
            self.save_projects()
            self.render_projects()
            self.update_display()

    def reset_selected_project(self):
        """Reset the selected project's timer"""
        selection = self.project_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.projects):
                project_name = self.projects[index]
                self.project_times[project_name] = self.default_duration
                self.project_paused[project_name] = False
                self.save_projects()
                self.render_projects()
                if index == self.current_project_index:
                    self.update_display()

    def toggle_current_project(self):
        """Toggle pause/resume for current project"""
        if self.projects and 0 <= self.current_project_index < len(self.projects):
            project_name = self.projects[self.current_project_index]
            current_state = self.project_paused.get(project_name, False)
            self.project_paused[project_name] = not current_state
            self.save_projects()
            self.render_projects()
            self.update_pause_button()

    def toggle_selected_project(self):
        """Toggle pause/resume for selected project"""
        selection = self.project_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.projects):
                project_name = self.projects[index]
                current_state = self.project_paused.get(project_name, False)
                self.project_paused[project_name] = not current_state
                self.save_projects()
                self.render_projects()
                if index == self.current_project_index:
                    self.update_pause_button()

    def update_pause_button(self):
        """Update the pause button text based on current project state"""
        if self.is_current_project_paused():
            self.pause_btn.config(text="Resume Current")
        else:
            self.pause_btn.config(text="Pause Current")

    def update_timer_display(self):
        """Update the timer display and status"""
        time_left = self.get_current_time_left()
        self.timer_label.config(text=self.format_time(time_left))

        # Update status
        if self.projects:
            if self.is_current_project_paused():
                self.status_label.config(text="⏸ PAUSED", fg='#e67e22')
            else:
                self.status_label.config(text="▶ RUNNING", fg='#27ae60')
        else:
            self.status_label.config(text="No projects", fg='#7f8c8d')

        # Flash when time is up
        if time_left <= 0 and not self.is_current_project_paused():
            current_color = self.timer_label.cget('fg')
            new_color = '#e74c3c' if current_color == '#2c3e50' else '#2c3e50'
            self.timer_label.config(fg=new_color)
        else:
            self.timer_label.config(fg='#2c3e50')

    def update_current_activity(self):
        """Update the current activity display"""
        if self.projects and 0 <= self.current_project_index < len(self.projects):
            self.activity_label.config(text=self.projects[self.current_project_index])
        else:
            self.activity_label.config(text="No Projects")
        self.update_pause_button()

    def update_display(self):
        """Update all display elements"""
        self.update_timer_display()
        self.update_current_activity()
        self.render_projects()

    def timer_tick(self):
        """Main timer tick function using tkinter's after method"""
        if self.projects and 0 <= self.current_project_index < len(self.projects):
            if not self.is_current_project_paused():
                current_time = self.get_current_time_left()
                if current_time > 0:
                    self.set_current_time_left(current_time - 1)
                    self.save_projects()
                else:
                    # Timer ended
                    self.timer_ended()
                    return

            self.update_display()

        # Schedule next tick
        self.after_id = self.root.after(1000, self.timer_tick)

    def timer_ended(self):
        """Handle timer end"""
        current_project = self.projects[self.current_project_index] if self.projects else "Current project"

        # Play alarm sound
        try:
            # winsound.PlaySound(r'C:\Windows\Media\')
            winsound.PlaySound('C:/Windows/Media/Alarm04.wav',
                               winsound.SND_FILENAME | winsound.SND_ASYNC)  # , winsound.SND_ALIAS)
            # winsound.Beep(1000, 1000)  # 1000 Hz for 1 second
        except:
            print("Alarm! Timer ended!")  # Fallback for non-Windows

        # Show notification
        result = messagebox.askquestion(
            "Timer Ended!",
            f"Time's up for: {current_project}\n\nMove to next project?",
            icon='question'
        )

        if result == 'yes':
            # Reset the current project before moving to next
            self.reset_current_project()
            self.next_project()
            # Automatically resume the timer for the new project
            self.resume_timer_after_switch()
        else:
            # Reset current project and resume
            self.reset_current_project()
            self.resume_timer_after_switch()

    def resume_timer_after_switch(self):
        """Resume the timer after switching projects or resetting"""
        # Ensure the new current project is not paused
        if self.projects and 0 <= self.current_project_index < len(self.projects):
            project_name = self.projects[self.current_project_index]
            self.project_paused[project_name] = False
            self.save_projects()
            self.update_display()

        # Continue the timer tick
        self.timer_tick()

    def start_timer(self):
        """Start the main timer loop"""
        if not self.timer_running:
            self.timer_running = True
            self.update_current_activity()
            self.timer_tick()

    def stop_timer(self):
        """Stop the timer"""
        self.timer_running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def next_project(self):
        """Move to the next project"""
        if self.projects:
            self.current_project_index = (self.current_project_index + 1) % len(self.projects)
            self.save_projects()
            self.update_display()

    def import_projects(self):
        """Import projects from a text file"""
        file_path = filedialog.askopenfilename(
            title="Import Projects",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                imported_projects = [line.strip() for line in content.split('\n') if line.strip()]

                if imported_projects:
                    self.projects = imported_projects
                    self.current_project_index = 0

                    # Initialize times and pause states for new projects
                    self.project_times = {}
                    self.project_paused = {}
                    for project in self.projects:
                        self.project_times[project] = self.default_duration
                        self.project_paused[project] = False

                    self.save_projects()
                    self.update_display()
                    messagebox.showinfo("Success", f"Imported {len(imported_projects)} projects!")
                else:
                    messagebox.showwarning("Warning", "No valid projects found in file!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to import file: {str(e)}")

    def export_projects(self):
        """Export projects to a text file"""
        if not self.projects:
            messagebox.showwarning("Warning", "No projects to export!")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Projects",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.projects))

                messagebox.showinfo("Success", f"Exported {len(self.projects)} projects to {file_path}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export file: {str(e)}")

    def on_closing(self):
        """Handle application closing"""
        self.stop_timer()
        self.save_projects()
        self.root.destroy()


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = TimaApp(root)
    root.mainloop()


if __name__ == "__main__":
    import winsound

    # Play Windows exit sound.

    main()