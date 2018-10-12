#!/bin/env python

import dis_client
import sys

DEBUG=False

#############################################################
def main():

    dataset_name = "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8/RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/MINIAODSIM"

    all_drivers = get_all_drivers(dataset_name)

    script_string = chain_all_drivers_into_script(all_drivers, 10)

    script_string = reroute_pileup_input_to_cached_files(script_string)

    get_condor_executable_script_string(script_string)

#############################################################
# Input : chained script string
# Output : pileup_input option replaced with local files in order to not time out in DAS query
def reroute_pileup_input_to_cached_files(script_string):

    pileup_caches = {
        "    --pileup_input \"dbs:/Neutrino_E-10_gun/RunIISpring15PrePremix-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v2-v2/GEN-SIM-DIGI-RAW\" \\" : "    --pileup_input \"file:/hadoop/cms/store/user/mliu/pileupfile/summer16_fullsim.root\" \\"
    }

    rtn_str_list = []
    for line in script_string.split("\n"):
        if "--pileup_input" in line:
            if line in pileup_caches:
                rtn_str_list.append(pileup_caches[line])
            else:
                print "ERROR - Failed to find a local cache for the pileup input"
                print line
                sys.exit(259)
        else:
            rtn_str_list.append(line)

    return "\n".join(rtn_str_list)

#############################################################
# Input  : list of all driver commands, Nevents to generate
# Output : chained driver command
#
# The idea is to use the "fileout, filein, datatier" options as keys to identify how to chain up the intermediate files
# Then a complete script will be obtained
#
def chain_all_drivers_into_script(all_drivers, nevents=500):

    # Just in case it was not formatted previously
    formatted_all_drivers = []
    for driver in all_drivers:
        formatted_all_drivers.append(format_driver(driver))

    # First chain all the driver as is
    chained_driver = chain_driver_with_cmsRun_commands(formatted_all_drivers)

    # Get all the lines to mod as well as the datatiers (e.g. LHE, AOD, MINIAOD, etc.)
    lines_to_mod = []
    datatiers = []
    for line in chained_driver.split("\n"):
        if "fileout" in line: lines_to_mod.append(line)
        if "filein" in line: lines_to_mod.append(line)
        if "datatier" in line: datatiers.append(line.split()[1])

    # Get the modded lines
    modded_lines = []
    for index, line in enumerate(lines_to_mod):
        filename = "file:file_%s.root" % (datatiers[index/2])
        ls = line.split()
        ls[1] = filename
        modded_lines.append("    %s" % (" ".join(ls)))

    # Now replace the lines with modded lines
    modded_chained_driver = []
    for line in chained_driver.split("\n"):
        if "fileout" in line or "filein" in line:
            modded_chained_driver.append(modded_lines.pop(0))
        elif " -n " in line:
            ls = line.split()
            ls[1] = "%d" % nevents
            modded_chained_driver.append("    %s" % (" ".join(ls)))
        else:
            modded_chained_driver.append(line)

    return "\n".join(modded_chained_driver)

#############################################################
# Input  : list of drivers
# Output : single string with a cmsRun command sandwiched in between driver commands
# Note   : It is important that the "sandwich" position is key'ed by " || exit $?" string and " -n "
#          FIXME:The above condition could be finicky!
def chain_driver_with_cmsRun_commands(all_drivers):

    # Just in case it was not formatted previously
    formatted_all_drivers = []
    for driver in all_drivers:
        formatted_all_drivers.append(format_driver(driver))

    chained_driver = "\n".join(formatted_all_drivers)

    chained_driver_with_cmsRun = []
    for line in chained_driver.split("\n"):

        # First add the line to the final list
        chained_driver_with_cmsRun.append(line)

        # Then be on the lookout for the --python_filename option
        if "--python_filename" in line:
            cfgname = line.split()[1]

        # Then be on the lookout for the --datatier option
        if "--datatier" in line:
            datatier = line.split()[1]

        # If the line we just added is the last line of the cmsDriver.py then sandwich it by cmsRun
        if " || exit $?" in line and " -n " in line:
            chained_driver_with_cmsRun.append("cmsRun -e -j %s.xml %s" % (datatier, cfgname))

    return "\n".join(chained_driver_with_cmsRun)

