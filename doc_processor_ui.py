import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
from doc_processor import DocumentProcessor
import os
from datetime import datetime
import subprocess
from PIL import Image
from tkcalendar import DateEntry
import tkinter.ttk as ttk
import sys

class DocumentProcessorUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize document processor and settings
        self.doc_processor = DocumentProcessor()
        self.selected_folder = "Shitongeni"
        self.processing = False
        self.log_visible = False
        
        # Get the correct paths using the DocumentProcessor's method for consistency
        self.documents_path = self.doc_processor.get_documents_path()
        self.printable_docs_path = os.path.join(self.documents_path, "Printable Documents")
        self.resumes_path = os.path.join(self.documents_path, "Resumes")
        
        # Set logo path using relative paths based on the application's location
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            self.base_dir = os.path.dirname(sys.executable)
            if os.path.basename(self.base_dir) == '_internal':
                self.logo_path = os.path.join(self.base_dir, "public", "assets", "twinrain-logo.png")
            else:
                self.logo_path = os.path.join(self.base_dir, "_internal", "public", "assets", "twinrain-logo.png")
        else:
            # If running as script
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.logo_path = os.path.join(self.base_dir, "public", "assets", "twinrain-logo.png")

        # Configure logging and UI
        self.setup_logging()
        self.setup_ui()
        
        # Select default folder after UI creation and maximize window
        self.after(100, lambda: [self.state('zoomed'), self.select_folder("Shitongeni")])

    def setup_ui(self):
        """Initialize UI configuration"""
        # Set dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configure window
        self.title("Document Processor")
        self.geometry("1200x800")
        self.state('zoomed')
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set minimum window size to ensure elements remain visible
        self.minsize(1000, 700)

        # Create layout
        self.create_layout()

    def create_layout(self):
        """Create main layout"""
        # Create main container with grid layout for better scaling
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=5)  # Increase weight of main content area
        self.grid_rowconfigure(0, weight=1)
        
        # Create sidebar with reduced width
        self.sidebar = ctk.CTkFrame(self, width=220)  # Reduced from 300 to 220
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.sidebar.grid_propagate(False)
        
        # Create main content area
        self.main_content = ctk.CTkFrame(self)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        
        # Configure main_content for vertical layout
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=0)  # Header
        self.main_content.grid_rowconfigure(1, weight=0)  # Folder selection
        self.main_content.grid_rowconfigure(2, weight=0)  # Input fields (non-scrollable)
        self.main_content.grid_rowconfigure(3, weight=0)  # Progress section
        
        # Create UI sections
        self.create_header()
        self.create_folder_section()
        self.create_input_fields()
        self.create_progress_section()
        self.create_sidebar_content()

    def create_button(self, parent, text, command, **kwargs):
        """Create a standardized button"""
        default_config = {
            'height': 40,
            'font': ctk.CTkFont(size=14, weight="bold"),
            'text_color': "white",
            'fg_color': "#1f538d",
            'hover_color': "#2d7bd4"
        }
        default_config.update(kwargs)
        
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            **default_config
        )

    def create_folder_section(self):
        """Create folder selection section"""
        folder_frame = ctk.CTkFrame(self.main_content)
        folder_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Configure folder frame layout
        folder_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            folder_frame,
            text="Select Folder",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 15))

        button_frame = ctk.CTkFrame(folder_frame)
        button_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Create folder buttons
        self.shitongeni_btn = self.create_button(
            button_frame,
            "Shitongeni",
            lambda: self.select_folder("Shitongeni"),
            width=200
        )
        self.shitongeni_btn.pack(side="left", padx=10, expand=True)
        
        self.wilson_btn = self.create_button(
            button_frame,
            "Wilson",
            lambda: self.select_folder("Wilson"),
            width=200
        )
        self.wilson_btn.pack(side="right", padx=10, expand=True)

    def create_input_fields(self):
        """Create input fields section"""
        # Use a regular frame instead of scrollable frame
        input_container = ctk.CTkFrame(self.main_content)
        input_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Configure input container layout
        input_container.grid_columnconfigure(0, weight=1)
        
        # Title for the section
        title = ctk.CTkLabel(
            input_container,
            text="Document Information",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(10, 15))
        
        # Create a regular frame for fields
        fields_frame = ctk.CTkFrame(input_container)
        fields_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.entries = {}
        for i, (keyword, prompt) in enumerate(self.doc_processor.keywords_prompts.items()):
            field_frame = ctk.CTkFrame(fields_frame)
            field_frame.pack(fill="x", padx=5, pady=5)
            
            label = ctk.CTkLabel(
                field_frame,
                text=prompt,
                font=ctk.CTkFont(size=12),
                width=200,
                anchor="w"
            )
            label.pack(side="left", padx=(10, 5))
            
            # Special handling for closing date and time
            if keyword == "*ADD DD*":
                # Create date picker
                date_frame = ctk.CTkFrame(field_frame)
                date_frame.pack(side="left", fill="x", expand=True, padx=(5, 10))
                
                date_picker = DateEntry(date_frame, width=20, background='darkblue',
                                    foreground='white', borderwidth=2)
                date_picker.pack(side="left", padx=5, pady=5)
                self.entries[keyword] = date_picker
                
            elif keyword == "*C&T*":
                # Create time picker frame
                time_frame = ctk.CTkFrame(field_frame)
                time_frame.pack(side="left", fill="x", expand=True, padx=(5, 10))
                
                # Hours entry field
                hour_var = tk.StringVar(value="01")
                hour_entry = ctk.CTkEntry(
                    time_frame,
                    textvariable=hour_var,
                    width=50,
                    height=35,
                    font=ctk.CTkFont(size=12),
                    placeholder_text="HH"
                )
                hour_entry.pack(side="left", padx=2)
                
                # Separator label
                separator = ctk.CTkLabel(
                    time_frame,
                    text=":",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    width=10
                )
                separator.pack(side="left")
                
                # Minutes entry field
                minute_var = tk.StringVar(value="00")
                minute_entry = ctk.CTkEntry(
                    time_frame,
                    textvariable=minute_var,
                    width=50,
                    height=35,
                    font=ctk.CTkFont(size=12),
                    placeholder_text="MM"
                )
                minute_entry.pack(side="left", padx=2)
                
                # AM/PM picker
                ampm_var = tk.StringVar(value="PM")
                ampm_menu = ctk.CTkOptionMenu(
                    time_frame,
                    variable=ampm_var,
                    values=["AM", "PM"],
                    width=70,
                    height=35,
                    font=ctk.CTkFont(size=12)
                )
                ampm_menu.pack(side="left", padx=2)
                
                self.entries[keyword] = (hour_var, minute_var, ampm_var)
            else:
                # Regular text entry for other fields
                entry = ctk.CTkEntry(
                    field_frame,
                    placeholder_text=f"Enter {prompt.lower().strip(': ')}",
                    height=35,
                    font=ctk.CTkFont(size=12)
                )
                entry.pack(side="left", fill="x", expand=True, padx=(5, 10))
                self.entries[keyword] = entry

    def create_progress_section(self):
        """Create progress section"""
        progress_frame = ctk.CTkFrame(self.main_content)
        progress_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Configure progress frame layout
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to process documents",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=5)
        self.progress_bar.set(0)
        
        button_frame = ctk.CTkFrame(progress_frame)
        button_frame.pack(fill="x", pady=10)
        
        self.process_button = ctk.CTkButton(
            button_frame,
            text="Process Documents",
            command=self.process_documents,
            state="disabled",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            hover_color=("#1f538d", "#2d7bd4")
        )
        self.process_button.pack(pady=5)

    def create_sidebar_content(self):
        """Create sidebar with both Printable Documents and Resumes sections"""
        # Create scrollable frame for all content
        self.sidebar_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent"
        )
        self.sidebar_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Create Printable Documents section
        self.create_document_section(
            "Printable Documents",
            self.printable_docs_path,
            self.sidebar_scroll
        )

        # Add separator
        separator = ctk.CTkFrame(
            self.sidebar_scroll,
            height=2,
            fg_color=("gray75", "gray25")
        )
        separator.pack(fill="x", padx=5, pady=15)

        # Create Resumes section
        self.create_document_section(
            "Resumes",
            self.resumes_path,
            self.sidebar_scroll
        )
        
        # Add separator
        separator2 = ctk.CTkFrame(
            self.sidebar_scroll,
            height=2,
            fg_color=("gray75", "gray25")
        )
        separator2.pack(fill="x", padx=5, pady=15)
        
        # Add signature at the bottom
        signature_frame = ctk.CTkFrame(
            self.sidebar_scroll,
            fg_color="transparent"
        )
        signature_frame.pack(fill="x", padx=5, pady=5)
        
        # Add Abraham's signature
        signature_label = ctk.CTkLabel(
            signature_frame,
            text="Call Abraham for Help",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold"),
            text_color="#1f538d"
        )
        signature_label.pack(pady=10, anchor="center")

    def create_document_section(self, title, path, parent):
        """Create a section in the sidebar for documents"""
        # Section title
        section_title = ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        section_title.pack(fill="x", pady=(10, 15))

        # Get list of folders
        try:
            if os.path.exists(path):
                folders = [f for f in os.listdir(path) 
                          if os.path.isdir(os.path.join(path, f))]
                
                if not folders:
                    self.log_message(f"No folders found in {title} directory: {path}")
                    no_folders_label = ctk.CTkLabel(
                        parent,
                        text=f"No folders found in {title}",
                        font=ctk.CTkFont(size=11, slant="italic"),
                        text_color="gray60"
                    )
                    no_folders_label.pack(fill="x", padx=10, pady=5)
            else:
                self.log_message(f"Path does not exist: {path}")
                path_error_label = ctk.CTkLabel(
                    parent,
                    text=f"Directory not found: {os.path.basename(path)}",
                    font=ctk.CTkFont(size=11, slant="italic"),
                    text_color="gray60"
                )
                path_error_label.pack(fill="x", padx=10, pady=5)
                return
        except Exception as e:
            self.log_message(f"Error accessing {title}: {str(e)}")
            error_label = ctk.CTkLabel(
                parent,
                text=f"Error: {str(e)}",
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color="gray60"
            )
            error_label.pack(fill="x", padx=10, pady=5)
            return

        for folder in folders:
            # Folder label with background
            folder_label_frame = ctk.CTkFrame(parent)
            folder_label_frame.pack(fill="x", padx=5, pady=(10, 5))
            
            label = ctk.CTkLabel(
                folder_label_frame,
                text=folder,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            )
            label.pack(fill="x", padx=10, pady=5)
            
            # Get documents in this folder
            folder_path = os.path.join(path, folder)
            try:
                if os.path.exists(folder_path):
                    documents = [f for f in os.listdir(folder_path) 
                               if f.endswith(('.pdf', '.docx'))]  # Support both PDF and Word
                    
                    if not documents:
                        no_docs_label = ctk.CTkLabel(
                            parent,
                            text=f"No documents found in {folder}",
                            font=ctk.CTkFont(size=11, slant="italic"),
                            text_color="gray60"
                        )
                        no_docs_label.pack(fill="x", padx=20, pady=2)
                        continue
                else:
                    self.log_message(f"Folder path does not exist: {folder_path}")
                    continue
            except Exception as e:
                self.log_message(f"Error accessing folder {folder}: {str(e)}")
                continue
            
            # Create document buttons
            for doc in documents:
                doc_frame = ctk.CTkFrame(parent, fg_color="transparent")
                doc_frame.pack(fill="x", padx=5, pady=2)
                
                # Add icon based on file type
                icon = "📄 " if doc.endswith('.pdf') else "📝 "
                
                doc_button = ctk.CTkButton(
                    doc_frame,
                    text=f"{icon}{doc}",
                    command=lambda f=folder_path, d=doc: self.view_document(f, d),
                    anchor="w",
                    font=ctk.CTkFont(size=11),
                    height=30,
                    fg_color="transparent",
                    text_color="gray75",
                    hover_color="gray25"
                )
                doc_button.pack(fill="x", padx=(20, 5))

    def view_document(self, folder_path, document):
        """Open the selected document"""
        try:
            doc_path = os.path.join(folder_path, document)
            if os.path.exists(doc_path):
                # Use the default application to open the file
                os.startfile(doc_path)
            else:
                messagebox.showerror("Error", "Document not found")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening document: {str(e)}")

    def setup_logging(self):
        """Configure logging to both file and custom handler"""
        # Initialize log messages list first
        self.log_messages = []
        
        class CustomHandler(logging.Handler):
            def __init__(self, log_messages):
                super().__init__()
                self.log_messages = log_messages

            def emit(self, record):
                log_entry = self.format(record)
                self.log_messages.append(log_entry)

        # Add custom handler to existing logger
        try:
            custom_handler = CustomHandler(self.log_messages)
            custom_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.doc_processor.logger.addHandler(custom_handler)
        except Exception as e:
            print(f"Error setting up logging: {str(e)}")

    def log_message(self, message):
        """Log message without updating UI"""
        # Just print to console instead of updating UI
        print(f"Log: {message}")

    def update_progress(self, current, total, file_path):
        """Update progress bar and label"""
        progress = current / total
        self.progress_bar.set(progress)
        self.progress_label.configure(
            text=f"Processing {os.path.basename(file_path)} ({current}/{total})"
        )
        self.update()

    def select_folder(self, folder_name):
        """Handle folder selection"""
        self.selected_folder = folder_name
        
        # Reset both buttons to default state
        for btn in [self.shitongeni_btn, self.wilson_btn]:
            btn.configure(
                state="normal",
                fg_color="#1f538d",
                text_color="white",
                font=ctk.CTkFont(size=14, weight="bold")
            )
        
        # Configure selected button
        selected_btn = self.shitongeni_btn if folder_name == "Shitongeni" else self.wilson_btn
        selected_btn.configure(
            state="disabled",
            fg_color="#2d7bd4"
        )
        
        # Update UI
        self.process_button.configure(state="normal")
        self.progress_label.configure(text=f"Selected folder: {folder_name}")
        self.log_message(f"\nSelected folder: {folder_name}")

    def process_documents(self):
        """Handle document processing"""
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first")
            return
        
        # Get and validate form values
        try:
            replacements = self.get_form_values()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        # Disable UI during processing
        self.set_processing_state(True)

        try:
            # Process documents
            result = self.doc_processor.process_documents(
                self.selected_folder,
                replacements,
                self.update_progress
            )
            
            if result:
                output_dir = result['output_directory']
                final_pdf = result['final_pdf']
                word_docs = result.get('word_documents', [])
                checklist_pdf = result.get('checklist_pdf')
                
                # Show success message with file information
                self.log_message(f"\nProcessing complete!")
                self.log_message(f"Output directory: {output_dir}")
                self.log_message(f"Final PDF: {os.path.basename(final_pdf)} (does not include cover page or TOC)")
                
                # Display information about the separate checklist PDF
                if checklist_pdf:
                    self.log_message(f"Tender and RFQ Checklist PDF kept separate: {os.path.basename(checklist_pdf)}")
                
                if word_docs:
                    self.log_message(f"Cover page and TOC from Extras folder (kept as Word docs only): {', '.join(word_docs)}")
                else:
                    self.log_message(f"No cover page or TOC found in Extras folder")
                
                # Open output folder
                if os.path.exists(output_dir):
                    os.startfile(output_dir)
            else:
                self.handle_failure()

        except Exception as e:
            self.log_message(f"\nError: {str(e)}")
            messagebox.showerror("Error", str(e))

        finally:
            self.set_processing_state(False)

    def get_form_values(self):
        """Get and validate form values"""
        replacements = {}
        for keyword, entry in self.entries.items():
            if keyword == "*ADD DD*":
                value = entry.get_date().strftime("%d/%m/%Y")
            elif keyword == "*C&T*":
                value = self.get_time_value(entry)
            else:
                value = entry.get().strip()
                
            if not value:
                raise ValueError(f"Please fill in the field: {self.doc_processor.keywords_prompts[keyword]}")
            
            replacements[keyword] = value
        return replacements

    def get_time_value(self, time_entries):
        """Get formatted time value"""
        hour_var, minute_var, ampm_var = time_entries
        hour = int(hour_var.get())
        minute = int(minute_var.get())
        
        if not (1 <= hour <= 12):
            raise ValueError("Hour must be between 1 and 12")
        if not (0 <= minute <= 59):
            raise ValueError("Minutes must be between 0 and 59")
        
        # Convert to 24-hour format
        if ampm_var.get() == "PM" and hour != 12:
            hour += 12
        elif ampm_var.get() == "AM" and hour == 12:
            hour = 0
            
        return f"{hour:02d}:{minute:02d}"

    def set_processing_state(self, is_processing):
        """Set UI state during processing"""
        state = "disabled" if is_processing else "normal"
        self.process_button.configure(
            state=state,
            text="Processing..." if is_processing else "Process Documents"
        )
        self.shitongeni_btn.configure(state=state)
        self.wilson_btn.configure(state=state)
        
        if not is_processing:
            self.progress_bar.set(0)
            for entry in self.entries.values():
                if isinstance(entry, (tk.StringVar, tk.IntVar, tk.DoubleVar)):
                    entry.set("")

    def handle_success(self, result):
        """Handle successful document processing"""
        self.progress_label.configure(text="Processing complete!")
        self.log_message(
            f"\nProcessing complete!\nDocuments saved in: {result['output_directory']}"
        )
        if result.get('final_pdf'):
            self.log_message(f"Final PDF created: {os.path.basename(result['final_pdf'])}")
        
        # Log about the separate Tender and RFQ Checklist PDF
        if result.get('checklist_pdf'):
            self.log_message(f"Tender and RFQ Checklist PDF kept separate: {os.path.basename(result['checklist_pdf'])}")
        
        messagebox.showinfo(
            "Success",
            f"Documents processed successfully!\nOutput directory: {result['output_directory']}"
        )
        
        # Ask user if they want to open the output folder
        if messagebox.askyesno(
            "Open Folder",
            "Would you like to open the output folder?",
            icon="question"
        ):
            try:
                os.startfile(result['output_directory'])
            except Exception as e:
                self.log_message(f"Error opening folder: {str(e)}")
                messagebox.showerror("Error", f"Could not open folder: {str(e)}")

    def handle_failure(self):
        """Handle document processing failure"""
        self.progress_label.configure(text="Processing failed. Check logs for details.")
        messagebox.showerror(
            "Error",
            "Failed to process documents. Check logs for details."
        )

    def on_closing(self):
        """Handle window closing"""
        try:
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                if os.name == 'nt':
                    os.system('taskkill /f /im WINWORD.EXE')
                self.quit()
                os._exit(0)
        except:
            os._exit(0)

    def create_header(self):
        """Create header section with logo, title and description"""
        header_frame = ctk.CTkFrame(self.main_content)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Configure header layout
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Create logo frame
        logo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(10, 5))
        
        # Load and display logo
        try:
            if os.path.exists(self.logo_path):
                logo_image = Image.open(self.logo_path)
                # Resize logo to appropriate size (e.g., 200px width)
                logo_width = 200
                aspect_ratio = logo_image.height / logo_image.width
                logo_height = int(logo_width * aspect_ratio)
                logo_image = logo_image.resize((logo_width, logo_height))
                logo_photo = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(logo_width, logo_height))
                logo_label = ctk.CTkLabel(logo_frame, image=logo_photo, text="")
                logo_label.pack(pady=(0, 10))
            else:
                # Create a simple text label if logo is not found
                self.log_message(f"Logo not found at: {self.logo_path}")
                logo_label = ctk.CTkLabel(
                    logo_frame, 
                    text="TwinRain", 
                    font=ctk.CTkFont(size=28, weight="bold"),
                    text_color="#1f538d"
                )
                logo_label.pack(pady=(0, 10))
        except Exception as e:
            # Handle any errors during logo loading
            self.log_message(f"Error loading logo: {str(e)}")
            # Create text label as fallback
            logo_label = ctk.CTkLabel(
                logo_frame, 
                text="TwinRain", 
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color="#1f538d"
            )
            logo_label.pack(pady=(0, 10))
        
        title = ctk.CTkLabel(
            header_frame, 
            text="Document Processor",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(10, 5))
        
        description = ctk.CTkLabel(
            header_frame,
            text="Process documents and convert to PDF with text replacement",
            font=ctk.CTkFont(size=14),
            text_color="gray70"
        )
        description.pack(pady=(0, 10))

    # Empty placeholder methods to maintain compatibility
    def create_collapsible_log(self):
        """Placeholder method to maintain compatibility"""
        pass

    def toggle_log(self):
        """Placeholder method to maintain compatibility"""
        pass
        
    def update_log_display(self):
        """Placeholder method to maintain compatibility"""
        pass

if __name__ == "__main__":
    app = DocumentProcessorUI()
    app.mainloop() 