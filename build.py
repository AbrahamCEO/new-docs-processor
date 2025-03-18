import os
import subprocess

def build_exe():
    command = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--name', 'DocReplacer',
        'doc_replacer.py'
    ]
    
    subprocess.run(command)

if __name__ == "__main__":
    build_exe() 