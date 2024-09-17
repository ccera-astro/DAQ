# Running the DAQ for Princeton PHY312 

## General 
The main DAQ script is `runDAQ.py`.  Information on this script can
be found in the `README.md` file in this repository.  

## Running `runDAQ.py` 

Here we assume a one-hour run targeting pulsar J0332+5434 .  Once
the dish has been set to track this star, enter the following command:

`> nohup python runDAQ.py --run_mode pulsar --run_type track --run_time 3600 --target J0332+5434 & `

This will create files in the `/home/phy312/data` directory with a base name something 
like `2024-08-23-2121`.   The `nohup` 
command is used to allow the DAQ to continue running, even if the connection
to the receiver machine is lost.  Initially, data will be written to `/home/phy312/data/2024-08-23-2121_1.raw`
and `/home/phy312/data/2024-08-23-2121_2.raw`.   Upon completion of the run, these files will 
be replaced with reduced files named `/home/phy312/data/2024-08-23-2121_1.sum`
and `/home/phy312/data/2024-08-23-2121_2.sum`.    In addition, a metadata file named 
`/home/phy312/data/2024-08-23-2121.json` will be created.  

To convert the pair of `.sum` files to a single `.npz` file that is compatible 
with the PHY312 handout, enter the following command

`> python makeNPZ.py -b 2024-08-23-2121` 

The resulting files (`.json` and `.npz`) can then be copied using `ssh` to a 
machine at Princeton.

## Troubleshooting
If `runDAQ.py` fails to instantiate a `top_block` try entering the following command
to rebuild the `DAQ.py` script.

`grcc DAQ.grc` 



