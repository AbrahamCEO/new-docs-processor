from docx import Document
import os
import logging
from docx.shared import Pt
from docx.oxml.ns import qn
from datetime import datetime
from docx.oxml import OxmlElement
import comtypes.client
from PyPDF2 import PdfMerger
import pikepdf
import shutil
import asyncio
import concurrent.futures
from operator import itemgetter
import sys

class DocumentProcessor:
    def __init__(self):
        self.logger = self.setup_logging()
        self.keywords_prompts = {
            "*ADD C&N*": "Client Name: ",
            "*ADD S&D*": "Project Name: ",
            "*ADD P&R*": "Procurement Reference No: ",
            "*ADD DD*": "Bid Closing Date: ",
            "*C&T*": "Closing Time: ",
            "*ADD P&B*": "P.O Box / Private Bag: ",
            "*ADD L*": "Delivery Address: ",
            "*ADD T*": "Town: ",
            "*ADD V&P*": "Price Validity: ",
            "*ADD S&R*": "Sales Representative: ",
        }
        # Update base paths for all document types
        self.base_paths = {
            'cover_letters': os.path.join(self.get_documents_path(), 'Cover Letters'),
            'resumes': os.path.join(self.get_documents_path(), 'Resumes'),
            'printable': os.path.join(self.get_documents_path(), 'Printable Documents')
        }
        self.extras_path = os.path.join(self.base_paths['cover_letters'], "Extras")
        self.max_workers = 4

    def get_documents_path(self):
        """Get the correct Documents path based on whether running as exe or script"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
            # Check if we're in the _internal directory structure
            if os.path.basename(base_dir) == '_internal':
                return os.path.join(base_dir, 'Documents')
            else:
                return os.path.join(base_dir, '_internal', 'Documents')
        else:
            # Running as script
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Documents')

    def setup_logging(self):
        """Set up logging configuration"""
        try:
            # Use a user-writeable location for logs
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                # Use %APPDATA% for logs when installed
                log_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'TwinRain Document Processor')
            else:
                # Running as script
                log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
                
            # Create logs directory if it doesn't exist
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'document_processor.log')
            
            # Configure logging
            logger = logging.getLogger('DocumentProcessor')
            logger.setLevel(logging.INFO)
            
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Create formatter and add to handlers
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Add handlers to logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
            # Log startup information
            logger.info("Document Processor initialized")
            logger.info(f"Log file: {log_file}")
            
            return logger
        except Exception as e:
            print(f"Error setting up logging: {str(e)}")
            # Fallback to basic logger that doesn't use files
            logger = logging.getLogger('DocumentProcessor')
            logger.setLevel(logging.INFO)
            
            # Only use console handler as fallback
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
            logger.warning(f"Using fallback logging due to error: {str(e)}")
            
            return logger

    def is_shape_locked(self, shape_element):
        """
        Check if a shape is locked.
        Supports both DrawingML shapes (w:drawing) and VML shapes (v:shape).
        """
        try:
            # Check for DrawingML shapes (typically used in footers)
            if shape_element.tag.endswith('drawing'):
                spPr = shape_element.find('.//a:spPr', {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                if spPr is not None:
                    protection = spPr.find('.//a:protection', {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                    if protection is not None:
                        is_protected = (
                            protection.get('noChangeAspect') == '1' or
                            protection.get('noMove') == '1' or
                            protection.get('noResize') == '1' or
                            protection.get('noEditPoints') == '1' or
                            protection.get('noRot') == '1'
                        )
                        if is_protected:
                            self.logger.info("Found protected DrawingML shape with locked properties")
                            return True
            # Check for VML shapes (commonly used in headers)
            if shape_element.tag.endswith('shape'):
                lock_elem = shape_element.find('.//{urn:schemas-microsoft-com:office:office}lock')
                if lock_elem is not None:
                    self.logger.info("Found protected VML shape with <o:lock>")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking shape protection: {str(e)}")
            return False

    def get_shapes_in_section(self, section):
        """
        Retrieve all shapes in a section (header/footer).
        This now includes both DrawingML shapes (w:drawing) and VML shapes (v:shape).
        """
        shapes = []
        try:
            if hasattr(section, 'header'):
                # DrawingML shapes in header
                header_drawing_shapes = section.header._element.findall(
                    './/w:drawing',
                    {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                )
                shapes.extend(header_drawing_shapes)
                # VML shapes in header
                header_vml_shapes = section.header._element.findall(
                    './/v:shape',
                    {'v': 'urn:schemas-microsoft-com:vml'}
                )
                shapes.extend(header_vml_shapes)
            if hasattr(section, 'footer'):
                # DrawingML shapes in footer
                footer_drawing_shapes = section.footer._element.findall(
                    './/w:drawing',
                    {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                )
                shapes.extend(footer_drawing_shapes)
                # VML shapes in footer
                footer_vml_shapes = section.footer._element.findall(
                    './/v:shape',
                    {'v': 'urn:schemas-microsoft-com:vml'}
                )
                shapes.extend(footer_vml_shapes)
        except Exception as e:
            self.logger.error(f"Error getting shapes: {str(e)}")
        return shapes

    def replace_text_preserve_format(self, paragraph, replacements, is_header_footer=False):
        """Replace text while preserving format."""
        try:
            for keyword, replacement in replacements.items():
                if keyword in paragraph.text:
                    for run in paragraph.runs:
                        if keyword in run.text:
                            # Store original formatting
                            original_format = {
                                'bold': run.bold,
                                'italic': run.italic,
                                'underline': run.underline,
                                'font_name': run.font.name,
                                'font_size': run.font.size,
                                'color': run.font.color.rgb if run.font.color else None,
                                'highlight_color': run.font.highlight_color
                            }
                            
                            # Replace text
                            run.text = run.text.replace(keyword, replacement)
                            
                            # Restore original formatting
                            run.bold = original_format['bold']
                            run.italic = original_format['italic']
                            run.underline = original_format['underline']
                            if original_format['font_name']:
                                run.font.name = original_format['font_name']
                            if original_format['font_size']:
                                run.font.size = original_format['font_size']
                            if original_format['color']:
                                run.font.color.rgb = original_format['color']
                            if original_format['highlight_color']:
                                run.font.highlight_color = original_format['highlight_color']
        except Exception as e:
            self.logger.error(f"Error during text replacement: {str(e)}")
            return

    def _apply_font_properties(self, run, font_properties):
        """Apply font properties to a run"""
        try:
            for prop, value in font_properties.items():
                if value is not None:
                    setattr(run.font, prop, value)
        except Exception as e:
            self.logger.error(f"Error applying font properties: {str(e)}")

    def check_shape_protection_status(self, section):
        """Check the protection status of shapes in a section."""
        shapes = self.get_shapes_in_section(section)
        protected_shapes = []
        unprotected_shapes = []
        for shape in shapes:
            if self.is_shape_locked(shape):
                protected_shapes.append(shape)
            else:
                unprotected_shapes.append(shape)
        if protected_shapes:
            self.logger.info(f"Found {len(protected_shapes)} protected shapes")
        if unprotected_shapes:
            self.logger.info(f"Found {len(unprotected_shapes)} unprotected shapes")
        return protected_shapes, unprotected_shapes

    def process_section(self, section, replacements):
        """Process headers and footers in a section."""
        # Process header
        if hasattr(section, 'header'):
            for paragraph in section.header.paragraphs:
                if any(keyword in paragraph.text for keyword in replacements.keys()):
                    self.logger.info("Found keywords in header")
                    self.replace_text_preserve_format(paragraph, replacements, is_header_footer=True)
            
            # Process header tables
            for table in section.header.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            if any(keyword in paragraph.text for keyword in replacements.keys()):
                                self.logger.info("Found keywords in header table")
                                self.replace_text_preserve_format(paragraph, replacements, is_header_footer=True)

        # Process footer
        if hasattr(section, 'footer'):
            for paragraph in section.footer.paragraphs:
                if any(keyword in paragraph.text for keyword in replacements.keys()):
                    self.logger.info("Found keywords in footer")
                    self.replace_text_preserve_format(paragraph, replacements, is_header_footer=True)
            
            # Process footer tables
            for table in section.footer.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            if any(keyword in paragraph.text for keyword in replacements.keys()):
                                self.logger.info("Found keywords in footer table")
                                self.replace_text_preserve_format(paragraph, replacements, is_header_footer=True)

    def lock_vml_shape(self, shape_element):
        """Lock a VML shape to prevent modifications."""
        try:
            lock_elem = shape_element.find('.//{urn:schemas-microsoft-com:office:office}lock')
            if lock_elem is None:
                lock_elem = OxmlElement('{urn:schemas-microsoft-com:office:office}lock')
                shape_element.append(lock_elem)
            # Set locking attributes – adjust these as needed
            lock_elem.set('rotation', 't')
            lock_elem.set('aspectratio', 't')
            lock_elem.set('move', 't')
            lock_elem.set('resize', 't')
            return True
        except Exception as e:
            self.logger.error(f"Error locking VML shape: {str(e)}")
        return False

    def lock_shape(self, shape_element):
        """
        Lock a shape to prevent modifications.
        Checks the shape type and calls the appropriate locking routine.
        """
        try:
            # If the shape is a VML shape (typically in headers), lock using VML method.
            if shape_element.tag.endswith('shape'):
                return self.lock_vml_shape(shape_element)
            else:
                # Otherwise, assume it's a DrawingML shape.
                spPr = shape_element.find('.//a:spPr', {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                if spPr is not None:
                    protection = spPr.find('.//a:protection', {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                    if protection is None:
                        protection = OxmlElement('a:protection')
                        spPr.append(protection)
                    protection.set('noChangeAspect', '1')
                    protection.set('noMove', '1')
                    protection.set('noResize', '1')
                    protection.set('noEditPoints', '1')
                    protection.set('noRot', '1')
                    return True
        except Exception as e:
            self.logger.error(f"Error locking shape: {str(e)}")
        return False

    def process_document(self, input_path, output_path, replacements):
        """Process a single document."""
        try:
            # Ensure input file exists
            if not os.path.exists(input_path):
                self.logger.error(f"Input file not found: {input_path}")
                return False

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            doc = Document(input_path)
            self.logger.info(f"Processing document: {os.path.basename(input_path)}")

            def replace_text_in_runs(paragraph, replacements):
                """Replace text in paragraph runs while preserving formatting"""
                for keyword, replacement in replacements.items():
                    if keyword in paragraph.text:
                        for run in paragraph.runs:
                            if keyword in run.text:
                                # Store original formatting
                                original_format = {
                                    'bold': run.bold,
                                    'italic': run.italic,
                                    'underline': run.underline,
                                    'font_name': run.font.name,
                                    'font_size': run.font.size,
                                    'color': run.font.color.rgb if run.font.color else None,
                                    'highlight_color': run.font.highlight_color
                                }
                                
                                # Replace text
                                run.text = run.text.replace(keyword, replacement)
                                
                                # Restore formatting
                                for attr, value in original_format.items():
                                    if value is not None:
                                        if attr == 'color':
                                            run.font.color.rgb = value
                                        elif attr.startswith('font_'):
                                            setattr(run.font, attr[5:], value)
                                        else:
                                            setattr(run, attr, value)

            def process_text_box(text_box, replacements):
                """Process text within a text box, including code blocks"""
                try:
                    # Process text directly in the text box
                    for text_elem in text_box.findall('.//w:t', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                        text = text_elem.text
                        if text:  # Check if text exists and is not None
                            for keyword, replacement in replacements.items():
                                if keyword in text:
                                    # Replace text
                                    text_elem.text = text.replace(keyword, replacement)
                                    self.logger.info(f"Replaced '{keyword}' with '{replacement}' in text box")
                    
                    # Process paragraphs in text box (for code blocks and other formatted text)
                    for paragraph in text_box.findall('.//w:p', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                        # Check if the entire paragraph contains any keywords
                        paragraph_text = ""
                        for run in paragraph.findall('.//w:r', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                            for t in run.findall('.//w:t', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                                if t.text:
                                    paragraph_text += t.text
                        
                        # If paragraph contains keywords, process each run
                        for keyword in replacements.keys():
                            if keyword in paragraph_text:
                                for run in paragraph.findall('.//w:r', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                                    for text_elem in run.findall('.//w:t', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                                        if text_elem.text and keyword in text_elem.text:
                                            # Store original formatting from the run
                                            rPr = run.find('.//w:rPr', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                                            
                                            # Replace text
                                            text_elem.text = text_elem.text.replace(keyword, replacements[keyword])
                                            self.logger.info(f"Replaced '{keyword}' with '{replacements[keyword]}' in formatted text box content")
                    
                    # Process tables within the text box
                    for table in text_box.findall('.//w:tbl', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                        for row in table.findall('.//w:tr', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                            for cell in row.findall('.//w:tc', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                                for paragraph in cell.findall('.//w:p', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                                    for run in paragraph.findall('.//w:r', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                                        text_elem = run.find('.//w:t', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                                        if text_elem is not None and text_elem.text:
                                            text = text_elem.text
                                            for keyword, replacement in replacements.items():
                                                if keyword in text:
                                                    # Replace text
                                                    text_elem.text = text.replace(keyword, replacement)
                                                    self.logger.info(f"Replaced '{keyword}' with '{replacement}' in text box table")
                except Exception as e:
                    self.logger.error(f"Error processing text box: {str(e)}")

            # Process main document
            for paragraph in doc.paragraphs:
                replace_text_in_runs(paragraph, replacements)

            # Process tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            replace_text_in_runs(paragraph, replacements)

            # Process text boxes
            for shape in doc.inline_shapes:
                if hasattr(shape, '_inline') and shape._inline.graphic.graphicData.find('.//w:txbx', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}) is not None:
                    text_box = shape._inline.graphic.graphicData.find('.//w:txbx', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                    process_text_box(text_box, replacements)

            # Process floating shapes (including text boxes)
            for shape in doc.part.inline_shapes:
                if hasattr(shape, '_element') and shape._element.find('.//w:txbx', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}) is not None:
                    text_box = shape._element.find('.//w:txbx', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                    process_text_box(text_box, replacements)

            # Process headers and footers
            for section in doc.sections:
                # Process headers
                for header in [section.header, section.first_page_header, section.even_page_header]:
                    if header:
                        for paragraph in header.paragraphs:
                            replace_text_in_runs(paragraph, replacements)
                        for table in header.tables:
                            for row in table.rows:
                                for cell in row.cells:
                                    for paragraph in cell.paragraphs:
                                        replace_text_in_runs(paragraph, replacements)
                        # Process text boxes in headers
                        for shape in header._element.findall('.//w:drawing', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                            text_box = shape.find('.//w:txbx', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                            if text_box is not None:
                                process_text_box(text_box, replacements)

                # Process footers
                for footer in [section.footer, section.first_page_footer, section.even_page_footer]:
                    if footer:
                        for paragraph in footer.paragraphs:
                            replace_text_in_runs(paragraph, replacements)
                        for table in footer.tables:
                            for row in table.rows:
                                for cell in row.cells:
                                    for paragraph in cell.paragraphs:
                                        replace_text_in_runs(paragraph, replacements)
                        # Process text boxes in footers
                        for shape in footer._element.findall('.//w:drawing', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
                            text_box = shape.find('.//w:txbx', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                            if text_box is not None:
                                process_text_box(text_box, replacements)

            # Save the document
            doc.save(output_path)
            self.logger.info(f"Successfully saved document: {os.path.basename(output_path)}")
            return True

        except Exception as e:
            self.logger.error(f"Error processing document {os.path.basename(input_path)}: {str(e)}")
            return False

    def convert_to_pdf(self, word_path, pdf_path):
        """Convert Word document to PDF"""
        try:
            if not os.path.exists(word_path):
                self.logger.error(f"Word file not found: {word_path}")
                return False

            word = comtypes.client.CreateObject('Word.Application')
            word.Visible = False
            
            try:
                doc = word.Documents.Open(word_path)
                doc.SaveAs(pdf_path, FileFormat=17)  # 17 = PDF format
                doc.Close()
                return True
            except Exception as e:
                self.logger.error(f"Error in PDF conversion: {str(e)}")
                return False
            finally:
                word.Quit()
        except Exception as e:
            self.logger.error(f"Error creating Word application: {str(e)}")
            return False

    def merge_pdfs(self, pdf_files, output_path):
        """Merge multiple PDFs into one"""
        try:
            # Verify all input files exist
            for pdf in pdf_files:
                if not os.path.exists(pdf):
                    self.logger.error(f"PDF file not found: {pdf}")
                    return False

            merger = PdfMerger()
            for pdf in pdf_files:
                merger.append(pdf)
            merger.write(output_path)
            merger.close()
            return True
        except Exception as e:
            self.logger.error(f"Error merging PDFs: {str(e)}")
            return False

    def compress_pdf(self, input_path, output_path):
        """Compress PDF file"""
        try:
            if not os.path.exists(input_path):
                self.logger.error(f"Input PDF not found: {input_path}")
                return False

            pdf = pikepdf.open(input_path)
            pdf.save(output_path, optimize=True)
            return True
        except Exception as e:
            self.logger.error(f"Error compressing PDF: {str(e)}")
            return False

    def format_date(self, date_str):
        """Convert date from any format to 'DD[suffix] Month YYYY' format with ordinal suffixes"""
        try:
            # First try to parse as YYYY-MM-DD
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                # If that fails, try DD/MM/YYYY format
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")

            # Get the day and determine the appropriate suffix
            day = date_obj.day
            if 10 <= day % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

            # Format the date with the suffix, full month name, and year
            # Ensure we get the complete month name and year
            formatted_date = f"{day}{suffix} {date_obj.strftime('%B')} {date_obj.year}"
            self.logger.info(f"Formatted date: {formatted_date}")
            return formatted_date
        except Exception as e:
            self.logger.error(f"Error formatting date: {str(e)}")
            return date_str

    def format_time(self, time_str):
        """Ensure time string includes AM/PM designation while keeping 24-hour format if provided"""
        try:
            time_str = time_str.strip()
            
            # Check if AM/PM is already included (case insensitive)
            if "am" in time_str.lower() or "pm" in time_str.lower():
                return time_str
                
            # Try to parse the time
            # For 24-hour format (e.g., "14:00"), keep the format but add AM/PM
            if ":" in time_str:
                parts = time_str.split(":")
                if len(parts) == 2:
                    try:
                        hour = int(parts[0])
                        # Determine AM/PM based on hour
                        if hour < 12:
                            return f"{time_str} AM"
                        else:
                            return f"{time_str} PM"
                    except ValueError:
                        pass
            
            # If we can't parse it as a time or it's already in the right format,
            # just add PM as default (most closing times are in the afternoon)
            if time_str and not time_str.lower().endswith('am') and not time_str.lower().endswith('pm'):
                time_str += " PM"
                
            self.logger.info(f"Formatted time: {time_str}")
            return time_str
        except Exception as e:
            self.logger.error(f"Error formatting time: {str(e)}")
            return time_str  # Return original if there's an error

    def get_doc_order(self, filename):
        """Extract the order number from filename (e.g., '1. Document.docx' -> 1)"""
        try:
            # Try to extract number from start of filename
            number = filename.split('.')[0]
            return int(number)
        except (ValueError, IndexError):
            # If no number found, return a large number to sort it last
            return float('inf')

    async def process_document_async(self, doc_info):
        """Async wrapper for document processing"""
        input_path, output_path, replacements = doc_info
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(
                pool, 
                self.process_document, 
                input_path, 
                output_path, 
                replacements
            )

    async def process_documents_async(self, docs_to_process):
        """Process multiple documents asynchronously"""
        tasks = []
        for doc_info in docs_to_process:
            task = asyncio.create_task(self.process_document_async(doc_info))
            tasks.append(task)
        return await asyncio.gather(*tasks)

    def process_documents(self, selected_folder=None, replacements=None, progress_callback=None):
        """Process documents based on selected folder"""
        try:
            # Set default folder to "Shitongeni" if none is specified
            if selected_folder is None:
                selected_folder = "Shitongeni"
            
            # Initialize empty replacements dict if none provided
            if replacements is None:
                replacements = {}

            # Format the date and time in replacements if they exist
            if "*ADD DD*" in replacements:
                replacements["*ADD DD*"] = self.format_date(replacements["*ADD DD*"])
            if "*C&T*" in replacements:
                replacements["*C&T*"] = self.format_time(replacements["*C&T*"])

            # Get the required information from replacements
            client_name = replacements.get("*ADD C&N*", "").strip()
            project_name = replacements.get("*ADD S&D*", "").strip()
            procurement_ref = replacements.get("*ADD P&R*", "").strip()
            
            # Validate required fields
            if not client_name:
                raise ValueError("Client name is required")
            if not procurement_ref:
                raise ValueError("Procurement reference is required")
            
            # Clean project name and procurement ref for folder names
            project_name = project_name.replace('/', '-').replace('\\', '-').strip()
            procurement_ref = procurement_ref.replace('/', '-').replace('\\', '-').strip()
            
            # Set up output directory using Desktop/RFQ Automation
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            rfq_automation_dir = os.path.join(desktop_path, 'RFQ Automation')
            client_dir = os.path.join(rfq_automation_dir, client_name)
            project_dir = os.path.join(client_dir, f"{project_name} ({procurement_ref})")
            
            # Create the directory if it doesn't exist
            os.makedirs(project_dir, exist_ok=True)
            self.logger.info(f"Created output directory: {project_dir}")

            # Initialize list to store all documents to process
            all_docs_to_process = []
            pdf_files = []

            # Process Cover Letters
            main_folder = os.path.join(self.base_paths['cover_letters'], selected_folder)
            cover_letter_docs = []
            for root, _, files in os.walk(main_folder):
                if "Extras" not in root:  # Skip extras folder
                    for file in files:
                        if file.endswith('.docx'):
                            order = self.get_doc_order(file)
                            cover_letter_docs.append((order, os.path.join(root, file)))
            
            # Process Resumes
            resume_folder = os.path.join(self.base_paths['resumes'], selected_folder)
            resume_docs = []
            if os.path.exists(resume_folder):
                for root, _, files in os.walk(resume_folder):
                    for file in files:
                        if file.endswith('.docx'):
                            order = self.get_doc_order(file)
                            resume_docs.append((order, os.path.join(root, file)))

            # Process Printable Documents
            printable_folder = os.path.join(self.base_paths['printable'])
            printable_docs = []
            if os.path.exists(printable_folder):
                for root, _, files in os.walk(printable_folder):
                    for file in files:
                        if file.endswith('.docx'):
                            order = self.get_doc_order(file)
                            printable_docs.append((order, os.path.join(root, file)))

            # Sort all document lists
            cover_letter_docs.sort(key=itemgetter(0))
            resume_docs.sort(key=itemgetter(0))
            printable_docs.sort(key=itemgetter(0))

            # Combine all documents in order: Cover Letters -> Resumes -> Printable Documents
            all_docs = [doc[1] for doc in cover_letter_docs + resume_docs + printable_docs]

            # Get extras documents
            extras_folder = os.path.join(self.extras_path, selected_folder)
            extras_docs = []
            if os.path.exists(extras_folder):
                for root, _, files in os.walk(extras_folder):
                    for file in files:
                        if file.endswith('.docx'):
                            order = self.get_doc_order(file)
                            extras_docs.append((order, os.path.join(root, file)))
            
            extras_docs.sort(key=itemgetter(0))
            extras_docs = [doc[1] for doc in extras_docs]

            total_files = len(all_docs) + len(extras_docs)
            processed_files = 0

            # Prepare all documents for processing
            for doc_path in all_docs:
                output_word = os.path.join(project_dir, os.path.basename(doc_path))
                all_docs_to_process.append((doc_path, output_word, replacements))

            # Process all documents asynchronously
            self.logger.info(f"Processing {len(all_docs)} documents...")
            asyncio.run(self.process_documents_async(all_docs_to_process))

            # Convert processed documents to PDF
            for doc_info in all_docs_to_process:
                _, output_word, _ = doc_info
                output_pdf = os.path.join(project_dir, 
                                      os.path.splitext(os.path.basename(output_word))[0] + '.pdf')
                if self.convert_to_pdf(output_word, output_pdf):
                    pdf_files.append(output_pdf)
                    self.logger.info(f"Created PDF: {output_pdf}")
                else:
                    self.logger.error(f"Failed to create PDF for {output_word}")
                try:
                    os.remove(output_word)
                    self.logger.info(f"Removed intermediate Word file: {output_word}")
                except Exception as e:
                    self.logger.error(f"Error removing Word file: {str(e)}")
                processed_files += 1
                if progress_callback:
                    progress_callback(processed_files, total_files, output_pdf)

            # Merge and compress PDFs
            final_pdf = None
            if pdf_files:
                self.logger.info(f"Merging {len(pdf_files)} PDFs...")
                
                try:
                    # Step 1: Merge PDFs
                    merger = PdfMerger()
                    for pdf in pdf_files:
                        merger.append(pdf)
                    
                    # Create temporary merged PDF
                    temp_merged_path = os.path.join(project_dir, 'temp_merged.pdf')
                    merger.write(temp_merged_path)
                    merger.close()
                    
                    # Step 2: Compress the merged PDF to final location
                    final_pdf_path = os.path.join(project_dir, f'{project_name} ({procurement_ref}).pdf')
                    with pikepdf.open(temp_merged_path) as pdf:
                        pdf.save(final_pdf_path,
                               compress_streams=True,
                               preserve_pdfa=True,
                               object_stream_mode=pikepdf.ObjectStreamMode.generate)
                    
                    # Verify the final PDF exists before cleaning up
                    if os.path.exists(final_pdf_path):
                        final_pdf = final_pdf_path
                        self.logger.info(f"Successfully created final PDF: {final_pdf_path}")
                        
                        # Only clean up intermediate files after confirming final PDF exists
                        self.logger.info("Cleaning up intermediate files...")
                        # Remove individual PDFs
                        for pdf_file in pdf_files:
                            if os.path.exists(pdf_file):
                                os.remove(pdf_file)
                                self.logger.info(f"Removed intermediate PDF: {pdf_file}")
                        
                        # Remove temporary merged file
                        if os.path.exists(temp_merged_path):
                            os.remove(temp_merged_path)
                            self.logger.info("Removed temporary merged PDF")
                    else:
                        self.logger.error("Final PDF was not created successfully")
                        final_pdf = None
                    
                except Exception as e:
                    self.logger.error(f"Error in PDF processing: {str(e)}")
                    final_pdf = None
                    # Clean up only intermediate files in case of error, not the final PDF
                    for path in [*pdf_files, temp_merged_path]:
                        if os.path.exists(path):
                            os.remove(path)
                            self.logger.info(f"Cleaned up intermediate file after error: {path}")

            return {
                'total': total_files,
                'output_directory': project_dir,
                'final_pdf': final_pdf
            }

        except Exception as e:
            self.logger.error(f"Error in batch processing: {str(e)}")
            return None
