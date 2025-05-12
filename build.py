import os
import subprocess
import shutil
import sys

def build_executable():
    print("Building TwinRain Document Processor executable...")
    
    # Clean previous build if exists
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Run PyInstaller using the spec file using Python's module system
    # This is more reliable than relying on the pyinstaller command being in PATH
    result = subprocess.run([sys.executable, "-m", "PyInstaller", "document_processor.spec"], 
                           capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error building executable:")
        print(result.stderr)
        return False
    
    print("Executable built successfully!")
    print(f"Output directory: {os.path.abspath('dist/TwinRain Document Processor')}")
    return True

if __name__ == "__main__":
    build_executable() 