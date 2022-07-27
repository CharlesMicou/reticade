# reticade: the REal TIme CAlcium imaging DEcoder

## First time setup & requirements

### Windows

This project requires Python 3.8 or greater, and is tested against Python 3.8.4 on Windows.

```
python --version
```

#### 2. Ensure pip is installed

```
python -m pip --version
```

#### 3. Ensure venv is installed

```
python -m pip install --user virtualenv
```

#### 4. Create a new virtual environmnet
```
python -m venv env
```


#### 5. Activate your virtual environment
```
env\Scripts\activate.bat
```

NB: if you want to leave the virtual environment from this terminal window, run `deactivate`.

#### 6. Install Dependencies
From within the virtual environment, run:

```
python -m pip install -r requirements_windows.txt
```

#### 7. Run the tests
This will run a quick sanity-check to test self-contained components. It won't test connectivity to the Bruker imaging software or LabView instance! We'll look into how to check test those connections in the next section.

```
python -m pytest -W ignore::DeprecationWarning
```

### Linux and OSX

This project requires Python 3.8 or greater, and is tested against Python 3.10.2 on OS X and Linux.

After cloning this repository:

#### 1. Ensure the correct Python version is installed

```
python3 --version
```

#### 2. Ensure pip is installed

```
python3 -m pip --version
```

#### 3. Ensure venv is installed

```
python3 -m pip install --user virtualenv
```

#### 4. Create a new virtual environmnet
```
python3 -m venv env
```


#### 5. Activate your virtual environment
```
source env/bin/activate
```

NB: if you want to leave the virtual environment from this terminal window, run `deactivate`.

#### 6. Install Dependencies
From within the virtual environment, run:

```
python3 -m pip install -r requirements.txt
```

#### 7. Run the tests
This will run a quick sanity-check to test self-contained components. It won't test connectivity to the Bruker imaging software or LabView instance! We'll look into how to check test those connections in the next section.

```
python3 -m pytest -W ignore::DeprecationWarning
```

## Using Reticade Interactively

From within the virtual environment, and from within the root directory, start up a Python shell with the `python` command on Windows (or `python3` on Linux/OSX).

Note: to exit the Python shell and return to the command-line simply enter the `exit()` command.

Import the reticade module.

``` python3
from reticade import interactive
```

Create a new reticade harness:
``` python3
my_harness = interactive.Harness()
```
This harness serves as the main interaction point.

### Testing connectivity to the microscope

This program retrieves image data through PrairieLink. In order for it to retrieve data, the PrairieView software must be running on the machine. It's essential that the version of PrairieView is 5.6 (earlier versions lack the APIs to retrieve raw data quickly enough).
To configure access to image data, first set the channel to read from (this example selects channel 2):

```python3
my_harness.set_imaging_channel(2)
```

To verify that you are receiving data from the microscope, you can run:
``` python3
my_harness.show_raw_image()
```
This will display the latest image at the time of running. Close the image window to regain control of the shell.

If you want to view a continuous stream of data from the microscope, instead run:
```python3
my_harness.show_live_view()
```
Close the window to regain control of the shell.

Warning: if you start an imaging request _after_ starting imaging on the microscope, there's no guarantee that your data will be aligned. It's easier to have the harness query for images before starting imaging, as the start of the recording will then align to the start of imaging data.

### Testing connectivity to LabView

In order to send data to LabView, we need to tell the harness the IP address of the machine running LabView.
In this example, we'll say that the IP address is `123.123.123.123`.
``` python3
my_harness.set_link_ip("123.123.123.123")
```

You can send some 'dummy' data to LabView and validate that it receives it as follows:
```python3
dummy_decoded_velocities = [1, 2, 3, 4]
my_harness.test_link(dummy_decoded_velocities)
```
Be sure to check that LabView actually receives the data correctly!

### Loading a previously trained decoder

Decoders are saved as .json files. This repository includes a 'fake' decoder for validation purposes at `demo/fake_decoder.json`. For information on how to create a decoder from previous data, see the 'Training a decoder' section.

You can load a decoder into a harness as follows:
```python3
my_harness.load_decoder("path/to/decoder.json")
```

### Running reticade after the harness is configured

Once reticade you're happy that reticade is correctly reading from the microscope, sending data to LabView, and has the right decoder loaded, you can start it running.
```python3
my_harness.run(stop_after_seconds=300)
```
Setting the `stop_after_seconds` parameter will gracefully stop reticade after that duration.

### Closing a harness

When you're done with a harness, you should close it in order to:
* Release the shared memory allocated for PrairieView's use
* Release resources associated with the harness
You can do this with:
```python3
my_harness.close()
```
If you forget to close your harness before exiting the environment, you'll get a warning about leaked memory resources.

## Training a decoder

A decoder can be trained on another computer and then shared with the computer running the real-time decoding. To train a decoder with the default settings, run the following from your virtual environment (_not_ your Python shell):

```
python3 -m reticade.train_decoder "<path to training data folder>"
```

Reticade expects the training data folder to be structured as follows:
```
training_folder
│   positions.csv
│   metadata.txt
│   0.tif
│   1.tif
│   ...
```

Where:
* `positions.csv` contains N positions on the linear track, one per line, arranged in chronological order.
* `metadata.txt` contains additional information about the data (e.g. which animal, the date, the training protocol) that will be attached to the decoder.
* `.tif` files are N images, the alphabetical sorting of which yields the images in chronological order.

### Fine-tuning decoder training

The decoder is a pipeline, where each stage in the pipeline can be broadly described as belonging to one of the following categories:
* Signal processing: cleaning up the raw image data
* Pattern matching: machine-learned mappings between signal-processed images and position on the track
* Behavioural interpretation: matching up the animal's behaviour to where it is on the track

The most important part of the decoder to fine-tune on a per-animal basis is the signal processing layer, as different imaging settings will require different signal processing. The first things to look at are:
* The high and low frequencies of the spatial bandpass filter (the DoG filter). A more zoomed-out field of view will have cells that are smaller, so the bandpass needs to be set smaller.
* The time-constants of the delta F filter. These operate on discrete frames, so if you're changing the imaging frequency you need to change these time constants accordingly.

You can visualise arbitrary signal processing pipelines (and test the effect of changes) by running:
```
python3 -m reticade.validation.sig_proc_validation <path to training data folder>
```

## Usage tips

### Populate initial LabView sample

You can send arbitrary data to LabView from the test harness. If you want to initialise the LabView state, e.g. setting the BMI-controlled velocity to zero before running an experiment, you can send a packet to configure the state. For example:

```python3
my_harness.test_link([0])
```

### Position extraction from LabView

The `legacy_scripts` directory contains a Krupic Lab MATLAB script to sync up galvo signals to positions.
