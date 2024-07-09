
#!/bin/bash

# first, cd to the folder containing this bash script (and Dockerfile + run_freesurfer.py)

version_tag="0.0.1"
version_tag_dash="0-0-1"

# Build:
docker build -t shrgud/fs7.4.1_bids_app:${version_tag} -f Dockerfile .

# Test:
dir_to_mount="/Users/gudapatis/Desktop/OpenNeuro-CATD"
mounted_dir="/root/OpenNeuro-CATD"
mounted_input_dir="/root/OpenNeuro-CATD/BIDS"
mounted_output_dir="/root/OpenNeuro-CATD/derivatives"
file_to_mount="/Users/gudapatis/Documents/license.txt"
mounted_license="/root/license.txt"

participant_label="sub-23823"

# unzipped input ds:
docker run --rm -it -v ${dir_to_mount}:${mounted_dir} \
    -v ${file_to_mount}:${mounted_license} \
    shrgud/fs7.4.1_bids_app:${version_tag} \
    ${mounted_input_dir} ${mounted_output_dir} participant \
    --participant_label ${participant_label} \
    --t1w \
    --t2w \
    -u m \
    -l ${mounted_license}

    # Output : Should have created a derivatives directory inside OpenNeuro-CATD and 2 sub-directories
    # within it (one each for fs7.4.1_recon_all_clinical and fs7.4.1_recon_all) with each having one output directory per scan