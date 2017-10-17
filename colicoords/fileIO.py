import h5py
import numpy as np
import tifffile
import os
from xml.etree import cElementTree as etree
import warnings
from colicoords.cell import Cell
from colicoords.data_models import Data


def save(file_path, cell_obj, imagej=False):
    ext = os.path.splitext(file_path)[1]
    if ext == '.cc' or '':
        if ext == '':
            file_path += '.cc'

        with h5py.File(file_path, 'w') as f:
            attr_grp = f.create_group('attributes')

            attr_grp.attrs.create('r', cell_obj.coords.r)
            attr_grp.attrs.create('xl', cell_obj.coords.xl)
            attr_grp.attrs.create('xr', cell_obj.coords.xr)
            attr_grp.attrs.create('coeff', cell_obj.coords.coeff)

            #todo python 3 compatiblity: https://github.com/h5py/h5py/issues/441
            if cell_obj.label:
                attr_grp.attrs.create('label', cell_obj.label.encode())

            data_grp = f.create_group('data')
            for k, v in cell_obj.data.data_dict.items():
                grp = data_grp.create_group(k)
                grp.create_dataset(k, data=v)
                grp.attrs.create('dclass', np.string_(v.dclass))
                #todo metatdata

    elif ext == '.tif' or '.tiff':
        with tifffile.TiffWriter(file_path, imagej=imagej) as tif:
            for k, v in cell_obj.data.data_dict.items():
                if v is not None:
                    if imagej:
                        if v.dtype == 'int32':
                            print(k)
                            print('something is int32')
                            v = v.astype('int16')

                    tif.save(v.astype('int32'), description=k)


def load(file_path):
    ext = os.path.splitext(file_path)[1]
    if ext == '.cc':
        with h5py.File(file_path, 'r') as f:

            data_obj = Data()
            data_grp = f['data']
            for key in list(data_grp.keys()):
                grp = data_grp[key]
                data_arr = grp[key]
                dclass = grp.attrs.get('dclass').decode('UTF-8')
                data_obj.add_data(data_arr, dclass=dclass, name=key)

            c = Cell(data_obj)

            attr_grp = f['attributes']
            attr_dict = dict(attr_grp.attrs.items())
            for a in ['r', 'xl', 'xr', 'coeff']:
                setattr(c.coords, a, attr_dict.get(a))
            c.name = attr_dict.get('label')

        return c

    elif ext == '.tif' or '.tiff':
        with tifffile.TiffFile(file_path, is_ome=True) as tif:
            omexml = tif.pages[0].tags['image_description'].value
            try:
                root = etree.fromstring(omexml)
            except etree.ParseError as e:
                # TODO: test this
                warnings.warn("ome-xml: %s" % e)
                omexml = omexml.decode('utf-8', 'ignore').encode('utf-8')
                root = etree.fromstring(omexml)


def load_thunderstorm(file_path):
    """
    Load a .csv file from THUNDERSTORM output
    :param file_path: Target file to open
    :return:
    """

    assert(os.path.splitext(file_path)[1] == '.csv')

    dtype = {
        'names': ("id", "frame", "x", "y", "sigma", "intensity", "offset", "bkgstd", "chi2", "uncertainty_xy"),
        'formats': (int, int, float, float, float, float, float, float, float, float)
    }

    storm_table = np.genfromtxt(file_path, skip_header=1, dtype=dtype, delimiter=',')
    return storm_table