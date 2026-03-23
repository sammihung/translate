# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/qwen_asr_app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include config files
        ('.env.example', '.'),
        ('src/qwen_asr_app/config', 'qwen_asr_app/config'),
        # Silero VAD model files (Windows paths)
        ('.venv\\Lib\\site-packages\\silero_vad\\data', 'silero_vad\\data'),
    ],
    hiddenimports=[
        # PyAudio
        'pyaudio',
        # CustomTkinter
        'customtkinter',
        'customtkinter.windows',
        'customtkinter.windows.widgets',
        # Torch vision
        'torchvision',
        # ONNX Runtime
        'onnxruntime',
        # Silero VAD
        'silero_vad',
        # Pyannote (optional)
        'pyannote.audio',
        # BitsAndBytes
        'bitsandbytes',
        # Accelerate
        'accelerate',
        # Librosa
        'librosa',
        'soundfile',
        # Pydantic
        'pydantic',
        'pydantic_settings',
        # Qwen ASR
        'qwen_asr',
        # Additional hidden imports
        'numpy',
        'scipy',
        'sklearn',
        'pandas',
        # SciPy submodules (required for PyInstaller)
        'scipy._cyutility',
        'scipy._lib._ccallback_c',
        'scipy.special._ufuncs',
        'scipy.linalg._fblas',
        'scipy.sparse.csgraph._tools',
        'scipy.sparse.csgraph._shortest_path',
        'scipy.sparse.csgraph._min_spanning_tree',
        'scipy.sparse.csgraph._flow',
        'scipy.sparse.csgraph._matching',
        'scipy.sparse.csgraph._reordering',
        'scipy.sparse._csparsetools',
        'scipy.sparse._sparsetools',
        'scipy.ndimage._nd_image',
        'scipy.ndimage._ni_support',
        'scipy.signal._sigtools',
        'scipy.signal._max_len_seq_inner',
        'scipy.signal._upfirdn_apply',
        'scipy.signal._sosfilt',
        'scipy.optimize._minpack',
        'scipy.optimize._lsq.givens_elimination',
        'scipy.optimize._zeros',
        'scipy.optimize._cython_nn',
        'scipy.stats._stats',
        'scipy.stats._statlib',
        'scipy.stats._mvn',
        'scipy.stats._rcont.rcont',
        'scipy.special.cython_special',
        'scipy.integrate._odepack',
        'scipy.integrate._quadpack',
        'scipy.integrate._vode',
        'scipy.integrate._dop',
        'scipy.integrate._lsoda',
        'scipy.fftpack.convolve',
        # scikit-learn submodules
        'sklearn.utils._cython_blas',
        'sklearn.utils._openmp_helpers',
        'sklearn.utils.murmurhash',
        'sklearn.utils._sorting',
        'sklearn.utils._vector_sentinel',
        'sklearn.utils._typedefs',
        'sklearn.utils._fast_dict',
        'sklearn.utils._array_api',
        'sklearn.metrics._dist_metrics',
        'sklearn.metrics._classification',
        'sklearn.tree._utils',
        'sklearn.tree._tree',
        'sklearn.tree._criterion',
        'sklearn.tree._splitter',
        # Numba
        'numba',
        'numba.core',
        'numba.np.ufunc.tbbpool',
    ],
    collect_submodules=[],
    collect_all=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'notebook',
        'jupyter',
        'ipython',
        'test',
        'tests',
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
    [],
    exclude_binaries=True,
    name='QwenASR Translate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI-only (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here: icon='assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QwenASR Translate',
)