#############################################################
# Input : driver
# Output : datatier
# Error : If --datatier not found throws error
# Note : The driver command must be formatted if it has not been formatted yet
# e.g. the line would look like this "    --datatier MINIAODSIM \"
def get_datatier(driver):

    # Just in case the driver is not formatted
    driver = format_driver(driver)

    datatier = ""
    for line in driver.split("\n"):
        if "datatier" in line:
            datatier = line

    if datatier == "":
        print "ERROR - Failed to find a line with '--datatier' option"
        print "The cmsDriver command string that was used to search was :"
        print driver
        sys.exit(257)

    return datatier.split()[-2].strip()

#############################################################
# Input  : dataset name (e.g. "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8...../MINIAODSIM")
# Output : list of driver commands
def get_all_drivers(dataset_name, output=[]):

    # Append to the output list the current dataset's driver command
    output.append(get_driver(dataset_name))

    if DEBUG:
        for i in output:
            print i

    # If the current dataset is the "end point" (i.e. LHE step) then stop.
    if is_LHE_dataset(dataset_name):
        output.reverse() # return in reverse order to have them in proper order
        return output

    if DEBUG: print "checking parent of %s" % dataset_name

    # Otherwise, continue one step upward
    parent_dataset_name = get_parent_dataset_name(dataset_name)

    if DEBUG: print "retrieved parent of %s" % parent_dataset_name

    return get_all_drivers(parent_dataset_name, output)

#############################################################
# Input  : dataset name (e.g. "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8/RunIIWinter15wmLHE-MCRUN2_71_V1-v1/LHE")
# Output : Is this LHE stage? (i.e. no parent to look for)
# Note   : Assumes LHE datasets have "/LHE" strings
def is_LHE_dataset(dataset_name):

    if "/LHE" in dataset_name:
        return True
    else:
        return False

#############################################################
# Input  : dataset name (e.g. "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8...../MINIAODSIM")
# Output : parent dataset_name (e.g. "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8...../AODSIM")
def get_parent_dataset_name(dataset_name):

    # Get the driver
    driver = get_driver(dataset_name)

    # Grep the line with the tag "--filein"
    return get_input_dataset_name(driver)

#############################################################
# Input  : driver command of a dataset
# Output : strips the input used for "--filein" option when cmsDriver.py was called
# Error  : Checks whether "--filein" exists
# Note   : The --filein format assumes of the form "dbs:/DATASETNAME" \
#                        i.e. important chars -->  ^^^^^            ^^^
#          Another thing to note is that some driver command has multiple steps.
#          In such cases, make sure to get the first one.
def get_input_dataset_name(driver):

    # Just in case it was not formatted
    # It is pertinent that it is formatted as it assumes specific position (see Note above)
    driver = format_driver(driver)

    cmsDriverCommand = ""
    # Grep the line with the tag "--filein"
    for line in driver.split("\n"):
        if "--filein" in line:
             cmsDriverCommand = line
             break

    if cmsDriverCommand == "":
        print "ERROR - Failed to find a line with '--filein' option"
        print "The cmsDriver command string that was used to search was :"
        print driver
        sys.exit(256)

    return cmsDriverCommand.rsplit("--filein")[1].rsplit("\\")[0].strip()[5:-1]

#############################################################
# Input  : dataset name (e.g. "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8...../MINIAODSIM")
# Output : driver command in string
# Error  : Checks whether dis_client gave proper response
def get_driver(dataset_name):

    # Get the query data
    query = dataset_name + ",this"
    data = dis_client.query(query, typ="driver")

    # Check the query data status
    if data["response"]["status"] != "success":
        print "ERROR - Query failed!"
        print "Check your dataset_name = %s" % (dataset_name)
        sys.exit(255)

    # Get the driver commands
    cmsDriver = data["response"]["payload"]["cmsDriver"]

    return format_driver(cmsDriver)

