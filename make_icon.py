from pathlib import Path
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

app = QGuiApplication.instance() or QGuiApplication([])

root = Path(__file__).resolve().parent / 'assets'
svg_symbol = root / 'transpro.svg'
png_file = root / 'transpro.png'
ico_file = root / 'transpro.ico'

# Modern squircle app tile SVG for Windows desktop, installer, and taskbar
# Ensures high contrast on light, dark, and photo wallpapers
svg_tile = '''<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <defs>
    <mask id="tile-mask">
      <rect width="256" height="256" fill="white"/>
      <polygon points="15,178 85,131 85,148 27,187" fill="black"/>
      <polygon points="148,84 175,64 175,108 148,128" fill="black"/>
    </mask>
  </defs>
  <!-- Modern dark app squircle -->
  <rect width="256" height="256" rx="56" fill="#121619" stroke="#252e35" stroke-width="2"/>
  <g transform="translate(128, 128) scale(0.95) translate(-124, -130)">
    <g fill="none" stroke="#ffffff" stroke-width="9.6" stroke-linecap="round" stroke-linejoin="round">
      <rect x="28.5" y="64.5" width="132" height="136" rx="20" mask="url(#tile-mask)"/>
      <path d="M 28.5 186 L 82 148" mask="url(#tile-mask)"/>
      <path d="M 98.5 178 L 98.5 137 A 9 9 0 0 0 89.5 128 L 63 128 A 7.5 7.5 0 0 1 63 113 L 138 113 Q 150 113 159 105 L 197 71.5" stroke-linecap="round"/>
    </g>
    <circle cx="214.5" cy="63.5" r="9.2" fill="#41e7f6"/>
  </g>
</svg>'''

def render_svg_at_size(svg_content, size):
    renderer = QSvgRenderer(svg_content.encode('utf-8'))
    qimg = QImage(size, size, QImage.Format_ARGB32)
    qimg.fill(Qt.transparent)
    painter = QPainter(qimg)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    renderer.render(painter)
    painter.end()
    ptr = qimg.bits()
    arr = np.frombuffer(ptr, np.uint8).reshape((size, size, 4))
    rgb = arr[..., [2, 1, 0, 3]]
    return Image.fromarray(rgb)

sizes = [16, 24, 32, 48, 64, 128, 256]
images = [render_svg_at_size(svg_tile, s) for s in sizes]

# Save 256x256 PNG
images[-1].save(str(png_file))

# Save multi-resolution Windows ICO with vector-rasterized frames
img_256 = images[-1]
other_images = images[:-1]
img_256.save(str(ico_file), format='ICO', append_images=other_images)

# Also generate transparent icon variant
trans_images = [render_svg_at_size(svg_symbol.read_text(encoding='utf-8'), s) for s in sizes]
trans_images[-1].save(str(root / 'tracer-transparent.png'))
trans_images[-1].save(str(root / 'tracer-transparent.ico'), format='ICO', append_images=trans_images[:-1])

print(f'Successfully generated {png_file.name}, {ico_file.name}, and transparent variants ({", ".join(f"{s}px" for s in sizes)}).')
