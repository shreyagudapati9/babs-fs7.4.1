
import argparse
import os
import os.path as op
import subprocess
import pandas as pd
import re

def cli():
    parser = argparse.ArgumentParser(
        description='SynthSeg BIDS App')
    parser.add_argument(
        'input_dir',
        help='The directory of the (unzipped) input dataset, '
        'or the path to the zipped dataset; '
        'unzipped dataset should be formatted according to the BIDS standard.')

    parser.add_argument(
        'output_dir',
        help='The directory where the output files should be stored')

    parser.add_argument(
        'analysis_level',
        choices=['participant'],
        help='Level of the analysis that will be performed.'
        " Currenlty only 'participant' is allowed.")

    parser.add_argument(
        '--participant_label', '--participant-label',
        help='The label of the participant that should be analyzed. The label'
        ' can either be <sub-xx>, or just <xx> which does not include "sub-".'
        " Currently only one participant label is allowed.",
        required=True)

    parser.add_argument(
        '--t1w',
        help='If present, T1w scans will be processed. If not present, T1w scans will not be processed.', action='store_true')

    parser.add_argument(
        '--t2w',
        help='If present, T2w scans will be processed. If not present, T2w scans will not be processed.', action='store_true')

    parser.add_argument(
        '--flair',
        help='If present, FLAIR scans will be processed. If not present, FLAIR scans will not be processed.', action='store_true')

    parser.add_argument(
        '--mprage',
        help='If present, MPRAGE scans will be processed. If not present, MPRAGE scans will not be processed.', action='store_true')
    
    parser.add_argument(
        '-u', '--age-units', help='Units of age (accepted values : m, d, y)', choices = ['m', 'd', 'y'],required=True)
    
    parser.add_argument(
        '-l', '--license', help='Path to the freesurfer license file', required=True)

    return parser

# Check if participants.tsv contains specific column names: "subject_id", "session_id", and "age_at_scan"
def check_col_names(partDf):
	
    cols = partDf.columns
    if (not ("subject_id" in cols)) or (not ("session_id" in cols)) or (not ("age_at_scan" in cols)):
        print("Please change the column names in `participants.tsv` that contain subject id, \
              session id, and age to `subject_id`, `session_id`, and `age_at_scan`, then rerun the script.")
        exit(1)
    else :
        return
     

# Get age in months from participants.tsv for a particular scan
def get_age(partDf, ageUnits, participant_label, ses):
    
    partAge = partDf[(partDf["subject_id"] == participant_label) & (partDf["session_id"] == ses)]["age_at_scan"].to_string(index=False)
    partAge = float(partAge)
	
    if ageUnits == "m":
        return partAge
		
    else:
        return convert_age_to_months(partAge, ageUnits)


# Convert age from days/years to months	
def convert_age_to_months(age, ageUnits):

	if ageUnits == "d":
		return (age/365.25)*12
		
	elif ageUnits == "y":
		return age * 12


# Get scan name
def get_scan_name(scan):

    # Use regular expression to remove .nii or .nii.gz
    scan_name = re.sub(r'\.nii(\.gz)?$', '', scan)
    return scan_name

def run_recon_all_clinical(out_recon_all_clinical, scan_name, scanPath, participant_label):

    print("============================")
    print("Running recon-all-clinical on ", scan_name)
    print()

    subjs_dir_clinical = os.path.join(out_recon_all_clinical, scan_name)
    if not op.exists(subjs_dir_clinical):
        os.makedirs(subjs_dir_clinical)
    
    command = ["recon-all-clinical.sh", scanPath, participant_label, "1", subjs_dir_clinical]
    result = subprocess.run(command)
    
    print(' '.join(command))

    if result.returncode!=0 :
        print("recon-all-clinical did not run for scan : ", scan_name)
        print()
    else:
        print("Done!")

    print("============================")
    print()


