from pathlib import Path
import pefile

root = Path(__file__).parent / 'diagnostic' / 'TransPro' / '_internal'
dirs = [root, root / 'PySide6', root / 'shiboken6', Path('C:/Windows/System32')]
cache = {}
for filename in [root / 'PySide6' / 'QtCore.pyd', root / 'PySide6' / 'pyside6.abi3.dll', root / 'PySide6' / 'Qt6Core.dll', root / 'shiboken6' / 'shiboken6.abi3.dll']:
    print('\nFILE', filename.name)
    pe = pefile.PE(str(filename))
    for dep in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
        name = dep.dll.decode()
        if name.lower().startswith(('api-ms-', 'ext-ms-')):
            continue
        candidates = [p / name for p in dirs if (p / name).exists()]
        if not candidates:
            print('MISSING DLL', name)
            continue
        target = candidates[0]
        if str(target) not in cache:
            target_pe = pefile.PE(str(target))
            cache[str(target)] = {e.name for e in getattr(target_pe, 'DIRECTORY_ENTRY_EXPORT', type('X', (), {'symbols': []})).symbols}
        for symbol in dep.imports:
            if symbol.name and symbol.name not in cache[str(target)]:
                print('MISSING SYMBOL', name, symbol.name.decode(), 'in', target)
