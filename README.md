## pyfcd

Python code to perform free surface profilometry with synthetic schlieren imaging (fast checkerboard demodulation). Code adapted from: https://github.com/kaspervn/pyfcd. `fcd_processing.py` uses the code at pyfcd to set up the preprocessing and fcd processing for a video.

## pypiv

Python code to perform PIV analysis. Mostly wraps around openpiv functions. `piv_processing.py` uses the code at pypiv to set up the preprocessing and piv processing for a video. `stack_processing.py` uses de preprocessing code at pypiv to preprocess images before stacking and blending them to show the lagrangian particle trajectories.

## pydata

Functions for image processing and video processing. Most of the code was inherited from: https://github.com/trapped-modes-ltg/fcd-analysis

## pyaux

Miscelaneous functions to create gifs, average images, etc.






