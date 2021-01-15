# Data Mapper
The script `remapdata.py` copies data from a FLASH chk file and writes it into another chk file, for the purpose of restarting a simulation with a different number of zones-per-block.

Recent changes include:
- Only leaf blocks are mapped. This reduces the amount of data to copy, and avoids issues with zone-alignment across refinement levels (see below). The rest of the block tree should get filled on sim restart. 
- Get the full list of variables to copy from `field_list` in `yt`.
- Split the blocks more evenly among MPI ranks
- Addressed an issue (bug?) with `yt` where the `point()` function returns an empty value if the point is aligned with the zone-edge of the chk being read. This should be avoided anyway if the new chk has equal or higher resolution.

### Usage
1. Have a python environment with `numpy`, `yt`, `h5py`, and `mpi4py`.

2. Change the parameters `file_read` and `file_write` to the names of the chk files. 

3. To allow multiple MPI processes to write to the same chk file, set the bash environment variable `export HDF5_USE_FILE_LOCKING=FALSE`

4. Run the script, e.g. `mpirun -np 12 python remapdata.py`

### Notes
It appears the actual file writes are still serial, so using too many processes will just spend most of their time waiting to write. From initial tests, 12 processes seems like an ok balance.   

Could look into using proper [parallel h5py](https://docs.h5py.org/en/stable/mpi.html) to improve on this, but requires re-building HDF5 and h5py for MPI. 