# TwinRain Document Processor - Installer Guide

This guide explains how to build an installer for the TwinRain Document Processor application.

## Prerequisites

Before building the installer, ensure you have the following installed:

1. **Python 3.7+** - The application and build scripts require Python 3.7 or higher.

2. **Required Python packages**:
   ```
   pip install pyinstaller pillow customtkinter tkcalendar
   ```

3. **NSIS (Nullsoft Scriptable Install System)** - Required to build the installer
   - Download from: https://nsis.sourceforge.io/Download
   - Install using the default options

## File Structure

The installer build process relies on the following files:

- `doc_processor.py` - The main document processing logic
- `doc_processor_ui.py` - The user interface code
- `build_installer.py` - The main script to build the installer
- `png_to_ico.py` - Utility to convert the logo to ICO format
- `document_processor.spec` - PyInstaller specification file
- `installer.nsi` - NSIS installer script

Make sure your project includes the following directories:
- `public/assets/` - Contains the application logo (`twinrain-logo.png`)
- `Documents/Cover Letters/` - Contains document templates
- `Documents/Printable Documents/` - Contains printable documents
- `Documents/Resumes/` - Contains resume templates

## Building the Installer

Follow these steps to build the installer:

1. **Prepare your environment**
   - Ensure all required packages are installed
   - Make sure NSIS is installed and visible in the system PATH

2. **Run the build installer script**
   ```
   python build_installer.py
   ```

3. **The build process will**:
   - Check for all required prerequisites
   - Convert the PNG logo to ICO format for the application icon
   - Check for NSIS installation
   - Build the executable using PyInstaller
   - Build the installer using NSIS

4. **Once complete, you'll find**:
   - The installer EXE: `TwinRain_Document_Processor_Setup.exe`
   - The built application in the `dist/TwinRain Document Processor/` directory

## Distributing the Installer

To distribute the installer:

1. Copy the `TwinRain_Document_Processor_Setup.exe` file to your distribution medium (USB, network share, etc.)
2. Users can install by double-clicking the installer and following the prompts
3. The installer will:
   - Install the application to the user's Programs directory
   - Create Start Menu shortcuts
   - Create a Desktop shortcut
   - Register the application in Add/Remove Programs

## Customizing the Installer

If you need to customize the installer:

- **Application Name/Version**: Edit the variables at the top of `installer.nsi`
- **Installation Directory**: Modify the `InstallDir` parameter in `installer.nsi`
- **Included Files**: Update the `datas` section in `document_processor.spec`
- **Icon**: Replace the logo file at `public/assets/twinrain-logo.png`

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

3. **Missing files in the installer**:
   - Check the `datas` section in the spec file
   - Ensure all required folders are included

4. **Icon conversion errors**:
   - Ensure the Pillow library is installed
   - Check if the logo file exists and is a valid PNG

## Support

For any issues or questions regarding the installer, please contact the TwinRain support team. 