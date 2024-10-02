# DAQ

## Data acquisition scripts.    
The principal modules are `DAQ.py`,
which is the Python representation of the `DAQ.grc` flowgraph;
and `runDAQ.py`, which is used to launch `DAQ.py`. `DAQ.py` incorporates
a ZMQ PUB Sink block, which can be used to monitor the data in real time. 
 Although `DAQ.py`can be run directly, it is generally more convenient to use
`runDAQ.py`.


### Run modes 
`runDAQ.py` runs in four basic "modes": pulsar, doppler, scan, or generic.
The mode is specified with the `run_mode` parameter.
The choice of mode determines the default values of other run time parameters,
such as `f_center, fft_size, samp_rate, decimation_factor`, etc.    These 
defaults can be overridden by specifying them explicitly at run time.

### `runDAQ.py` parameters 
- `run_mode`: determines run mode (see above)
- `run_type`: which should be either "track" or "transit"
- `run_time`: the total run time in integer seconds
- `data_dir` : data directory 
- `target`: the astrophysical target, e.g., M31  
  Note that setting this parameter to "test" or "junk" will lead to eventual deletion.
- `lmst`: wait until this time in LMST (specified in hours) before starting the DAQ
- `n_jobs` : setting this parameter causes the same run to be repeated `n_jobs` time.  This
is useful, for example, if one wants to take a series of (say) 10 minute runs. 
- `XMLRPC`: enable control over file name changing via XMLRPC
- `no_avg`: don't compute the average PSD (see below)
- `no_sum`: don't compute the sum time series (see below)

### Data formats

The base file name of a given dataset is a time stamp of the form `YYYY-MM-DD-hhmm` 
followed by either `"_1"` or `"_2"` corresponding to the receiver channel.

The following file extensions are used:

- `.json`  This is a JSON file containing the run metadata
- `.raw`   This is a time series of vectors (FFT PSDs)
- `.avg`   This is a PSD averaged over the full .raw file
- `.sum`   This is a time series corresponding to the sum of the PSDs in the .raw file.
- `.npz`   This file format combines both channels, add MJD timestamp information, and provides a result in `numpy`'s `.npz` format.   See the `makeNPZ` section below for instructions on converting `.sum` files to `.npz` files.


### Important Note ###
During data taking, the output of the DAQ flowgraph is written to the disk 
in the form of series of vectors (FFT PSDs) (the `.raw` file).  To save 
disk space, by default at the end of each run, either a `.avg` file (for Doppler mode) or
a `.sum` file (for Pulsar mode) is computed and <span style="color:red"> the .raw file is deleted. </span>
To avoid this, the --no_avg or --no_sum parameters can be used. 

### Troubleshooting
If `runDAQ.py` fails to instantiate a `top_block` try entering the following command
to rebuild the `DAQ.py` script.

`grcc DAQ.grc` 

### `makeNPZ.py` ###
A utility script called `makeNPZ.py` has been provided to convert `.sum` files to the `.npz` format that is compatible with Princeton's PHY312 pulsar lab.   The run parameters are 

- `data_dir`: data directory (default = `/home/phy312/data` if run from the phy312 account)
- `base_name`: base name of data file--e.g. 2024-08-23-2121 
- `down_sample`: number of samples to combine (default = 4)