def run_recon_all(out_recon_all, scan_name, inFn, subID):

    print("============================")
    print("Running recon-all on ", scan_name)
    print()

    subjs_dir_reconall = os.path.join(out_recon_all, scan_name)
    if not op.exists(subjs_dir_reconall):
        os.makedirs(subjs_dir_reconall)

    target = os.getenv("FREESURFER_HOME") + "/subjects/fsaverage"
    command = ["recon-all", "-sd", subjs_dir_reconall, "-i", inFn, "-s", subID, "-all", "-target", target]
    result = subprocess.run(command)

    print(' '.join(command))

    if result.returncode!=0 :
        print("recon-all did not run for scan : ", scan_name)
        print()
    else:
        print("Done!")

    print("============================")
    print()



def main():

    args = cli().parse_args()

    # Sanity checks and preparations: --------------------------------------------
    if args.participant_label:
        if "sub-" == args.participant_label[0:4]:
            participant_label = args.participant_label
        else:
            participant_label = "sub-" + args.participant_label

    print("participant: " + participant_label)

    # Check for participants.tsv
    partPath = os.path.join(args.input_dir, "participants.tsv")
    if op.exists(partPath) is False:
        print()
        exit(1)

    # Read participants.tsv file
    partDf = pd.read_csv(partPath, sep="\t")
	
    # Check column names for participants.tsv
    check_col_names(partDf)

    # Set the FS_LICENSE environment variable to point to the license file
    os.environ['FS_LICENSE'] = args.license

    # check and make output dir:
    if op.exists(args.output_dir) is False:
        os.makedirs(args.output_dir)

    dir_4analysis = os.path.join(args.input_dir, participant_label)
    #print(dir_4analysis)
    sessions = [ses for ses in os.listdir(dir_4analysis) if op.isdir(op.join(dir_4analysis,ses))] # Gets sessions
    #print(sessions)

    # Check scans to be processed using infantFS and recon-all:
    types_to_process = []
    if args.t1w is True:
        types_to_process.append("T1w")
    if args.t2w is True:
        types_to_process.append("T2w")
    if args.flair is True:
        types_to_process.append("FLAIR")
    if args.mprage is True:
        types_to_process.append("MPRAGE")

    if len(types_to_process)==0:
        print("Please specify the type of scans you would like to process (--t1w, --t2w, --flair or --mprage) and try again.")
        exit(1)

    # recon-all
    recon_all = "fs7.4.1_recon_all"
    out_recon_all = op.join(args.output_dir, recon_all)
    if op.exists(out_recon_all) is False:
        os.makedirs(out_recon_all)

    # recon-all-cliinical
    recon_all_clinical = "fs7.4.1_recon_all_clinical"
    out_recon_all_clinical = op.join(args.output_dir, recon_all_clinical)
    if op.exists(out_recon_all_clinical) is False:
        os.makedirs(out_recon_all_clinical)

    for ses in sessions :
        sesPath = op.join(dir_4analysis, ses)
        if "anat" in os.listdir(sesPath):
            anatPath = op.join(sesPath, "anat")
            # Get all anat scans
            all_scans = [fn for fn in os.listdir(anatPath) if (".nii" in fn or ".nii.gz" in fn)]
            # Get only the scans we wish to process using ifs and recon-all
            scans_chosen = [fn for fn in os.listdir(anatPath) if (any(x.lower() in fn.lower() for x in types_to_process) and (".nii" in fn or ".nii.gz" in fn))]
        else :
            continue
        for scan in all_scans:
            print("--------------------- Working on scan : ", scan, " ---------------------")
            scanPath = op.join(anatPath, scan)
            age = get_age(partDf, args.age_units, participant_label, ses)

            # Run recon-all-clinical irrespective of age
            run_recon_all_clinical(out_recon_all_clinical, get_scan_name(scan), scanPath, participant_label)


            if (age>(2*12)) and (scan in scans_chosen):
                run_recon_all(out_recon_all, get_scan_name(scan), scanPath, participant_label)


if __name__ == "__main__":
    main()