#############################################################
# Input : Driver command
# Output : Same driver command but with the option lines --filein or -n into new lines
# Note : Sanity check that the driver is not already formmated is done by checking backslash in the cmsDriver.py line
# e.g. The following long line :
#
# cmsDriver.py step1 --filein "dbs:/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8/RunIISummer16DR80Premix-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/AODSIM" --fileout file:SUS-RunIISummer16MiniAODv2-00168.root --mc --eventcontent MINIAODSIM --runUnscheduled --datatier MINIAODSIM --conditions 80X_mcRun2_asymptotic_2016_TrancheIV_v6 --step PAT --nThreads 4 --era Run2_2016 --python_filename SUS-RunIISummer16MiniAODv2-00168_1_cfg.py --no_exec --customise Configuration/DataProcessing/Utils.addMonitoring -n 5760 || exit $? ;
#
# vs.
#
# cmsDriver.py step1 \
#     --filein "dbs:/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8/RunIISummer16DR80Premix-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/AODSIM" \
#     --fileout file:SUS-RunIISummer16MiniAODv2-00168.root \
#     --mc \
#     --eventcontent MINIAODSIM \
#     --runUnscheduled \
#     --datatier MINIAODSIM \
#     --conditions 80X_mcRun2_asymptotic_2016_TrancheIV_v6 \
#     --step PAT \
#     --nThreads 4 \
#     --era Run2_2016 \
#     --python_filename SUS-RunIISummer16MiniAODv2-00168_1_cfg.py \
#     --no_exec \
#     --customise Configuration/DataProcessing/Utils.addMonitoring \
#     -n 5760 || exit $? ;
#
def format_driver(driver):

    if is_driver_formatted(driver):
        return driver

    rtn_str_list = []
    for line in driver.split("\n"):

        # If the line contains "cmsDriver.py" it's the line that creates the configuration driver
        if "cmsDriver.py" in line:

            # Split the cmsDriver command line by options
            items = line.split(" -")

            for index, item in enumerate(items):

                # First item does not get the extra "    -"
                if index == 0:
                    rtn_str_list.append(item + " \\")
                # Last item  does not get the \
                elif index == len(items) - 1:
                    rtn_str_list.append("    -" + item)
                # The rest gets the "    -" and the \
                else:
                    rtn_str_list.append("    -" + item + " \\")

        else:
            rtn_str_list.append(line)

    return "\n".join(rtn_str_list)


#############################################################
# Input : Driver command
# Output : Same driver command but with the option lines --filein or -n into new lines
# Error : If no "cmsDriver.py" found the error is thrown
# Note : Sanity check that the driver is not already formmated is done by checking backslash in the cmsDriver.py line
#
def is_driver_formatted(driver):
    for line in driver.split("\n"):
        # If the line contains "cmsDriver.py" it's the line that creates the configuration driver
        if "cmsDriver.py" in line:
            if "\\" in line:
                return True
            else:
                return False

    print "ERROR - Failed to find a line with 'cmsDriver.py'"
    print "The cmsDriver command string that was used to search was :"
    print driver
    sys.exit(258)

