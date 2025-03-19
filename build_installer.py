import os
import subprocess
import sys
import shutil
from png_to_ico import png_to_ico
from build import build_executable

def check_nsis_installed():
    """Check if NSIS is installed"""
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe"
    ]
    
    for path in nsis_paths:
        if os.path.exists(path):
            return path
    
    return None

def create_app_icon():
    """Convert PNG logo to ICO format for application icon"""
    print("\nConverting logo to ICO format...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(base_dir, 'public', 'assets', 'twinrain-logo.png')
    ico_path = os.path.join(base_dir, 'public', 'assets', 'twinrain-logo.ico')
    
    # Ensure assets directory exists
    assets_dir = os.path.dirname(ico_path)
    os.makedirs(assets_dir, exist_ok=True)
    
    if not os.path.exists(png_path):
        print(f"Error: Logo file not found at {png_path}")
        print("Creating placeholder logo...")
        
        # Create assets directory if it doesn't exist
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
        
        # Create a simple placeholder image
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (256, 256), color=(30, 83, 141))  # Using TwinRain blue color
        d = ImageDraw.Draw(img)
        d.text((85, 120), "TwinRain", fill=(255, 255, 255))
        img.save(png_path)
        
    if png_to_ico(png_path, ico_path):
        print(f"Successfully created icon at {ico_path}")
        return True
    else:
        print("Failed to create icon")
        return False

def build_installer(nsis_path):
    """Build the installer using NSIS"""
    print("\nBuilding installer...")
    
    try:
        result = subprocess.run([nsis_path, "installer.nsi"], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Error building installer:")
            print(result.stderr)
            return False
        
        # Verify installer was created
        installer_path = os.path.abspath("TwinRain_Document_Processor_Setup.exe")
        if not os.path.exists(installer_path):
            print("Installer file not found. Build may have failed.")
            return False
            
        print(f"Installer built successfully at: {installer_path}")
        return True
    except Exception as e:
        print(f"Error executing NSIS: {str(e)}")
        return False

def check_prerequisites():
    """Check if all prerequisites are installed"""
    prerequisites = {
        "pyinstaller": False,
        "pillow": False,
        "customtkinter": False,
        "tkcalendar": False
    }
    
    try:
        # Check PyInstaller
        import PyInstaller
        prerequisites["pyinstaller"] = True
    except ImportError:
        pass
        
    try:
        # Check Pillow
        import PIL
        prerequisites["pillow"] = True
    except ImportError:
        pass
        
    try:
        # Check customtkinter
        import customtkinter
        prerequisites["customtkinter"] = True
    except ImportError:
        pass
        
    try:
        # Check tkcalendar
        import tkcalendar
        prerequisites["tkcalendar"] = True
    except ImportError:
        pass
    
    missing = [pkg for pkg, installed in prerequisites.items() if not installed]
    if missing:
        print("Missing required packages:")
        for pkg in missing:
            print(f"- {pkg}")
        print("\nPlease install missing packages with:")
        print(f"pip install {' '.join(missing)}")
        return False
        
    return True

def ensure_directory_structure():
    """Ensure necessary directory structure exists"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define key directories
    assets_dir = os.path.join(base_dir, 'public', 'assets')
    docs_dir = os.path.join(base_dir, 'Documents')
    
    # Create required directories
    dirs_to_create = [
        assets_dir,
        os.path.join(docs_dir, 'Cover Letters', 'Shitongeni'),
        os.path.join(docs_dir, 'Cover Letters', 'Wilson'),
        os.path.join(docs_dir, 'Cover Letters', 'Extras', 'Shitongeni'),
        os.path.join(docs_dir, 'Cover Letters', 'Extras', 'Wilson'),
        os.path.join(docs_dir, 'Printable Documents'),
        os.path.join(docs_dir, 'Resumes')
    ]
    
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")
            except Exception as e:
                print(f"Error creating directory {dir_path}: {str(e)}")
                return False
    
    return True

def main():
    """Main function to build installer"""
    print("=" * 60)
    print("    TwinRain Document Processor Installer Builder")
    print("=" * 60)
    
    # Step 1: Check prerequisites
    print("\nStep 1: Checking prerequisites...")
    if not check_prerequisites():
        print("Prerequisite check failed. Please install missing packages.")
        return False
    
    # Step 2: Ensure directory structure
    print("\nStep 2: Ensuring directory structure...")
    if not ensure_directory_structure():
        print("Failed to create required directories. Please check permissions.")
        return False
    
    # Step 3: Create app icon
    print("\nStep 3: Creating application icon...")
    if not create_app_icon():
        print("Warning: Failed to create application icon. Continuing anyway...")
    
    # Step 4: Check if NSIS is installed
    print("\nStep 4: Checking for NSIS installation...")
    nsis_path = check_nsis_installed()
    
    if not nsis_path:
        print("NSIS not found. Please install NSIS from https://nsis.sourceforge.io/Download")
        print("After installing NSIS, run this script again.")
        return False
    
    print(f"NSIS found at: {nsis_path}")
    
    # Step 5: Build the executable
    print("\nStep 5: Building executable...")
    if not build_executable():
        print("Failed to build executable. Aborting.")
        return False
    
    # Step 6: Build the installer
    print("\nStep 6: Building installer...")
    if not build_installer(nsis_path):
        print("Failed to build installer.")
        return False
    
    print("\n" + "=" * 60)
    print("    Build Completed Successfully!")
    print("=" * 60)
    
    installer_path = os.path.abspath("TwinRain_Document_Processor_Setup.exe")
    print(f"\nInstaller created at: {installer_path}")
    print("\nTo install the application:")
    print("1. Run the installer executable")
    print("2. Follow the installation wizard")
    print("3. Launch the application from the Start Menu or Desktop shortcut")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 