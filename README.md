# reticade: the REal TIme CAlcium imaging DEcoder

## First time setup & requirements

This project requires Python 3.10 or greater, and is tested against Python 3.10.2.

After cloning this repository:

#### 1. Ensure the correct Python version is installed

Note: on Windows, replace `python3` commands with `python`.

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

From within the virtual environment, and from within the root directory, start up a Python shell:
```
python3
```

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

In order to receive data from the microscope, the Bruker software needs to write data into shared memory managed by the reticade harness. You can view how reticade has configured the shared memory block through:

```python3
my_harness.show_sharedmem_info()
```
You can use this information to configure the Bruker software to write into the shared memory space. [todo: write an extra section for this when we better understand it]

To verify that you are receiving data from the microscope, you can run:
``` python3
my_harness.show_raw_image()
```
This will display the latest image at the time of running. Close the image to regain control of the shell.

### Testing connectivity to LabView

In order to send data to LabView, we need to tell the harness the IP address of the machine running LabView.
In this example, we'll say that the IP address is `123.123.123.123`.
``` python3
my_harness.set_link_ip("123.123.123.123")
```

You can send some 'dummy' data to LabView and validate that it receives it as follows:
```
dummy_decoded_positions = [100, 200, 300, 400]
my_harness.test_link(dummy_decoded_positions)
```
Be sure to check that LabView actually receives the data correctly!

### Loading a previously trained decoder

Decoders are saved as files with a `.reticade` suffix. This repository includes a 'fake' decoder for validation purposes at `<todo filepath>`. For information on how to create a decoder from previous data, see [todo section on training decoders].

You can load a decoder into a harness as follows:
```python3
my_harness.load_decoder("path/to/decoder.reticade")
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

## Training decoder

A decoder can be trained on another computer and then shared with the computer running the real-time decoding. To train a decoder with the default settings, run the following from your virtual environment (_not_ your Python shell):

```
python3 -m reticade.decoders.train_default_decoder "<path to training data folder>"
```

Reticade expects the training data folder to be structured as follows:
```
training_folder
│   positions.csv
│   metadata.txt
└───images
│   │   0.tif
│   │   1.tif
│   │   ...
```

Where:
* `positions.csv` contains N positions on the linear track, one per line, arranged in chronological order.
* `metadata.txt` contains additional information about the data (e.g. which animal, the date, the training protocol) that will be attached to the decoder.
* `images` is a folder of N images, the alphabetical sorting of which yields the images in chronological order.