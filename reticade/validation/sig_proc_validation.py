import sys
import os
from reticade.decoding import sig_proc
from reticade.decoding import motion_correction
from matplotlib.pyplot import imread
import numpy as np
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import cm
import time

SAMPLE_RATE_HZ = 30
NUM_FRAMES_TO_VIEW = SAMPLE_RATE_HZ * 30

def get_image_paths(image_path):
    contents = os.listdir(image_path)
    contents.sort()
    all_images = []
    for c in contents:
        if '.tif' in c and c[0] != '.':
            all_images.append(image_path + '/' + c)
    return all_images

def get_intermediate_ims(path, stages):
    results = []
    for i, image_file in enumerate(get_image_paths(path)):
        if i > NUM_FRAMES_TO_VIEW:
            break
        image = imread(image_file)
        last_val = image
        for j, stage in enumerate(stages):
            last_val = stage.process(last_val)
        results.append(last_val)
    return np.array(results)

path_in = sys.argv[1]
save_file = None
if len(sys.argv) > 2:
    save_file = sys.argv[2]

downsampler = sig_proc.Downsampler((4, 4))
low_pass = sig_proc.LowPassFilter(1.2)

correction_ref = get_intermediate_ims(path_in, [downsampler, low_pass]).mean(axis=0)
correction = motion_correction.FlowMotionCorrection(correction_ref)
delta = sig_proc.DeltaFFilter(0.3, 0.001, (128, 128), initial_state=correction_ref)
second_downsammpler = sig_proc.Downsampler((4, 4))
dog = sig_proc.DoGFilter(0.5, 2.5)
threshold = sig_proc.Threshold(0)
sig_proc_pipeline = [downsampler, low_pass, correction, delta, dog, threshold, second_downsammpler]
processed_ims = [[] for _ in range(len(sig_proc_pipeline) + 1)] # First is raw image
descriptions = ["raw"] + [type(t).__name__ for t in sig_proc_pipeline]
execution_times = [0 for _ in descriptions]
for i, image_file in enumerate(get_image_paths(path_in)):
    if i > NUM_FRAMES_TO_VIEW:
        break
    image = imread(image_file)
    processed_ims[0].append(image)
    last_val = image
    for j, stage in enumerate(sig_proc_pipeline):
        start = time.perf_counter()
        last_val = stage.process(last_val)
        stop = time.perf_counter()
        execution_times[j+1] += (stop - start)
        processed_ims[j+1].append(last_val)

NUM_FRAMES_TO_VIEW = min(NUM_FRAMES_TO_VIEW, len(processed_ims[0]))

ms_per_stage = [d * 1000 / NUM_FRAMES_TO_VIEW for d in execution_times]

rows = 2
cols = 4
fig, ax = plt.subplots(rows, cols)
fig.set_figheight(6)
fig.set_figwidth(18)
fig.set_dpi(150)
imrefs = []

cmap_diverge = plt.get_cmap("seismic")
cmap_mono = plt.get_cmap("viridis")

i = 0
for r in range(rows):
    for c in range(cols):
        if i >= len(processed_ims):
            break
        # Use different colorbars depending on whether negative is allowed
        if np.any(processed_ims[i][100] < 0):
            imrefs.append(ax[r][c].imshow(processed_ims[i][100], norm=colors.CenteredNorm(), cmap=cmap_diverge))
        else:
            imrefs.append(ax[r][c].imshow(processed_ims[i][100], cmap=cmap_mono))
        ax[r][c].set_title(f"[{i}] {descriptions[i]} ({ms_per_stage[i]:.2f} ms/frame)")
        ax[r][c].set_xticks([])
        ax[r][c].set_yticks([])
        fig.colorbar(imrefs[i], ax=ax[r][c])
        
        i += 1

def update(idx):
    for i, imref in enumerate(imrefs):
        imref.set_data(processed_ims[i][idx])

ani = animation.FuncAnimation(fig, update, range(NUM_FRAMES_TO_VIEW), interval=33)

if save_file:
    ani.save('XM036-2x-res-pmt-680-041.mp4', fps=30)
else:
    plt.show()
