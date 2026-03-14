# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'paramiko',
        'paramiko.transport',
        'paramiko.auth_handler',
        'paramiko.sftp_client',
        'paramiko.sftp_attr',
        'cryptography',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.primitives.asymmetric.rsa',
        'cryptography.hazmat.primitives.asymmetric.ed25519',
        'bcrypt',
        'nacl',
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScpGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No terminal window on Windows/macOS
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows icon (create your own .ico)
    # icon='assets/icon.ico',
)

# macOS .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='ScpGUI.app',
        # icon='assets/icon.icns',
        bundle_identifier='com.scpgui.app',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHumanReadableCopyright': 'MIT License',
        },
    )
