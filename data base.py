import qrcode
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sqlite3
import io
from PIL import Image, ImageTk

class QRCodeGenerator:
    def __init__(self, master):
        self.master = master
        master.title("Google Pay QR Code Generator")
        master.geometry("600x500")

        # Create label and entry widgets
        self.label = tk.Label(master, text="Enter data for Google Pay QR Code:")
        self.label.pack(pady=10)
        self.entry = tk.Entry(master, width=50)
        self.entry.pack(pady=5)

        # Create label and entry for QR code size
        self.size_label = tk.Label(master, text="Enter QR Code size (pixels):")
        self.size_label.pack(pady=10)
        self.size_entry = tk.Entry(master, width=20)
        self.size_entry.pack(pady=5)
        self.size_entry.insert(0, '300')  # Default size

        # Create button widgets
        self.generate_button = tk.Button(master, text="Generate QR Code", command=self.generate_qr_code)
        self.generate_button.pack(pady=10)
        self.save_button = tk.Button(master, text="Save QR Code", command=self.save_qr_code, state=tk.DISABLED)
        self.save_button.pack(pady=10)
        self.view_button = tk.Button(master, text="View Saved QR Codes", command=self.view_saved_qr_codes)
        self.view_button.pack(pady=10)

        # Initialize variables
        self.qr_code = None
        self.qr_image_label = tk.Label(master)
        self.qr_image_label.pack(pady=10)

        # Initialize the database
        self.conn = sqlite3.connect('googlepay_qrcodes.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS googlepay_qrcodes (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL UNIQUE,
                image BLOB NOT NULL
            )
        ''')
        self.conn.commit()

    def generate_qr_code(self):
        # Generate QR Code
        data = self.entry.get()
        size = self.size_entry.get()
        try:
            size = int(size)
            if size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid size", "Please enter a valid positive integer for the QR code size.")
            return

        if data:
            # Format data for Google Pay QR Code
            gpay_data = f"upi://pay?pa={data}&pn=Recipient&mc=1234&tid=1234&tr=123456"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(gpay_data)
            qr.make(fit=True)
            self.qr_code = qr.make_image(fill='black', back_color='white').resize((size, size))

            self.display_qr_code()
            self.save_button.config(state=tk.NORMAL)
            self.view_button.config(state=tk.NORMAL)
            # Save QR Code to database
            self.save_qr_code_to_db(data)
        else:
            self.qr_code = None
            self.save_button.config(state=tk.DISABLED)

    def display_qr_code(self):
        if self.qr_code:
            image = ImageTk.PhotoImage(self.qr_code)
            self.qr_image_label.config(image=image)
            self.qr_image_label.image = image  # Keep a reference to avoid garbage collection

    def save_qr_code_to_db(self, data):
        # Check if data already exists in the database
        self.cursor.execute('SELECT * FROM googlepay_qrcodes WHERE data = ?', (data,))
        result = self.cursor.fetchone()
        if result:
            messagebox.showinfo("Info", "QR Code for this data already exists.")
            return

        # Convert QR Code image to binary
        buffer = io.BytesIO()
        self.qr_code.save(buffer, format='PNG')
        image_data = buffer.getvalue()

        # Insert data and image into database
        self.cursor.execute('INSERT INTO googlepay_qrcodes (data, image) VALUES (?, ?)', (data, image_data))
        self.conn.commit()

    def save_qr_code(self):
        # Save QR Code as image file
        file_path = filedialog.asksaveasfilename(defaultextension=".png")
        if file_path:
            self.qr_code.save(file_path)

    def view_saved_qr_codes(self):
        self.view_window = tk.Toplevel(self.master)
        self.view_window.title("Saved Google Pay QR Codes")
        self.view_window.geometry("600x400")

        self.tree = ttk.Treeview(self.view_window, columns=('ID', 'Data'), show='headings')
        self.tree.heading('ID', text='ID')
        self.tree.heading('Data', text='Data')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.load_qr_codes()

        self.view_button_frame = tk.Frame(self.view_window)
        self.view_button_frame.pack(fill=tk.X)

        self.load_button = tk.Button(self.view_button_frame, text="Load QR Code", command=self.load_qr_code)
        self.load_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_button = tk.Button(self.view_button_frame, text="Delete QR Code", command=self.delete_qr_code)
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)

    def load_qr_codes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.cursor.execute('SELECT id, data FROM googlepay_qrcodes')
        for row in self.cursor.fetchall():
            self.tree.insert('', tk.END, values=row)

    def load_qr_code(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            qr_id = item['values'][0]
            self.cursor.execute('SELECT image FROM googlepay_qrcodes WHERE id = ?', (qr_id,))
            image_data = self.cursor.fetchone()[0]

            image = Image.open(io.BytesIO(image_data))
            image.show()
        else:
            messagebox.showwarning("Warning", "Please select a QR code to load.")

    def delete_qr_code(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            qr_id = item['values'][0]

            self.cursor.execute('DELETE FROM googlepay_qrcodes WHERE id = ?', (qr_id,))
            self.conn.commit()
            self.load_qr_codes()
        else:
            messagebox.showwarning("Warning", "Please select a QR code to delete.")

    def __del__(self):
        # Close the database connection when the program ends
        self.conn.close()

root = tk.Tk()
qrcode_generator = QRCodeGenerator(root)
root.mainloop()
