import tkinter as tk
from tkinter import ttk, Menu
from tkinter import messagebox
from src.bin.generator import generate_cvv, generate_pan, update_card_brand_display
from src.utils.validator import validate_pan, validate_expiry_date
from src.utils.import_export import import_bins_action, export_pans_action
from PIL import Image, ImageTk


class Application:
    def __init__(self):
        self.win = None
        
    def run(self):
        self.win = tk.Tk()
        self.win.title("PAN Generator App")
        setup_ui(self.win)
        self.win.mainloop()

def setup_ui(win):
    win.geometry('800x600')  # Setting the initial size of the window
    win.resizable(True, True)  # Allow the window to be resizable
    win.configure(bg='#f0f0f0')

    tabControl = ttk.Notebook(win)
    tab1 = ttk.Frame(tabControl)
    tabControl.add(tab1, text='PANS')
    tabControl.pack(expand=1, fill="both")

    mighty = ttk.LabelFrame(tab1, text=' Generate PAN(s)')
    mighty.grid(column=0, row=0, padx=8, pady=4, sticky='NSEW')

    # Configuring grid for expanding
    tab1.grid_columnconfigure(0, weight=1)
    tab1.grid_rowconfigure(0, weight=1)
    mighty.grid_columnconfigure(0, weight=1)
    mighty.grid_columnconfigure(1, weight=1)
    mighty.grid_columnconfigure(2, weight=1)
    mighty.grid_columnconfigure(3, weight=1)
    mighty.grid_rowconfigure(7, weight=1)

    # Row 0: Input BIN Label and Entry
    ttk.Label(mighty, text="Input BIN, use '?' to complete the unknown number(s):").grid(column=0, row=0, sticky='W', padx=5, pady=5, columnspan=2)
    name = tk.StringVar()
    name_entered = ttk.Entry(mighty, width=50, textvariable=name)
    name_entered.grid(column=0, row=1, sticky='W', padx=5, pady=5, columnspan=2)

    # Card brand images and checkboxes
    card_images = {
        'Visa': ImageTk.PhotoImage(Image.open('/Users/temi/Downloads/Visa.jpeg').resize((50, 50))),
        'Mastercard': ImageTk.PhotoImage(Image.open('/Users/temi/Downloads/mastercard.jpeg').resize((50, 50))),
        'American Express': ImageTk.PhotoImage(Image.open('/Users/temi/Downloads/Amex.jpeg').resize((50, 50)))
    }

    card_vars = {brand: tk.IntVar(value=0) for brand in card_images}
    card_checkboxes = {}
    for idx, (brand, image) in enumerate(card_images.items()):
        card_checkboxes[brand] = ttk.Checkbutton(mighty, text=brand, image=image, compound='left',
                                                 variable=card_vars[brand])
        card_checkboxes[brand].image = image  # Keeping a reference to the image
        card_checkboxes[brand].grid(column=idx, row=2, padx=5, pady=5, sticky='W')

    name_entered.bind('<KeyRelease>', lambda event: update_card_brand_display(name_entered, card_vars))

    # Row 1: Generate and Validate Buttons
    action_generate = ttk.Button(mighty, text="Generate", command=lambda: generate_action(name, tree, count_var))
    action_generate.grid(column=2, row=1, padx=5, pady=5)

    action_validate = ttk.Button(mighty, text="Validate", command=lambda: validate_action(name, validate_scr))
    action_validate.grid(column=3, row=1, padx=5, pady=5)

    # Text widget for displaying validation result
    validate_scr = tk.Text(mighty, width=40, height=5)
    validate_scr.grid(column=2, row=4, columnspan=2, padx=15, pady=5)

    # Row 2: Expiry Date Label and Entry
    expiry_label = ttk.Label(mighty, text="Expiry Date (MM/YY):")
    expiry_label.grid(column=0, row=3, sticky='W', padx=5, pady=5)
    expiry_date = tk.StringVar()
    expiry_entered = ttk.Entry(mighty, width=20, textvariable=expiry_date)
    expiry_entered.grid(column=1, row=3, sticky='W', padx=5, pady=5)

    # Row 3: Validate Expiry Button
    action_validate_expiry = ttk.Button(mighty, text="Validate Expiry", command=lambda: validate_expiry_action(expiry_date.get(), tree))
    action_validate_expiry.grid(column=2, row=3, padx=5, pady=5)

    # Row 4: Count Label and Entry
    count_label = ttk.Label(mighty, text="Total PANS Generated:")
    count_label.grid(column=0, row=4, sticky='W', padx=5, pady=5)
    count = tk.IntVar(value=1)
    count_var = tk.StringVar()
    count_entered = ttk.Entry(mighty, width=20, textvariable=count_var, state='readonly')
    count_entered.grid(column=1, row=4, sticky='W', padx=5, pady=5)

    # Row 5: CVV Label and Entry
    cvv_label = ttk.Label(mighty, text="CVV:")
    cvv_label.grid(column=0, row=5, sticky='W', padx=5, pady=5)
    cvv = tk.StringVar()
    cvv_generated = ttk.Entry(mighty, width=20, textvariable=cvv)
    cvv_generated.grid(column=1, row=5, sticky='W', padx=5, pady=5)

    # Row 6: Generate CVV Button
    action_generate_cvv = ttk.Button(mighty, text="Generate CVV", command=lambda: cvv.set(generate_cvv()))
    action_generate_cvv.grid(column=2, row=5, padx=5, pady=5)

    # Row 7: Import and Export Buttons
    import_button = ttk.Button(mighty, text="Import BIN", command=lambda: import_bins_action(tree))
    import_button.grid(column=0, row=6, sticky='W', padx=5, pady=5)
    export_button = ttk.Button(mighty, text="Export PANs", command=lambda: export_pans_action(tree))
    export_button.grid(column=1, row=6, sticky='W', padx=5, pady=5)

    # Row 8: Treeview with Scrollbar
    tree_frame = ttk.Frame(mighty)
    tree_frame.grid(column=0, row=7, columnspan=4, sticky='NSEW', padx=5, pady=5)

    tree_scroll = ttk.Scrollbar(tree_frame)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(tree_frame, columns=('PAN'), show='headings', yscrollcommand=tree_scroll.set)
    tree.heading('PAN', text='PANs Generated')
    tree.column('PAN', width=500)
    tree.pack(expand=True, fill='both')

    tree_scroll.config(command=tree.yview)

    # Menu bar setup
    menu_bar = Menu(win)
    win.config(menu=menu_bar)
    file_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    help_menu = Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "PAN Generator App v1.0"))
    menu_bar.add_cascade(label="Help", menu=help_menu)

def generate_action(name, tree, count_var):
    bin_input = name.get()
    if bin_input:
        for i in tree.get_children():
            tree.delete(i)
        pans = generate_pan(bin_input)
        if pans:
            for pan in pans:
                tree.insert('', tk.END, values=(pan, ))
            count_var.set('{:,}'.format(len(pans)))
        else:
            messagebox.showerror("Error", "Failed to generate PANs.")


def validate_action(name, scr):
    pan_input = name.get()
    is_valid, message = validate_pan(pan_input)
    scr.delete(1.0, tk.END)
    scr.insert(tk.END, message)


def validate_expiry_action(expiry_date, scr):
    is_valid, message = validate_expiry_date(expiry_date)
    scr.delete(1.0, tk.END)
    scr.insert(tk.END, message)

