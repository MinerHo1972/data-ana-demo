# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_forecast_ui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sales_4g_byweek.xlsx', '.'),
        ('UI使用说明.md', '.'),
        ('README.md', '.'),
        ('启动预测系统.bat', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'pandas',
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'seaborn',
        'datetime',
        'threading',
        'warnings',
        'openpyxl',
        're',
        'os',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 深度学习框架
        'torch',
        'tensorflow',
        'keras',
        'transformers',
        'datasets',
        'tokenizers',
        'accelerate',
        'diffusers',
        'timm',

        # 图像处理
        'cv2',
        'opencv-python',
        'scikit-image',
        'PIL._imagingtk',

        # Web框架
        'django',
        'flask',
        'fastapi',

        # 数据库
        'sqlalchemy',
        'psycopg2',
        'pymongo',
        'redis',

        # 云服务
        'boto3',
        'botocore',
        's3transfer',

        # 开发工具
        'jupyter',
        'notebook',
        'IPython',
        'pytest',
        'black',
        'flake8',
        'mypy',

        # 其他不需要的大型库
        'bokeh',
        'plotly',
        'dash',
        'streamlit',
        'panel',
        'holoviews',
        'datashader',
        'xarray',
        'dask',
        'distributed',
    ],
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
    name='4G销售数据预测系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version='version_info.txt'
)