import sys
import os

import matplotlib
from reticade import decoder_harness
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import imread
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from skimage.transform import rescale
import matplotlib.animation as animation

SAMPLE_RATE_HZ = 30
NUM_FRAMES_TO_VIEW = SAMPLE_RATE_HZ * 30

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
image_path = sys.argv[2]
print(f"Loading decoder from {path_in}")
pipeline = decoder_harness.DecoderPipeline.from_json(path_in)

decoder_index = 8
decoder = pipeline.pipeline_stages[decoder_index]
coefs = np.copy(decoder.underlying_decoder.coef_).reshape((9, 32, 32))

fig, axs = plt.subplots(3, 3)
cmap_names = ['Purples', 'Blues', 'Greens', 'Oranges', 'Reds']
bin_colors = ['darkred', 'orangered', 'gold', 'lawngreen', 'teal', 'deepskyblue', 'blue', 'darkviolet', 'deeppink']
for coef_idx in range(coefs.shape[0]):
    ax_i = coef_idx % 3
    ax_j = int(coef_idx / 3)
    ax = axs[ax_j][ax_i]
    ax.set_title(f"Bin {coef_idx}")
    actual_cmap = LinearSegmentedColormap.from_list(f"cmap{coef_idx}", ['white', bin_colors[coef_idx]])
    imref = ax.imshow(np.abs(coefs[coef_idx,:,:]), cmap=actual_cmap)
    fig.colorbar(imref, ax=ax, shrink=0.9)
    ax.set_xticks([])
    ax.set_yticks([])
fig.suptitle("Classifier coefficient maps", fontsize=24)
plt.show()

fig, ax = plt.subplots()
cmap_names = ['Purples', 'Blues', 'Greens', 'Oranges', 'Reds']
ax.set_title(f"Classifier coefficient map", fontsize=24)

first_image = imread(get_image_paths(image_path)[0])
ax.imshow(first_image, cmap='gray')
ax.set_xticks([])
ax.set_yticks([])
for coef_idx in range(coefs.shape[0]):
    cmap_name = cmap_names[coef_idx % len(cmap_names)]
    actual_cmap = LinearSegmentedColormap.from_list(f"cmap{coef_idx}", ['white', bin_colors[coef_idx]])

    coef_sizes = rescale(np.abs(coefs[coef_idx,:,:]), 16, order=0, anti_aliasing=False)
    alphas = (coef_sizes > 0) * 0.5
    ax.imshow(coef_sizes, cmap=actual_cmap, alpha=alphas)

fakecmap = ListedColormap(bin_colors)
normalizer = matplotlib.colors.Normalize(vmin=0, vmax=900)
fig.colorbar(matplotlib.cm.ScalarMappable(norm=normalizer, cmap=fakecmap))
plt.show()

fig, ax = plt.subplots()
ax.set_title(f"Merged Coefficients")
merged_coeffs = np.sum(np.abs(coefs), axis=0)
imref = ax.imshow(merged_coeffs, cmap=plt.get_cmap('plasma'))
fig.colorbar(imref, ax=ax)
ax.set_xticks([])
ax.set_yticks([])
plt.show()

raw_ims = []
multiplied_ims = []
merged_coeffs_big = rescale(merged_coeffs, 16, order=0, anti_aliasing=False)
merged_coeffs_big = merged_coeffs_big > 0
for i, image_file in enumerate(get_image_paths(image_path)):
    if i > NUM_FRAMES_TO_VIEW:
        break
    image = imread(image_file)
    raw_ims.append(image)
    multiplied_ims.append(np.multiply(image, merged_coeffs_big))

fig, axs = plt.subplots(1, 2)
ax = axs[0]
ax.set_title("Raw Image", fontsize=18)
raw_ref = ax.imshow(raw_ims[0])
ax.set_xticks([])
ax.set_yticks([])

ax = axs[1]
ax.set_title("Masked by nonzero weights", fontsize=18)
masked_ref = ax.imshow(multiplied_ims[0])
ax.set_xticks([])
ax.set_yticks([])

def update(idx):
    masked_ref.set_data(multiplied_ims[idx])
    raw_ref.set_data(raw_ims[idx])

#fig.suptitle("Importance of motion correction", fontsize=24)
ani = animation.FuncAnimation(fig, update, range(NUM_FRAMES_TO_VIEW), interval=33)
fig.set_figheight(6)
fig.set_figwidth(13)
fig.set_dpi(150)

plt.show()
