import asyncio
import tkinter as tk
from threading import Thread
from hello import main as document_handler
from appendaudio import main as general_handler
from Attendance_email import main as attendance_handler 

class MicroserviceRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("Microservice Runner")

        # Create buttons
        self.doc_button = tk.Button(root, text="Run Document Handler", command=self.run_document_handler)
        self.doc_button.pack(pady=10)

        self.gen_button = tk.Button(root, text="Run General Handler", command=self.run_general_handler)
        self.gen_button.pack(pady=10)

        self.att_button = tk.Button(root, text="Run Attendance Handler", command=self.run_attendance_handler)
        self.att_button.pack(pady=10)

        self.quit_button = tk.Button(root, text="Quit", command=self.quit)
        self.quit_button.pack(pady=10)


    def quit(self):
        # Properly stop any ongoing asyncio tasks if needed
        self.root.quit()

    def run_document_handler(self):
        document_handler()

    def run_general_handler(self):
        general_handler()
    
    def run_attendance_handler(self):
        attendance_handler()
    

if __name__ == "__main__":
    root = tk.Tk()
    app = MicroserviceRunner(root)
    root.mainloop()
