import tkinter as tk

# Create a basic Tkinter window with grid layout
def create_window():
    root = tk.Tk()
    root.title("Basic EducationalRAG Window")
    root.geometry("400x200")  # Set window size

    # Label for text entry
    label = tk.Label(root, text="Enter text:")
    label.grid(row=0, column=0, padx=10, pady=10)  # Position the label

    # Text entry field
    entry = tk.Entry(root)
    entry.grid(row=0, column=1, padx=10, pady=10)  # Position the text entry

    # Text box to display the result
    output_text = tk.Text(root, height=5, wrap=tk.WORD)
    output_text.grid(row=2, column=0, columnspan=2, padx=10, pady=10)  # Span across 2 columns

    # Button to display the input in the text box
    def on_button_click():
        entered_text = entry.get()
        output_text.delete(1.0, tk.END)  # Clear previous text
        output_text.insert(tk.END, f"You entered: {entered_text}")

    button = tk.Button(root, text="Submit", command=on_button_click)
    button.grid(row=1, column=0, columnspan=2, pady=10)  # Center the button across 2 columns

    # Start the Tkinter event loop
    root.mainloop()

# Run the function to create the window
if __name__ == "__main__":
    create_window()
