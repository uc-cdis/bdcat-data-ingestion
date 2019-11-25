import os
import csv
from collections import OrderedDict


def get_sample_data_from_manifest(manifest_file, dem="\t"):
    """
    Create an OrderedDictionary mapping sample_id to properties from a
    genome_file_manifest.csv file (output of the generate-file-manifest.sh script).
    Args:
        manifest_file (string)
        dem (string): delimiter used to separate entries in the file. for a tsv, this is \t
    Returns:
        files (OrderedDict): maps a sample_id to its properties
    """
    files = OrderedDict()
    with open(manifest_file, "rt") as csvfile:
        csvReader = csv.DictReader(csvfile, delimiter=dem)
        for row in csvReader:
            row["file_size"] = int(row["file_size"])
            if row["submitted_sample_id"] in files:
                files[row["submitted_sample_id"]].append(row)
            else:
                files[row["submitted_sample_id"]] = [row]

    return files


def get_sample_info_from_dbgap_extract_file(manifest_file, dem="\t"):
    """
    Create an OrderedDictionary mapping sample_id to properties from a
    dbgap_extract.tsv file (output of the dbgap_extract.py script).

    Args:
        manifest_file (string)
        dem (string): delimiter used to separate entries in the file. for a tsv, this is \t
    Returns:
        files (OrderedDict): maps a sample_id to its properties
    """
    files = OrderedDict()
    with open(manifest_file, "rt") as csvfile:
        csvReader = csv.DictReader(csvfile, delimiter=dem)
        for row in csvReader:
            if row["submitted_sample_id"] in files:
                files[row["submitted_sample_id"]].append(row)
            else:
                files[row["submitted_sample_id"]] = [row]

    return files


def write_file(filename, rows, fieldnames=None):
    fieldnames = fieldnames or rows[0].keys()
    with open(filename, mode="w") as outfile:
        writer = csv.DictWriter(outfile, delimiter="\t", fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def read_mapping_file(fname):
    """
        Uses a studys_to_google_access_groups.txt file to create a dictionary mapping study_accession_with_consent's 
        to their google group name.
        
        Args:
            manifest_file (string)
            dem (string): delimiter used to separate entries in the file. for a tsv, this is \t
        Returns:
            files (OrderedDict): maps a sample_id to its properties
    """
    mapping = {}
    with open(fname, "r") as fopen:
        lines = fopen.readlines()
        for line in lines:
            words = line.split(":")
            mapping[words[0].strip()] = words[1].strip()

    return mapping


def _sync_2_dicts(dict1, dict2):
    for key, new_row in dict1.items():
        if key not in dict2:
            new_row["GUID"] = "None"
            dict2[new_row["submitted_sample_id"] + "|" + new_row["md5"]] = new_row

    return dict2


def create_or_update_file_with_guid(fname, indexable_data, fieldnames=None):
    """
    If the file fname does not exist, create a file with the indexable_data.
    if the file fname does exist, merge the file with the indexable_data.
    
    Args:
        fname (string): output path
        indexable_data (list of OrderedDicts): a list of dictionary
        fieldnames (list of strings): the file header
    Returns:
        None
    """
    if not os.path.exists(fname):
        for data in indexable_data:
            data["GUID"] = "None"
        write_file(fname, indexable_data, fieldnames=fieldnames)
    else:
        dict1 = OrderedDict()
        dict2 = OrderedDict()

        for data in indexable_data:
            dict1[data["submitted_sample_id"] + "|" + data["md5"]] = data

        with open(fname, "rt") as csvfile:
            csvReader = csv.DictReader(csvfile, delimiter="\t")
            for row in csvReader:
                row["file_size"] = int(row["file_size"])
                dict2[row["submitted_sample_id"] + "|" + row["md5"]] = row

        # merge dict1 to dict1
        dict2 = _sync_2_dicts(dict1, dict2)
        L = [v for _, v in dict2.items()]
        write_file(fname, L, fieldnames)