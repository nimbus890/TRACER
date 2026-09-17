# Third-party components

TransPro uses open-source Whisper model weights through faster-whisper / CTranslate2 (MIT licensed projects), OpenCV Zoo's NanoDet visual-search model and reference design (Apache 2.0), PySide6 / Qt (LGPL/GPL/commercial licensing), PyAV / FFmpeg, Pillow, NumPy, ONNX Runtime, Hugging Face Hub, Tokenizers, and the NVIDIA CUDA/cuDNN runtime libraries. NVIDIA components are subject to NVIDIA's distribution terms and are not open source.

The standalone distribution includes component license files under `licenses`. Libraries remain separate in `_internal`; the application is not statically linked to Qt. Application source and build instructions are supplied with this project. Consult individual license files before redistribution, especially for Qt/FFmpeg/NVIDIA components.

Whisper: https://github.com/openai/whisper
faster-whisper: https://github.com/SYSTRAN/faster-whisper
CTranslate2: https://github.com/OpenNMT/CTranslate2
PySide6 / Qt: https://www.qt.io/licensing/
PyAV: https://github.com/PyAV-Org/PyAV
FFmpeg: https://ffmpeg.org/legal.html
NVIDIA CUDA: https://docs.nvidia.com/cuda/eula/index.html
NVIDIA cuDNN: https://docs.nvidia.com/deeplearning/cudnn/backend/latest/reference/eula.html
OpenCV Zoo / NanoDet: https://huggingface.co/opencv/opencv_zoo/tree/main/models/object_detection_nanodet
