import tkinter as tk
from tkinter import ttk, font
import subprocess
import threading

def create_styles():
    style = ttk.Style()
    style.theme_use('clam')
    
    # Define larger and more stylish fonts
    large_font = ('Verdana', 14)
    medium_font = ('Verdana', 12)
    small_font = ('Verdana', 10)
    
    # General frame and label styles
    style.configure('TFrame', background='#333940')
    style.configure('TLabel', background='#333940', foreground='white', font=large_font)
    
    # Specific styles for status updates
    style.configure('Error.TLabel', foreground='red', font=medium_font)
    style.configure('Success.TLabel', foreground='green', font=medium_font)
    style.configure('Running.TLabel', foreground='orange', font=medium_font)
    
    # Button and Radio Button styles
    style.configure('TButton', font=medium_font, borderwidth=1)
    style.configure('TRadiobutton', font=small_font, background='#333940', foreground='white')
    
    style.map('TButton',
              foreground=[('pressed', 'white'), ('active', 'white')],
              background=[('pressed', '!disabled', '#666666'), ('active', '#555555')],
              relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
    style.map('TRadiobutton',
              foreground=[('selected', 'green')],
              background=[('active', '#333940')],
              indicatorcolor=[('selected', 'green'), ('!selected', 'white')])

def create_gui():
    window = tk.Tk()
    window.title("Traffic Light Simulation Script Runner")
    window.geometry('600x400')  # Slightly larger window for better layout
    window.configure(bg='#333940')
    
    create_styles()
    
    frame_top = ttk.Frame(window, style='TFrame')
    frame_top.pack(fill='x', padx=30, pady=20)

    frame_middle = ttk.Frame(window, style='TFrame')
    frame_middle.pack(fill='x', padx=30, pady=20)
    
    frame_bottom = ttk.Frame(window, style='TFrame')
    frame_bottom.pack(fill='x', padx=30, pady=20)
    
    ttk.Label(frame_top, text="Traffic Light Simulation Script Runner", font=('Verdana', 16, 'bold')).pack(pady=10)
    
    selected_script = tk.StringVar(value="ML_Traffic Control")
    ttk.Radiobutton(frame_middle, text="ML Traffic Control", variable=selected_script, value="ML_Traffic Control").pack(side='top', anchor='w', pady=5)
    ttk.Radiobutton(frame_middle, text="Smart Traffic Control", variable=selected_script, value="Smart Traffic Control").pack(side='top', anchor='w', pady=5)
    
    status_label = ttk.Label(frame_bottom, text="Simulation Stopped", style='Error.TLabel')
    status_label.pack(pady=10)
    
    progress_bar = ttk.Progressbar(frame_bottom, orient='horizontal', length=300, mode='indeterminate')
    progress_bar.pack(pady=20)
    
    def run_script(script_name):
        def target():
            try:
                print(f"Running {script_name}...")
                subprocess.run(["python", script_name], check=True)
                status_label.config(text="Simulation Completed", style='Success.TLabel')
            except subprocess.CalledProcessError as e:
                status_label.config(text=f"Error: {str(e)}", style='Error.TLabel')
            finally:
                progress_bar.stop()

        status_label.config(text="Simulation Running...", style='Running.TLabel')
        progress_bar.start(10)
        threading.Thread(target=target).start()

    def run_selected_script():
        script_file = "ML_Main.py" if selected_script.get() == "ML Traffic Control" else "AVG_Time.py"
        run_script(script_file)
    
    run_button = ttk.Button(frame_bottom, text="Start Simulation", command=run_selected_script)
    run_button.pack(pady=20, fill='x', expand=True)
    
    window.mainloop()

if __name__ == "__main__":
    create_gui()
    