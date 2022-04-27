import sys
import os
from reticade.decoders import sig_proc
from matplotlib.pyplot import imread
import numpy as np
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import cm

SAMPLE_RATE_HZ = 30
NUM_FRAMES_TO_VIEW = SAMPLE_RATE_HZ * 20

def get_image_paths(path_in):
    image_folder = path_in + '/images'
    contents = os.listdir(image_folder)
    contents.sort()
    all_images = []
    for c in contents:
        if '.tif' in c:
            all_images.append(image_folder + '/' + c)
    return all_images

path_in = sys.argv[1]

downsampler = sig_proc.Downsampler((4, 4))
dog = sig_proc.DoGFilter(1, 5)
second_downsammpler = sig_proc.Downsampler((4, 4))
delta = sig_proc.DeltaFSliding(30, 90, (32, 32))
#delta = sig_proc.DeltaFFilter(0.5, 0.2, (32, 32))

sig_proc_pipeline = [downsampler, dog, second_downsammpler, delta]
processed_ims = [[] for _ in range(len(sig_proc_pipeline) + 1)] # First is raw image
descriptions = ["raw", "downsampled 4", "DoG", "downsampled 4", "delta F"]
for i, image_file in enumerate(get_image_paths(path_in)):
    if i > NUM_FRAMES_TO_VIEW:
        break
    image = imread(image_file)
    processed_ims[0].append(image)
    last_val = image
    for j, stage in enumerate(sig_proc_pipeline):
        last_val = stage.process(last_val)
        processed_ims[j+1].append(last_val)


rows = 2
cols = 3
fig, ax = plt.subplots(rows, cols)

imrefs = []

i = 0
for r in range(rows):
    for c in range(cols):
        if i >= len(processed_ims):
            break
        if "delta F" in descriptions[i]:
            imrefs.append(ax[r][c].imshow(processed_ims[i][100], norm=colors.Normalize(-2, 2)))
        else:
            imrefs.append(ax[r][c].imshow(processed_ims[i][100]))
        ax[r][c].set_title(f"{i} {descriptions[i]}")
        ax[r][c].set_xticks([])
        ax[r][c].set_yticks([])
        

        i += 1

def update(idx):
    for i, imref in enumerate(imrefs):
        imref.set_data(processed_ims[i][idx])

ani = animation.FuncAnimation(fig, update, range(NUM_FRAMES_TO_VIEW), interval=33)
plt.show()
