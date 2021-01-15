# Data Mapper
The script `remapdata.py` copies grid data from a FLASH checkpoint (chk) file and writes it into the grid of another chk file, for the purpose of restarting a simulation with a different number of zones-per-block.
Based on a script originally written by [Carl E. Fields](https://github.com/carlnotsagan).

### Usage
1. Have a python environment with `numpy`, `yt`, `h5py`, and `mpi4py`.

2. Change the parameters `file_read` and `file_write` to the names of the chk files. 

3. Specify the physical variables to copy in the `variables` parameter, or allow it to copy all variables available.

4. To allow multiple MPI processes to write to the same chk file, set the bash environment variable `export HDF5_USE_FILE_LOCKING=FALSE`

5. Run the script, e.g. `mpirun -np 12 python remapdata.py`

### Notes
- Only leaf blocks are mapped. This reduces the amount of data to copy, and avoids issues with zone-alignment across refinement levels (see below). The rest of the block tree should automatically get filled on sim restart. 
- There's a bug in `yt` where the `point()` function sometimes returns an empty value if the point is aligned with the zone-edge of the chk being read (see issue [2891](https://github.com/yt-project/yt/issues/2891)). This should be avoided anyway if the new chk has equal or higher resolution.
- It appears the actual file writes are still serial, so using too many processes will just spend most of their time waiting to write. From initial tests, 12 processes seems like an ok balance. 
- Could look into using proper [parallel h5py](https://docs.h5py.org/en/stable/mpi.html) to improve on this, but requires re-building HDF5 and h5py for MPI. 
