# Slow-Fast BMI Protocol

## 1 Environment Preparation

### 1.1 Set up reticade
Set up the current version of reticade on the imaging computer. Full instructions are in `README.md`.

The short version:
* Download the reticade zip from GitHub.
* Extract it to a folder, then within the folder:

```
python -m venv env
env\Scripts\activate.bat
python -m pip install -r requirements_windows.txt
```

### 1.2 Set up LabView

Open the LabView project (TODO: project name here) on the LabView computer and set up the project as normal. The LabView project should be a 400 cm long track with a reward site at 250 cm.

### 1.3 Validate inter-machine communication

* Note the IP address of the LabView computer
* On the imaging computer, open a python instance in the venv with `python`, then:

```python3
from reticade import interactive
harness = interactive.Harness()
harness.set_link_ip("<IP of LabView computer>")
```
* Turn on the BMI button within LabView, then from the reticade harness:
```
dummy_data = [0, 0, 0, 0, 0]
harness.test_link(dummy_data)
```
* Verify that LabView receives the BMI input, then turn off the BMI button

## 2 Imaging setup

### 2.1 Introduce animal to rig

Introduce the animal to the rig as normal. Configure the field of view from within PrairieView (it is important that the version of PrairieView is 5.6, 5.4 will not work).

### 2.2 Imaging link validation

With PrairieView running in 'Live Imaging' mode, resonant galvo (30 Hz), test the following in reticade:

```python3
harness.set_imaging_channel(2)
harness.show_live_view()
```
And validate that the viewport shown by reticade matches that seen in the PrairieView viewport.

## 3 Generate training data

Configure PrairieView to record a 5-minute long timeseries. Frame averaging should be turned off, and imaging frequency should be 30 Hz. Run the 5-minute trial, this should produce:

* A `.pos` and `.adat` file from LabView
* About 9000 `.tif` image files from PrairieView

## 4 BMI Decoder Training

### 4.1 Position extraction

Use the `legacy_scripts/position_extractor.m` MATLAB script to generate a `positions.csv` file. 

### 4.2 Training the decoder

Copy the `positions.csv` file into the folder where the `.tif` images are saved, then from a new terminal window in the root of the reticade directory, run:
```
env\Scripts\activate.bat
python3 -m reticade.train_decoder_binary "<path to image folder>"
```

This will take 2-3 minutes to run and produce a saved decoder file `decoder-<current datetime>.json`.

### 4.3 Load the decoder into the harness

From the reticade harness window, run:

```python3
harness.load_decoder("path/to/decoderfile.json")
```

## 5 Run the BMI trial

### 5.1 Prepare the trial

Ensure LabView is ready to record the positions/adat component of the trial.

### 5.2 Run the trial

In succession, perform the following:
* Turn the 'Use BMI' button on in LabView. This should halt motion on the track (as we previously primed the initival velocity as zero).
* Start the live imaging in PrairieView.
* From within reticade, run:
```
harness.run(stop_after_seconds=300)
```

### 5.3 Save data

Once the reticade harness is finished running, it will produce a `.npy` file that contains a record of decoding results and signal-processed images. Also be sure to collect the `.adat` and `.pos` files from LabView.
Once reticade has finished running, it's safe to stop imaging in PrairieView and recording in LabView.
