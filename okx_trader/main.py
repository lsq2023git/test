import tkinter as tk
from ui.main_window import MainWindow

if __name__ == "__main__":
    print("OKX Trader application starting...")

    root = tk.Tk()
    app = MainWindow(root) # Pass the root window to the MainWindow class

    # Set a callback for the window close button
    def on_closing():
        print("OKX Trader application closing...")
        # Add any cleanup logic here if needed
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application interrupted by user. Closing...")
        on_closing()

    print("OKX Trader application finished.")
