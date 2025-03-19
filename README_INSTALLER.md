# TwinRain Document Processor - Installer Guide

This guide explains how to build an installer for the TwinRain Document Processor application.

## Prerequisites

Before building the installer, ensure you have the following installed:

1. **Python 3.7+** - The application and build scripts require Python 3.7 or higher.

2. **Required Python packages**:
   ```
   pip install pyinstaller pillow customtkinter tkcalendar babel
   ```

3. **NSIS (Nullsoft Scriptable Install System)** - Required to build the installer
   - Download from: https://nsis.sourceforge.io/Download
   - Install using the default options

## File Structure

The installer build process relies on the following files:

- `doc_processor.py` - The main document processing logic
- `doc_processor_ui.py` - The user interface code
- `build.py` - Script to build the executable
- `build_installer.py` - The main script to build the installer
- `png_to_ico.py` - Utility to convert the logo to ICO format
- `document_processor.spec` - PyInstaller specification file
- `installer.nsi` - NSIS installer script

The following directory structure will be created automatically if it doesn't exist:
```
/
├── public/
│   └── assets/
│       ├── twinrain-logo.png
│       └── twinrain-logo.ico
└── Documents/
    ├── Cover Letters/
    │   ├── Shitongeni/
    │   ├── Wilson/
    │   └── Extras/
    │       ├── Shitongeni/
    │       └── Wilson/
    ├── Printable Documents/
    └── Resumes/
```

## Building the Installer

Follow these steps to build the installer:

1. **Prepare your environment**
   - Ensure all required packages are installed
   - Make sure NSIS is installed and in your system PATH
   - Place any required document templates in the appropriate folders

2. **Run the build installer script**
   ```
   python build_installer.py
   ```

3. **The build process will**:
   - Check for all required prerequisites
   - Create the necessary directory structure
   - Convert the logo to ICO format for the application icon
   - Check for NSIS installation
   - Build the executable using PyInstaller
   - Build the installer using NSIS

4. **Once complete, you'll find**:
   - The installer EXE: `TwinRain_Document_Processor_Setup.exe`
   - The built application in the `dist/TwinRain Document Processor/` directory

## Directory Structure and Permissions

When installed, the application will use the following directory structure:

1. **Application Files**:
   - Installed to `C:\Program Files (x86)\TwinRain Document Processor\` (or similar)
   - Read-only, contains the executable and required files

2. **User Data and Logs**:
   - Stored in `%APPDATA%\TwinRain Document Processor\`
   - Contains application logs and user-specific settings
   - User has full write permissions to this location

3. **Output Documents**:
   - Generated in `Desktop\RFQ Automation\Client Name\Project Name (Procurement Reference)\`
   - User has full write permissions to this location
   - Automatically created during installation and document processing

## Distributing the Installer

To distribute the installer:

1. Copy the `TwinRain_Document_Processor_Setup.exe` file to your distribution medium (USB, network share, etc.)
2. Users can install by double-clicking the installer and following the prompts
3. The installer will:
   - Install the application to the user's Programs directory
   - Create Start Menu shortcuts
   - Create a Desktop shortcut
   - Create necessary folders with appropriate permissions
   - Register the application in Add/Remove Programs

## Fixing Path Issues

The application now uses relative paths instead of absolute paths, which means:

1. It will work on any computer regardless of username or installation location
2. The application automatically finds resources relative to its installation location
3. If files are missing, the application creates placeholder resources
4. Log files are stored in user-writeable locations to avoid permission issues
5. Error handling is improved to prevent crashes due to missing files or permissions

## Troubleshooting

If you encounter issues during the build process:

1. **PyInstaller errors**:
   - Check that all required Python packages are installed
   - Ensure the spec file is correctly configured
   - Check for missing imports in your application

2. **NSIS errors**:
   - Verify NSIS is correctly installed
   - Check the `installer.nsi` file for syntax errors
   - Ensure all paths are correct

3. **Permission errors after installation**:
   - Check if the application is being launched with administrator privileges
   - Verify that the installer created the necessary folders in %APPDATA% and Desktop
   - Make sure the user has write permissions to these locations

## Running the Application After Installation

After installation:

1. Launch the application from the Start Menu or Desktop shortcut
2. The application will automatically create any required folders if they don't exist
3. Log files will be stored in `%APPDATA%\TwinRain Document Processor\logs\`
4. Output documents will be stored in `Desktop\RFQ Automation\`
5. If the logo is missing, a placeholder text logo will be displayed

## Contact

For any issues or questions regarding the installer, please contact the TwinRain support team. 