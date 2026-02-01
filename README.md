# "Manual" extraction of the affiliations from the PDF and the metadata

The goal of this helper is to extract that affiliations from the PDFs of the ISCA archive using the ISCA archive metadata.

This repository is aimed to be temporary and will be integrated into a larger ISCA archive analysis repository

## pre-requisites

The repository requires the following python packages:
  - python-json-logger
  - pandas
  - pymupdf

It also assumes you have the ISCA archive metadata and content somewhere

## Bash helper


Here is the bash script, I am using to extract the affiliations which are present on the repository:

```sh
#!/bin/bash -xe

mkdir -p interspeech_2013_2025_affiliations/log/
mkdir -p interspeech_2013_2025_affiliations/dataframe/

for year in $(seq 2013 2025)
do
  python extract_affiliations_manually.py \
      -v -l "interspeech_2013_2025_affiliations/log/$year.json"         \
      "/home/lemaguer/work/current_projects/isca_archive/code/isca-archive/published/metadata/interspeech_${year}.json" \
      "/home/lemaguer/work/current_projects/isca_archive/code/isca-archive/published/archive/interspeech_${year}" \
      "interspeech_2013_2025_affiliations/dataframe/$year.tsv"
done
```

Please adapt the paths to your needs

## Python helper

```sh
❯ python extract_affiliations_manually.py -h
usage: extract_affiliations_manually.py [-h] [-l LOG_FILE] [-v] input_metadata_file archive_conf_dir output_dataframe_affiliations

Helper to extract the affiliations from the ISCA archive data using the metadata

positional arguments:
  input_metadata_file   The input metadata file
  archive_conf_dir      The ISCA archive conference directory which contains the PDF
  output_dataframe_affiliations
                        The output dataframe containing the

options:
  -h, --help            show this help message and exit
  -l LOG_FILE, --log_file LOG_FILE
                        Logger file
  -v, --verbosity       increase output verbosity
```
