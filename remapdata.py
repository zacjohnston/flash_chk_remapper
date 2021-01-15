import yt
import numpy as np
import h5py
from mpi4py import MPI
import time

file_read = 'test/sedov4_hdf5_chk_0000'
file_write = 'test/sedov1.5_hdf5_chk_0000'

# load the chk file of the 3d progenitor at collapse
data_read = yt.load(file_read)

# load the ccsn data file to be overwritten
data_write = h5py.File(file_write, 'r+')

# list of variables to copy
# variables = ['dens', 'pres', 'temp', 'ye  ', 'velx', 'vely', 'velz']
variables = np.array(data_read.field_list)[:, 1]

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
n_ranks = comm.Get_size()

leaf_blocks = np.where(np.array(data_write['node type']) == 1)[0]
n_blocks = len(leaf_blocks)

# split blocks among ranks as evenly as possible
rank_blocks = np.array_split(leaf_blocks, n_ranks)[rank]
n_rank_blocks = len(rank_blocks)

comm.barrier()
if rank == 0:
    print(f'{n_blocks} leaf blocks, '
          f'distributing ~{n_blocks // n_ranks} blocks per rank, '
          f'copying {len(variables)} variables', flush=True)

comm.barrier()
print(f'rank {rank} doing {n_rank_blocks} blocks', flush=True)
comm.barrier()


def replace_data_over_block_range(blocks):
    nxb = int(data_write['integer scalars'][0][1])
    nyb = int(data_write['integer scalars'][1][1])
    nzb = int(data_write['integer scalars'][2][1])

    arrays = dict.fromkeys(variables)
    for var in arrays:
        arrays[var] = np.zeros((nzb, nyb, nxb))

    for n, b in enumerate(blocks):
        n_fails = 0
        t0 = time.time()

        # cell spacing for given block
        dx = data_write['block size'][b][0] / nxb
        dy = data_write['block size'][b][1] / nyb
        dz = data_write['block size'][b][2] / nzb

        # lower limits in physical space for block
        x_low = data_write['bounding box'][b][0][0]
        y_low = data_write['bounding box'][b][1][0]
        z_low = data_write['bounding box'][b][2][0]

        # Fill arrays
        for i in range(nxb):
            for j in range(nyb):
                for k in range(nzb):
                    x = x_low + (i+0.5) * dx
                    y = y_low + (j+0.5) * dy
                    z = z_low + (k+0.5) * dz

                    point = data_read.point([x, y, z])

                    # Points sometimes fail to return a value if the zone-center
                    # in data_write is aligned with a zone-edge in data_read (yt bug???).
                    # Add a tiny jiggle to bump it off the edge.
                    # Though this should only occur if data_write has lower resolution
                    if len(point['flash', variables[0]]) == 0:
                        n_fails += 1
                        point = data_read.point([x + np.random.rand(),
                                                 y + np.random.rand(),
                                                 z + np.random.rand()])

                    for var in variables:
                        arrays[var][k, j, i] = point['flash', var].v[0]

        # Write block data to file
        for var in variables:
            data_write[var][b, :, :, :] = arrays[var]

        if n_fails > 1:
            print(10*'X', f'{n_fails} POINT FAILS FIXED in rank {rank}, block {b}',
                  10*'X', '\nDouble check output for weirdness!', flush=True)

        t1 = time.time()
        print(f'rank {rank} finished block {b} ({n+1}/{n_rank_blocks}) '
              f'in {t1-t0:.0f} s. '
              f'Rough time remaining: {(t1-t0)*(n_rank_blocks-n-1)/3600:.2f} hr',
              flush=True)

    return
