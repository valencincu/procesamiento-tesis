import warnings
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scienceplots
from matplotlib import use as matplotlib_backend
from openpiv import validation
from tqdm import tqdm

from pyaux.output_config import create_output_directory, write_analysis_notes
from pydata.roi import ROI
from pydata.video import Video
from pypiv.algorithms import generate_background
from pypiv.runner import PIVRunner
from pypiv.settings import WindefPIVSettings

matplotlib_backend("TkAgg")
plt.style.use('science')

# --------------------------------------------------------------------------
# CONSTANTS
# --------------------------------------------------------------------------

DEFAULT_STEP = 4
BACKGROUND_AVERAGE_STEP = 10

CONTRAST_STRETCH_LOWER = 60
CONTRAST_STRETCH_UPPER = 99

PIV_INTERVAL = 6
PIV_WINDOW_SIZES = (64, 32)
PIV_OVERLAPS = (32, 16)
PIV_SIG2NOISE_THRESHOLD = 1.2

FILTER_SCALE = 0.1
FILTER_NEIGHBORHOOD = 2

SMOOTHN: bool = True

CALIBRATION_FACTOR = 1/3927.3

# --------------------------------------------------------------------------
# SELECT VIDEO
# --------------------------------------------------------------------------

video = Video()

# --------------------------------------------------------------------------
# PREPROCESS
# --------------------------------------------------------------------------

first_frame = video[0]
roi = ROI(first_frame, select=True).square()
background = generate_background(video, step=BACKGROUND_AVERAGE_STEP)

def preprocess_func(image):
    processed_image = image.astype(np.float32) - background
    processed_image = processed_image.cropped(roi=roi)
    processed_image = processed_image.inverted().normalized()
    processed_image = processed_image.contrast_stretch(
        lower_limit=CONTRAST_STRETCH_LOWER,
        upper_limit=CONTRAST_STRETCH_UPPER
    )
    return processed_image

video.preprocess = preprocess_func

# --------------------------------------------------------------------------
# VELOCITY FIELD FILTER FUNCTION
# --------------------------------------------------------------------------

def validation_func(u, v, s2n):
    flags = validation.sig2noise_val(s2n, threshold=PIV_SIG2NOISE_THRESHOLD)
    u = np.where(flags, np.nan, u)
    v = np.where(flags, np.nan, v)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        flags |= validation.local_norm_median_val(u, v, FILTER_SCALE, FILTER_NEIGHBORHOOD)
    return flags

# --------------------------------------------------------------------------
# PIV CONFIGURATION
# --------------------------------------------------------------------------

settings = WindefPIVSettings(
    window_sizes=PIV_WINDOW_SIZES,
    overlaps=PIV_OVERLAPS,
    validation_function=validation_func,
    use_smoothn=SMOOTHN,
)

piv = PIVRunner(
    video=video,
    settings=settings,
    fps=video.fps,
    interval=PIV_INTERVAL,
    calibration_factor=CALIBRATION_FACTOR
)

# --------------------------------------------------------------------------
# SAVE CONFIG
# --------------------------------------------------------------------------

script_path  = Path(__file__).resolve()
date_tag = datetime.now().strftime("%Y_%m_%d")
output_root = script_path.parent / "postprocessing" / "data" / "piv" / date_tag
save_dir, notes_path = create_output_directory(video, video.directory_path, output_root)

path_dictionary: dict[str, str] = {
    "video_path": str(video.directory_path.resolve()),
    "script_path": str(Path(__file__).resolve()),
}
write_analysis_notes(notes_path, path_dictionary, {'roi': roi, 'original_fps': video.fps, 'step': DEFAULT_STEP}, extra=settings.__repr__())

# --------------------------------------------------------------------------
# CHECK: PLOT ORIGINAL AND PREPROCESSED FIRST FRAME
# --------------------------------------------------------------------------

fig, axs = plt.subplots(1, 2)
axs[0].set_title("Original")
axs[0].imshow(first_frame)

axs[1].set_title("Preprocessed")
axs[1].imshow(video[0])

fig.savefig(save_dir/"preprocessing.pdf", dpi=200)
plt.show()

# --------------------------------------------------------------------------
# CHECK: COMPARE CONSECUTIVE FRAMES
# --------------------------------------------------------------------------

ax = piv.compare_frames(0, show=False)
plt.savefig(save_dir/"frame_comparison.pdf", dpi=200)
plt.show()

# --------------------------------------------------------------------------
# RUN PIV
# --------------------------------------------------------------------------

results = piv.run(step=DEFAULT_STEP, animate=True, save_at=save_dir/"piv")
try:
    for time, u, v, flags in tqdm(results):
        pass
finally:
    results.close()
    plt.ioff()
