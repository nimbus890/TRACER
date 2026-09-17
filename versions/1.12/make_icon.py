from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PIL import Image

root = Path(__file__).resolve().parent / 'assets'
image = QImage(256, 256, QImage.Format_ARGB32)
image.fill(Qt.transparent)
painter = QPainter(image)
QSvgRenderer(str(root / 'transpro.svg')).render(painter)
painter.end()
image.save(str(root / 'transpro.png'))
Image.open(root / 'transpro.png').save(root / 'transpro.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
