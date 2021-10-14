import h5py
from typing import Union, List
from pathlib import Path
import os
import pandas as pd
import warnings
import numpy as np

SIZE_TO_MB = {
    np.dtype("bool"): 1e-6 * 0.125,
    np.dtype("uint8"): 1e-6,
    np.dtype("int16"): 2 * 1e-6,
    np.dtype("uint16"): 2 * 1e-6,
    np.dtype("int32"): 4 * 1e-6,
    np.dtype("uint32"): 4 * 1e-6,
    np.dtype("float32"): 4 * 1e-6,
    np.dtype("float64"): 8 * 1e-6,
}


def main():
    pass


def h5_write_channel(f: h5py.File, data: np.array, name: str, copy_from: h5py.Dataset = None, attrs: dict = None,
                     compression='gzip', overwrite=True):
    if overwrite:
        if name in f:
            del f[name]
    dset = f.create_dataset(name=name, data=data, compression=compression)
    if copy_from is not None:
        h5_copy_attributes(copy_from, dset)
    if attrs is not None:
        h5_write_attributes(dset, attrs, overwrite=True)
    return dset


def h5_iterate(f: h5py.File, attr: str):
    unique = list(set([dset.attrs.get(attr) for dset in h5_datasets(f)]))
    return [h5_select(f, {attr: u}) for u in unique]


def h5_set(f: h5py.File, attr: str, remove_none=True):
    unique = set([dset.attrs.get(attr) for dset in h5_datasets(f)])
    if None in unique:
        unique.remove(None)
    return unique


def h5_copy_attributes(
        dset_from: h5py.Dataset,
        dset_to: h5py.Dataset,
        *,
        include: Union[tuple, list] = None,
        exclude: Union[tuple, list] = None
):
    if exclude is None:
        exclude = []
    if include is None:
        for attr in dset_from.attrs.keys():
            if attr not in exclude:
                dset_to.attrs[attr] = dset_from.attrs.get(attr, "NA")
    else:
        for attr in include:
            dset_to.attrs[attr] = dset_from.attrs.get(attr, "NA")


def h5_write_attributes(
        dset: h5py.Dataset, attrs: dict = None, overwrite: bool = False
):
    if attrs is None:
        attrs = dict()
    if overwrite:
        for key in attrs:
            dset.attrs[key] = attrs.get(key, "NA")
    else:
        for key in attrs:
            if dset.attrs.get(key) in ["NA", None]:
                dset.attrs[key] = attrs[key]


def h5_rename_file_attributes(f: h5py.File, attr: str, old_new: dict):
    f.attrs[attr] = old_new.get(f.attrs.get(attr), f.attrs.get(attr))


def h5_rename_attributes(f: h5py.File, attr: str, old_new: dict):
    for dset in h5_datasets(f):
        dset.attrs[attr] = old_new.get(dset.attrs.get(attr), dset.attrs.get(attr))


class Collector:
    def __init__(self, collect=h5py.Dataset):
        # Store an empty list for dataset names
        self.names = []
        self.objs = []
        self.collect = collect

    def __call__(self, name, h5obj):
        # only h5py datasets have dtype attribute, so we can search on this
        if isinstance(h5obj, self.collect) and not name in self.names:
            self.names.append(name)
            self.objs.append(h5obj)


def h5_recursive_collect(
        f: h5py.File, collect: Union[h5py.Dataset, h5py.Group], return_names: bool = True
):
    collector = Collector(collect)
    f.visititems(collector)
    if return_names:
        return collector.names
    return collector.objs


def h5_rename_dataset(f: h5py.File, dset_name: str, new_dset_name: str):
    f['temporary_dataset_'] = f[dset_name]
    del f[dset_name]
    for grp in h5_groups(f, return_names=False):
        if len(grp) == 0:
            del f[grp.name]
    f[new_dset_name] = f['temporary_dataset_']
    del f['temporary_dataset_']
    return f[new_dset_name]


def h5_datasets(f: h5py.File, return_names=False):
    return h5_recursive_collect(f, h5py.Dataset, return_names=return_names)


def h5_groups(f: h5py.File, return_names=False):
    return h5_recursive_collect(f, h5py.Group, return_names=return_names)


def h5_select(
        f: h5py.File, attr_select: dict = None, not_attr_select: dict = None
) -> List[h5py.Dataset]:
    dsets = []
    for dset in h5_datasets(f):

        check = []
        if attr_select:
            for a in attr_select:
                if isinstance(attr_select[a], (tuple, list)):
                    check.append(dset.attrs.get(a) in attr_select[a])
                else:
                    check.append(dset.attrs.get(a) == attr_select[a])

        uncheck = []
        if not_attr_select:
            for b in not_attr_select:
                if isinstance(not_attr_select[b], (tuple, list)):
                    uncheck.append(dset.attrs.get(b) in not_attr_select[b])
                else:
                    uncheck.append(dset.attrs.get(b) == not_attr_select[b])

        if all(check) and not any(uncheck):
            dsets.append(dset)
    return dsets


def h5_summary(filename):
    file_attrs = ["condition"]
    fs = "{}:\t{}"
    file_attrs_string = []
    base_attrs = ["shape", "dtype", "size"]
    attrs_attrs = [
        "element_size_um",
        "img_type",
        "stain",
        "cycle",
        "wavelength",
        "level",
    ]

    with h5py.File(filename, "r") as fl:
        file_attrs_string.append(fs.format("filename", os.path.basename(fl.filename)))
        for attr in file_attrs:
            file_attrs_string.append(fs.format(attr, fl.attrs.get(attr, "NA")))
        file_attrs_string.append("")
        dset_names = h5_datasets(fl, return_names=True)
        df = pd.DataFrame(columns=base_attrs + attrs_attrs, index=dset_names)
        df.index.name = "name"
        for k in dset_names:
            for attr in base_attrs:
                if attr == "size":
                    sz = getattr(fl[k], attr, "NA")
                    if sz != "NA":
                        sz = round(
                            sz * SIZE_TO_MB[fl[k].dtype], 2
                        )  # convert size attribute to MB for readability
                    df.loc[k, attr] = sz
                else:
                    df.loc[k, attr] = getattr(fl[k], attr, "NA")

            for attr in attrs_attrs:
                df.loc[k, attr] = fl[k].attrs.get(attr, "NA")

    df.reset_index(level=0, inplace=True)
    return "\n".join(
        [
            *file_attrs_string,
            df.to_string(
                index=False,
                na_rep="",
                max_rows=None,
                max_cols=None,
                line_width=140,
                justify="right",
            ),
            "\n",
        ]
    )


def h5_experiment_summary(fld):
    base_attrs = ["name"]
    file_attrs = ["condition", "distance_to_bottom", "well"]
    df = pd.DataFrame(columns=base_attrs + file_attrs)
    for fn in Path(fld).glob("*.h5"):
        with h5py.File(fn) as f:
            data = {"name": os.path.basename(f.filename)}
            for attr in file_attrs:
                data[attr] = f.attrs.get(attr, "NA")
            #             print(data)
            df = df.append(data, ignore_index=True)
    return df.to_string(
        index=False,
        na_rep="",
        max_rows=None,
        max_cols=None,
        line_width=120,
        justify="right",
    )


def to_numpy(img, pass_everything=False):
    if isinstance(img, np.ndarray):
        trans_img = img
    elif isinstance(img, h5py.Dataset):
        trans_img = img[...]
    else:
        if pass_everything:
            trans_img = img
        else:
            raise ValueError('Unknown image type: {}'.format(type(img)))
    return trans_img


if __name__ == "__main__":
    main()