#############################################################
# Input : local command script
# Output : condor-ready executable
def get_condor_executable_script_string(script_string):

    # Print the header portion of the executable
    print condor_executable_header

    # The final output file to be copied via gfal-copy
    final_output_file = ""

    # Also save the .xml output paths so we can print out status
    xml_outputs = []

    # Loop over the lines and print out the scripts from the local files with few additional lines depending on the --datatier
    for line in script_string.split("\n"):

        # For condor jobs, use only one 1 cpu per node
        if "--nThreads" in line: continue

        # The run number and random seeds needs to be customized for each condor jobs.
        # The special strings defined in customise_commands_<type> global string contains the necessary modifications.
        # So as we print out the lines we add a lines depending on the conditions

        # If LHE and not GEN-SIM then print customise_commands_LHE
        if "--datatier" in line and "LHE" in line and "GEN-SIM" not in line:
            print customise_commands_LHE
            print line
        # If not LHE and GEN-SIM then print customise_commands_GS
        elif "--datatier" in line and "LHE" not in line and "GEN-SIM" in line:
            # double check whether it's GEN-SIM and not GEN-SIM-RAW (n.b. there are GEN-SIM and also GEN-SIM-RAW while we need customise commands for GEN-SIM only)
            ls = line.split()[1].split(",")
            if "GEN-SIM" in ls:
                print customise_commands_GS
                print line
            else:
                print line
        # If LHE and GEN-SIM then print customise_commands_LHEGS
        elif "--datatier" in line and "LHE" in line and "GEN-SIM" in line:
            print customise_commands_LHEGS
            print line
        else:
            print line

        # As we go through the lines we also pick up the "FINALOUTPUT" root file to be gfal-copied
        if "--fileout" in line:
            final_output_file = line.split()[1][5:]


        # As we go through the lines we pick up the .xml paths
        if "cmsRun " in line:
            xml_outputs.append(line.split()[3])

    # Set the final output file as FINALOUTPUT environment variable which will be used in the condor_executable_trailer to gfal-copy
    print "FINALOUTPUT=%s \n" % (final_output_file)

    for xml in xml_outputs:
        print """
# Printing out some information about the result of each step
XML=%s
echo "getting stats from "${XML}
grep "TotalEvents" ${XML}
grep "Timing-tstoragefile-write-totalMegabytes"  ${XML}
grep "PeakValueRss" ${XML}
grep "AvgEventTime" ${XML}
grep "AvgEventCPU"  ${XML}
grep "TotalJobCPU"  ${XML}
grep "EventThroughput" ${XML}
""" % xml

    # Add the gfal-copy portion
    print condor_executable_trailer

#### Global "const" strings hard-coded for the mods needed for condor executable 

customise_commands_GS    = "    --customise_commands \"process.source.numberEventsInLuminosityBlock = cms.untracked.uint32(50) \\n process.source.firstRun = cms.untracked.uint32(${JOBNUM})\" \\"
customise_commands_LHE   = "    --customise_commands \"process.RandomNumberGeneratorService.externalLHEProducer.initialSeed = ${RANDOMSEED}\" \\"
customise_commands_LHEGS = "    --customise_commands \"process.source.numberEventsInLuminosityBlock = cms.untracked.uint32(50) \\n process.source.firstRun = cms.untracked.uint32(${JOBNUM}) \\n process.RandomNumberGeneratorService.externalLHEProducer.initialSeed = ${RANDOMSEED}\" \\"

