#!/usr/bin/env python3
"""
VR Experiment Supervisor Control
A GUI application for controlling Unity VR experiments via UDP broadcast messages.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import json
import threading
import time
from datetime import datetime


class VRExperimentSupervisor:
    def __init__(self, root):
        self.root = root
        self.root.title("VR Experiment Supervisor Control")
        self.root.geometry("750x900")
        self.root.resizable(True, True)
        
        # Experiment configuration
        self.condition_types = ["Helpful", "Demotivating", "Control"]
        self.object_types = ["Brick", "Paperclip", "Rope"]
        
        # Experiment state
        self.experiment_sequence = []
        self.current_condition_index = 0
        self.experiment_configured = False
        self.condition_start_time = None
        self.countdown_timer = None
        self.countdown_active = False
        
        # UDP settings
        self.udp_ip = "10.195.83.255"
        self.udp_port = 1221
        
        # Create GUI
        self.create_gui()
        
        # Log initial status
        self.log_message("Application started. Ready to configure experiment.")
        
        # Start the countdown update timer
        self.update_countdown_display()
    
    def create_gui(self):
        """Create and layout all GUI elements"""
        
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for responsive design
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        row = 0
        
        # Instructions section
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions", padding="10")
        instructions_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        instructions_frame.columnconfigure(0, weight=1)
        
        instructions_text = (
            f"Broadcasting to: {self.udp_ip} on port {self.udp_port}\n"
            "Note: Shares port 1221 with avatar sync system\n"
            "1. Configure experiment parameters below\n"
            "2. Click 'Set Experiment Parameters' to confirm setup\n"
            "3. Use 'Start Current Condition' and 'Next Condition' to control experiment"
        )
        instructions_label = ttk.Label(instructions_frame, text=instructions_text, justify=tk.LEFT)
        instructions_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        row += 1
        
        # Session Information section
        session_frame = ttk.LabelFrame(main_frame, text="Session Information", padding="10")
        session_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        session_frame.columnconfigure(1, weight=1)
        
        # Group ID
        ttk.Label(session_frame, text="Group ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        self.group_id_var = tk.StringVar()
        self.group_id_entry = ttk.Entry(session_frame, textvariable=self.group_id_var, width=20)
        self.group_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Notes
        ttk.Label(session_frame, text="Notes:").grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10), pady=(5, 2))
        self.notes_text = scrolledtext.ScrolledText(session_frame, height=4, wrap=tk.WORD, width=50)
        self.notes_text.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 2))
        
        # Save button
        self.save_button = ttk.Button(session_frame, text="Save Session Data", command=self.save_session_data)
        self.save_button.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        row += 1
        
        # Experiment Setup section
        setup_frame = ttk.LabelFrame(main_frame, text="Experiment Setup", padding="10")
        setup_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        setup_frame.columnconfigure(1, weight=1)
        setup_frame.columnconfigure(3, weight=1)
        
        # Headers
        ttk.Label(setup_frame, text="Condition", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, padx=(0, 10), pady=(0, 5))
        ttk.Label(setup_frame, text="Condition Type", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=1, padx=(0, 10), pady=(0, 5))
        ttk.Label(setup_frame, text="Object", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=2, padx=(0, 10), pady=(0, 5))
        ttk.Label(setup_frame, text="Object Type", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=3, pady=(0, 5))
        
        # Create dropdowns for each condition
        self.condition_vars = []
        self.object_vars = []
        
        for i in range(3):
            # Condition label
            ttk.Label(setup_frame, text=f"Condition {i+1}:").grid(row=i+1, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            
            # Condition type dropdown
            condition_var = tk.StringVar()
            condition_combo = ttk.Combobox(setup_frame, textvariable=condition_var, values=self.condition_types, state="readonly", width=15)
            condition_combo.grid(row=i+1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=2)
            self.condition_vars.append(condition_var)
            
            # Object label
            ttk.Label(setup_frame, text="Object:").grid(row=i+1, column=2, sticky=tk.W, padx=(0, 10), pady=2)
            
            # Object type dropdown
            object_var = tk.StringVar()
            object_combo = ttk.Combobox(setup_frame, textvariable=object_var, values=self.object_types, state="readonly", width=15)
            object_combo.grid(row=i+1, column=3, sticky=(tk.W, tk.E), pady=2)
            self.object_vars.append(object_var)
        
        # Set experiment parameters button
        self.set_params_button = ttk.Button(setup_frame, text="Set Experiment Parameters", command=self.set_experiment_parameters)
        self.set_params_button.grid(row=4, column=0, columnspan=4, pady=(10, 0))
        
        row += 1
        
        # Current Experiment Display section
        display_frame = ttk.LabelFrame(main_frame, text="Current Experiment Sequence", padding="10")
        display_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        display_frame.columnconfigure(0, weight=1)
        
        self.sequence_display = scrolledtext.ScrolledText(display_frame, height=6, state=tk.DISABLED, wrap=tk.WORD)
        self.sequence_display.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        row += 1
        
        # Control Buttons section
        control_frame = ttk.LabelFrame(main_frame, text="Experiment Control", padding="10")
        control_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)
        control_frame.columnconfigure(3, weight=1)
        
        self.start_button = ttk.Button(control_frame, text="Start Current Condition", command=self.start_current_condition, state=tk.DISABLED)
        self.start_button.grid(row=0, column=0, padx=(0, 5), pady=5, sticky=(tk.W, tk.E))
        
        self.next_button = ttk.Button(control_frame, text="Next Condition", command=self.next_condition, state=tk.DISABLED)
        self.next_button.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.force_next_button = ttk.Button(control_frame, text="Force Next (Override Timer)", command=self.force_next_condition, state=tk.DISABLED)
        self.force_next_button.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.reset_button = ttk.Button(control_frame, text="Reset Experiment", command=self.reset_experiment)
        self.reset_button.grid(row=0, column=3, padx=(5, 0), pady=5, sticky=(tk.W, tk.E))
        
        row += 1
        
        # Status Display section
        status_frame = ttk.LabelFrame(main_frame, text="Experiment Status", padding="10")
        status_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Ready to configure experiment", font=("TkDefaultFont", 10, "bold"))
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Countdown timer display
        self.countdown_label = ttk.Label(status_frame, text="", font=("TkDefaultFont", 12, "bold"), foreground="red")
        self.countdown_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        row += 1
        
        # Error/Log Display section
        log_frame = ttk.LabelFrame(main_frame, text="Log Messages", padding="10")
        log_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(row, weight=1)
        
        self.log_display = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.log_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def log_message(self, message):
        """Add a timestamped message to the log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_display.config(state=tk.NORMAL)
        self.log_display.insert(tk.END, formatted_message)
        self.log_display.see(tk.END)
        self.log_display.config(state=tk.DISABLED)
    
    def update_status(self, status):
        """Update the status label"""
        self.status_label.config(text=status)
        self.log_message(f"Status: {status}")
    
    def start_countdown_timer(self):
        """Start the 5-minute countdown timer for the current condition"""
        self.condition_start_time = time.time()
        self.countdown_active = True
        self.log_message("5-minute countdown timer started for current condition")
    
    def update_countdown_display(self):
        """Update the countdown display every second"""
        if self.countdown_active and self.condition_start_time is not None:
            elapsed_time = time.time() - self.condition_start_time
            remaining_time = max(0, 300 - elapsed_time)  # 300 seconds = 5 minutes
            
            if remaining_time > 0:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                self.countdown_label.config(text=f"Time Remaining: {minutes:02d}:{seconds:02d}")
            else:
                # Timer expired
                self.countdown_label.config(text="TIME EXPIRED - Block Finished")
                self.countdown_active = False
                self.condition_finished()
        else:
            self.countdown_label.config(text="")
        
        # Schedule next update
        self.root.after(1000, self.update_countdown_display)
    
    def condition_finished(self):
        """Called when the 5-minute timer expires"""
        self.log_message("5-minute timer expired - sending disable_all command")
        
        # Send command to Unity to disable all objects and avatars
        message_data = {
            "command": "disable_all",
            "reason": "timer_expired"
        }
        
        if self.send_udp_message(message_data):
            self.update_status("Block finished - All objects disabled. Ready for next condition.")
            # Enable next condition button if not the last condition
            if self.current_condition_index < len(self.experiment_sequence) - 1:
                self.next_button.config(state=tk.NORMAL)
                self.force_next_button.config(state=tk.DISABLED)  # Disable force button when timer expires
    
    def force_next_condition(self):
        """Force move to next condition (override timer)"""
        if messagebox.askyesno("Override Timer", "Are you sure you want to skip the remaining time and move to the next condition?"):
            # Stop the current timer
            self.countdown_active = False
            self.log_message("Timer manually overridden by supervisor")
            
            # Call the condition finished function to disable current objects
            self.condition_finished()
    
    def save_session_data(self):
        """Save session data to a text file"""
        try:
            group_id = self.group_id_var.get().strip()
            if not group_id:
                messagebox.showerror("Error", "Please enter a Group ID before saving.")
                return
            
            if not self.experiment_configured:
                messagebox.showerror("Error", "Please configure the experiment before saving.")
                return
            
            # Create filename with group ID and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"VR_Experiment_{group_id}_{timestamp}.txt"
            
            # Prepare data to save
            notes = self.notes_text.get(1.0, tk.END).strip()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"VR Experiment Session Data\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"Group ID: {group_id}\n")
                f.write(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Current Condition Index: {self.current_condition_index}\n\n")
                
                f.write(f"Experiment Sequence:\n")
                f.write(f"-" * 20 + "\n")
                for i, condition in enumerate(self.experiment_sequence):
                    status = ""
                    if i < self.current_condition_index:
                        status = " [COMPLETED]"
                    elif i == self.current_condition_index:
                        status = " [CURRENT]"
                    else:
                        status = " [PENDING]"
                    
                    f.write(f"Condition {i+1}: {condition['condition_type']} ({condition['object_type']}){status}\n")
                
                f.write(f"\nSupervisor Notes:\n")
                f.write(f"-" * 20 + "\n")
                if notes:
                    f.write(f"{notes}\n")
                else:
                    f.write("No notes provided.\n")
            
            self.log_message(f"Session data saved to: {filename}")
            messagebox.showinfo("Success", f"Session data saved to:\n{filename}")
            
        except Exception as e:
            error_msg = f"Failed to save session data: {str(e)}"
            self.log_message(f"ERROR: {error_msg}")
            messagebox.showerror("Error", error_msg)
    
    def set_experiment_parameters(self):
        """Validate and set the experiment parameters"""
        try:
            # Get selected values
            selected_conditions = [var.get() for var in self.condition_vars]
            selected_objects = [var.get() for var in self.object_vars]
            
            # Validate that all dropdowns are filled
            if any(not cond for cond in selected_conditions) or any(not obj for obj in selected_objects):
                messagebox.showerror("Error", "Please select condition types and objects for all three conditions.")
                return
            
            # Validate that each condition type is used exactly once
            if len(set(selected_conditions)) != 3 or set(selected_conditions) != set(self.condition_types):
                messagebox.showerror("Error", "Each condition type (Helpful, Demotivating, Control) must be used exactly once.")
                return
            
            # Validate that each object type is used exactly once
            if len(set(selected_objects)) != 3 or set(selected_objects) != set(self.object_types):
                messagebox.showerror("Error", "Each object type (Brick, Paperclip, Rope) must be used exactly once.")
                return
            
            # Create experiment sequence
            self.experiment_sequence = []
            for i in range(3):
                self.experiment_sequence.append({
                    "condition_index": i,
                    "condition_type": selected_conditions[i],
                    "object_type": selected_objects[i]
                })
            
            self.current_condition_index = 0
            self.experiment_configured = True
            
            # Update sequence display
            self.update_sequence_display()
            
            # Enable control buttons
            self.start_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.DISABLED)  # Will be enabled after timer
            self.force_next_button.config(state=tk.DISABLED)  # Will be enabled after start
            
            # Update status
            self.update_status("Experiment configured. Ready to start first condition.")
            
            messagebox.showinfo("Success", "Experiment parameters set successfully!")
            
        except Exception as e:
            self.log_message(f"Error setting experiment parameters: {str(e)}")
            messagebox.showerror("Error", f"Failed to set experiment parameters: {str(e)}")
    
    def update_sequence_display(self):
        """Update the experiment sequence display"""
        if not self.experiment_configured:
            display_text = "No experiment configured."
        else:
            display_text = "Experiment Sequence:\n\n"
            for i, condition in enumerate(self.experiment_sequence):
                status = ""
                if i < self.current_condition_index:
                    status = " [COMPLETED]"
                elif i == self.current_condition_index:
                    status = " [CURRENT]"
                else:
                    status = " [PENDING]"
                
                display_text += f"Condition {i+1}: {condition['condition_type']} ({condition['object_type']}){status}\n"
        
        self.sequence_display.config(state=tk.NORMAL)
        self.sequence_display.delete(1.0, tk.END)
        self.sequence_display.insert(1.0, display_text)
        self.sequence_display.config(state=tk.DISABLED)
    
    def send_udp_message(self, message_data):
        """Send UDP broadcast message"""
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Convert message to JSON
            json_message = json.dumps(message_data)
            
            # Send message
            sock.sendto(json_message.encode('utf-8'), (self.udp_ip, self.udp_port))
            sock.close()
            
            self.log_message(f"Sent UDP message: {json_message}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send UDP message: {str(e)}"
            self.log_message(f"ERROR: {error_msg}")
            messagebox.showerror("Network Error", error_msg)
            return False
    
    def start_current_condition(self):
        """Start the current condition"""
        if not self.experiment_configured or self.current_condition_index >= len(self.experiment_sequence):
            return
        
        current_condition = self.experiment_sequence[self.current_condition_index]
        
        message_data = {
            "command": "start_condition",
            "condition_type": current_condition["condition_type"],
            "object_type": current_condition["object_type"],
            "condition_index": self.current_condition_index
        }
        
        if self.send_udp_message(message_data):
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)  # Disabled until timer expires
            # Enable force next button if there are more conditions
            if self.current_condition_index < len(self.experiment_sequence) - 1:
                self.force_next_button.config(state=tk.NORMAL)
            
            condition_name = f"{current_condition['condition_type']} ({current_condition['object_type']})"
            self.update_status(f"Current Condition: {condition_name}")
            self.update_sequence_display()
            
            # Start the 5-minute countdown timer
            self.start_countdown_timer()
    
    def next_condition(self):
        """Move to the next condition"""
        if not self.experiment_configured:
            return
        
        self.current_condition_index += 1
        
        if self.current_condition_index >= len(self.experiment_sequence):
            # Experiment completed
            self.update_status("Experiment Completed")
            self.start_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.update_sequence_display()
            messagebox.showinfo("Experiment Complete", "All conditions have been completed!")
            return
        
        current_condition = self.experiment_sequence[self.current_condition_index]
        
        message_data = {
            "command": "next_condition",
            "condition_type": current_condition["condition_type"],
            "object_type": current_condition["object_type"],
            "condition_index": self.current_condition_index
        }
        
        if self.send_udp_message(message_data):
            # Update UI
            self.next_button.config(state=tk.DISABLED)  # Disabled until timer expires
            # Enable force next button if there are more conditions after this one
            if self.current_condition_index < len(self.experiment_sequence) - 1:
                self.force_next_button.config(state=tk.NORMAL)
            else:
                self.force_next_button.config(state=tk.DISABLED)
            
            condition_name = f"{current_condition['condition_type']} ({current_condition['object_type']})"
            self.update_status(f"Current Condition: {condition_name}")
            self.update_sequence_display()
            
            # Start the 5-minute countdown timer for the new condition
            self.start_countdown_timer()
    
    def reset_experiment(self):
        """Reset the experiment to allow new configuration"""
        if messagebox.askyesno("Reset Experiment", "Are you sure you want to reset the experiment? This will clear the current configuration."):
            # Reset state
            self.experiment_sequence = []
            self.current_condition_index = 0
            self.experiment_configured = False
            self.countdown_active = False
            self.condition_start_time = None
            
            # Clear dropdowns
            for var in self.condition_vars:
                var.set("")
            for var in self.object_vars:
                var.set("")
            
            # Reset UI
            self.start_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.force_next_button.config(state=tk.DISABLED)
            self.update_status("Ready to configure experiment")
            self.update_sequence_display()
            
            self.log_message("Experiment reset. Ready for new configuration.")


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = VRExperimentSupervisor(root)
    
    # Center the window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Start the GUI event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user.")


if __name__ == "__main__":
    main() 
