# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Define the base directory
base_dir = os.path.abspath('.')

# Define the public/assets directory for icons
assets_dir = os.path.join(base_dir, 'public', 'assets')

# Define the Documents directory for cover letters, etc.
docs_dir = os.path.join(base_dir, 'Documents')

# Ensure directories exist or create them
os.makedirs(assets_dir, exist_ok=True)
os.makedirs(os.path.join(docs_dir, 'Cover Letters', 'Shitongeni'), exist_ok=True)
os.makedirs(os.path.join(docs_dir, 'Cover Letters', 'Wilson'), exist_ok=True)
os.makedirs(os.path.join(docs_dir, 'Cover Letters', 'Extras', 'Shitongeni'), exist_ok=True)
os.makedirs(os.path.join(docs_dir, 'Cover Letters', 'Extras', 'Wilson'), exist_ok=True)
os.makedirs(os.path.join(docs_dir, 'Printable Documents'), exist_ok=True)
os.makedirs(os.path.join(docs_dir, 'Resumes'), exist_ok=True)

# Create placeholder logo if needed
logo_path = os.path.join(assets_dir, 'twinrain-logo.png')
if not os.path.exists(logo_path):
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (256, 256), color=(30, 83, 141))  # Using TwinRain blue color
        d = ImageDraw.Draw(img)
        d.text((85, 120), "TwinRain", fill=(255, 255, 255))
        img.save(logo_path)
        print(f"Created placeholder logo at {logo_path}")
    except Exception as e:
        print(f"Failed to create placeholder logo: {e}")

a = Analysis(
    ['doc_processor_ui.py'],
    pathex=[base_dir],
    binaries=[],
    datas=[
        # Include assets (logo, etc.)
        (assets_dir, os.path.join('public', 'assets')),
        # Include Documents folder structure
        (docs_dir, 'Documents'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'babel.numbers',
        'tkinter',
        'tkinter.ttk',
        'tkcalendar',
        'customtkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TwinRain Document Processor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(assets_dir, 'Logo.ico') if os.path.exists(os.path.join(assets_dir, 'Logo.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TwinRain Document Processor',
) 