condor_executable_header = """
#!/bin/bash

PACKAGE=package.tar.gz

# Echo exact command
echo "$(basename $0) $*"


###################################################################################################
# ProjectMetis/CondorTask specific (Setting up some common environment)
###################################################################################################
#echo "To check whether it's on condor universe Vanilla or Local. The following variables are used."
#echo "If _CONDOR_SLOT is set, it's on Vanilla"
#echo "If X509_USER_PROXY is set, it's either on Vanilla or Local."
# if 
if [ "x${_CONDOR_JOB_AD}" == "x" ]; then
    :
    INPUTFILENAMES=$1
    shift;
else
    hostname
    uname -a
    date
    whoami
    pwd
    echo "ls'ing hadoop"
    ls -lh /hadoop/cms/store/user/phchang/
    echo "_CONDOR_SLOT" ${_CONDOR_SLOT}
    echo "X509_USER_PROXY" ${X509_USER_PROXY}
    echo "_CONDOR_SCRATCH_DIR"             ${_CONDOR_SCRATCH_DIR}
    echo "_CONDOR_SLOT"                    ${_CONDOR_SLOT}
    echo "CONDOR_VM"                       ${CONDOR_VM}
    echo "X509_USER_PROXY"                 ${X509_USER_PROXY}
    echo "_CONDOR_JOB_AD"                  ${_CONDOR_JOB_AD}
    echo "_CONDOR_MACHINE_AD"              ${_CONDOR_MACHINE_AD}
    echo "_CONDOR_JOB_IWD"                 ${_CONDOR_JOB_IWD}
    echo "_CONDOR_WRAPPER_ERROR_FILE"      ${_CONDOR_WRAPPER_ERROR_FILE}
    echo "CONDOR_IDS"                      ${CONDOR_IDS}
    echo "CONDOR_ID"                       ${CONDOR_ID}
    OUTPUTDIR=$1
    OUTPUTNAME=$2
    INPUTFILENAMES=$3
    IFILE=$4
    CMSSWVERSION=$5
    SCRAMARCH=$6
    if [ "x${_CONDOR_SLOT}" == "x" ]; then
        WORKDIR=/tmp/phchang_condor_local_${OUTPUTDIR//\//_}_${OUTPUTNAME}_${IFILE}
        mkdir -p ${WORKDIR}
        ls
        cp package.tar.gz ${WORKDIR}
        cd ${WORKDIR}
        ls
        echo "This is in Condor session with Universe=Local."
        echo "WORKDIR=${WORKDIR}"
        echo "pwd"
        pwd
    fi
    echo "OUTPUTDIR     : $1"
    echo "OUTPUTNAME    : $2"
    echo "INPUTFILENAMES: $3"
    echo "IFILE         : $4"
    echo "CMSSWVERSION  : $5"
    echo "SCRAMARCH     : $6"
    shift 6
    #tar xvzf package.tar.gz
    #if [ $? -eq 0 ]; then
    #    echo "Successfully untarred package."
    #    :
    #else
    #    echo "Failed to untar package."
    #    exit
    #fi
fi
###################################################################################################

#OUTPUTDIR=$1
#OUTPUTNAME=$2
#INPUTFILENAMES=$3
#IFILE=$4
#CMSSWVERSION=$5
#SCRAMARCH=$6

OUTDIR=${OUTPUTDIR}
OUTPUT=${OUTPUTNAME}
JOBNUM=${IFILE}
RANDOMSEED=123${IFILE}
TAG=""

if [ -z ${OUTDIR} ]; then usage; fi
if [ -z ${OUTPUT} ]; then usage; fi
if [ -z ${JOBNUM} ]; then usage; fi
if [ -z ${RANDOMSEED} ]; then usage; fi

# Verbose
date
echo "================================================"
echo "$(basename $0) $*"
echo "$(basename $0) $*" >> $DIR/.$(basename $0).history
echo "------------------------------------------------"
echo "FRAGMENT          : ${FRAGMENT}"
echo "OUTDIR            : ${OUTDIR}"
echo "OUTPUT            : ${OUTPUT}"
echo "JOBNUM            : ${JOBNUM}"
echo "RANDOMSEED        : ${RANDOMSEED}"
echo "CMSSWVERSION      : ${CMSSWVERSION}"
echo "TAG               : ${TAG}"
echo "================================================"


"""

condor_executable_trailer = """
# For copying outputs when using some older CMSSW this stupid thing needs to be loaded
export LD_PRELOAD=/usr/lib64/gfal2-plugins//libgfal_plugin_xrootd.so 

gfal-copy -p -f -t 4200 --verbose file://`pwd`/${FINALOUTPUT} gsiftp://gftp.t2.ucsd.edu/${OUTPUTDIR}/${OUTPUTNAME}_${IFILE}.root --checksum ADLER32
echo "Bye."

date
"""



if __name__ == "__main__":

    main()
