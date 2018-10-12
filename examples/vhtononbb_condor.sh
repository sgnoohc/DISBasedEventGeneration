
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
    tar xvzf package.tar.gz
    if [ $? -eq 0 ]; then
        echo "Successfully untarred package."
        :
    else
        echo "Failed to untar package."
        exit
    fi
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




#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc6_amd64_gcc481
if [ -r CMSSW_7_1_16_patch2/src ] ; then 
 echo release CMSSW_7_1_16_patch2 already exists
else
scram p CMSSW CMSSW_7_1_16_patch2
fi
cd CMSSW_7_1_16_patch2/src
eval `scram runtime -sh`

curl -s --insecure https://cms-pdmv.cern.ch/mcm/public/restapi/requests/get_fragment/SUS-RunIIWinter15wmLHE-00052 --retry 2 --create-dirs -o Configuration/GenProduction/python/SUS-RunIIWinter15wmLHE-00052-fragment.py 
[ -s Configuration/GenProduction/python/SUS-RunIIWinter15wmLHE-00052-fragment.py ] || exit $?;

scram b
cd ../../
cmsDriver.py Configuration/GenProduction/python/SUS-RunIIWinter15wmLHE-00052-fragment.py \
    --fileout file:file_LHE.root \
    --mc \
    --eventcontent LHE \
    --customise_commands "process.RandomNumberGeneratorService.externalLHEProducer.initialSeed = ${RANDOMSEED}" \
    --datatier LHE \
    --conditions MCRUN2_71_V1::All \
    --step LHE \
    --python_filename SUS-RunIIWinter15wmLHE-00052_1_cfg.py \
    --no_exec \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    -n 10 || exit $? ;
cmsRun -e -j LHE.xml SUS-RunIIWinter15wmLHE-00052_1_cfg.py



#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc6_amd64_gcc481
if [ -r CMSSW_7_1_18/src ] ; then 
 echo release CMSSW_7_1_18 already exists
else
scram p CMSSW CMSSW_7_1_18
fi
cd CMSSW_7_1_18/src
eval `scram runtime -sh`

curl -s --insecure https://cms-pdmv.cern.ch/mcm/public/restapi/requests/get_fragment/SUS-RunIISummer15GS-00050 --retry 2 --create-dirs -o Configuration/GenProduction/python/SUS-RunIISummer15GS-00050-fragment.py 
[ -s Configuration/GenProduction/python/SUS-RunIISummer15GS-00050-fragment.py ] || exit $?;

scram b
cd ../../
cmsDriver.py Configuration/GenProduction/python/SUS-RunIISummer15GS-00050-fragment.py \
    --filein file:file_LHE.root \
    --fileout file:file_GEN-SIM.root \
    --mc \
    --eventcontent RAWSIM \
    --customise SLHCUpgradeSimulations/Configuration/postLS1Customs.customisePostLS1,Configuration/DataProcessing/Utils.addMonitoring \
    --customise_commands "process.source.numberEventsInLuminosityBlock = cms.untracked.uint32(50) \n process.source.firstRun = cms.untracked.uint32(${JOBNUM})" \
    --datatier GEN-SIM \
    --conditions MCRUN2_71_V1::All \
    --beamspot Realistic50ns13TeVCollision \
    --step GEN,SIM \
    --magField 38T_PostLS1 \
    --python_filename SUS-RunIISummer15GS-00050_1_cfg.py \
    --no_exec \
    -n 10 || exit $? ;
cmsRun -e -j GEN-SIM.xml SUS-RunIISummer15GS-00050_1_cfg.py



#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc6_amd64_gcc530
if [ -r CMSSW_8_0_21/src ] ; then 
 echo release CMSSW_8_0_21 already exists
else
scram p CMSSW CMSSW_8_0_21
fi
cd CMSSW_8_0_21/src
eval `scram runtime -sh`


scram b
cd ../../
cmsDriver.py step1 \
    --filein file:file_GEN-SIM.root \
    --fileout file:file_GEN-SIM-RAW.root \
    --pileup_input "file:/hadoop/cms/store/user/mliu/pileupfile/summer16_fullsim.root" \
    --mc \
    --eventcontent PREMIXRAW \
    --datatier GEN-SIM-RAW \
    --conditions 80X_mcRun2_asymptotic_2016_TrancheIV_v6 \
    --step DIGIPREMIX_S2,DATAMIX,L1,DIGI2RAW,HLT:@frozen2016 \
    --nThreads 4 \
    --datamix PreMix \
    --era Run2_2016 \
    --python_filename SUS-RunIISummer16DR80Premix-00125_1_cfg.py \
    --no_exec \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    -n 10 || exit $? ;
cmsRun -e -j GEN-SIM-RAW.xml SUS-RunIISummer16DR80Premix-00125_1_cfg.py

cmsDriver.py step2 \
    --filein file:file_GEN-SIM-RAW.root \
    --fileout file:file_AODSIM.root \
    --mc \
    --eventcontent AODSIM \
    --runUnscheduled \
    --datatier AODSIM \
    --conditions 80X_mcRun2_asymptotic_2016_TrancheIV_v6 \
    --step RAW2DIGI,RECO,EI \
    --nThreads 4 \
    --era Run2_2016 \
    --python_filename SUS-RunIISummer16DR80Premix-00125_2_cfg.py \
    --no_exec \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    -n 10 || exit $? ;
cmsRun -e -j AODSIM.xml SUS-RunIISummer16DR80Premix-00125_2_cfg.py



#!/bin/bash
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc6_amd64_gcc530
if [ -r CMSSW_8_0_21/src ] ; then 
 echo release CMSSW_8_0_21 already exists
else
scram p CMSSW CMSSW_8_0_21
fi
cd CMSSW_8_0_21/src
eval `scram runtime -sh`


scram b
cd ../../
cmsDriver.py step1 \
    --filein file:file_AODSIM.root \
    --fileout file:file_MINIAODSIM.root \
    --mc \
    --eventcontent MINIAODSIM \
    --runUnscheduled \
    --datatier MINIAODSIM \
    --conditions 80X_mcRun2_asymptotic_2016_TrancheIV_v6 \
    --step PAT \
    --nThreads 4 \
    --era Run2_2016 \
    --python_filename SUS-RunIISummer16MiniAODv2-00168_1_cfg.py \
    --no_exec \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    -n 10 || exit $? ;
cmsRun -e -j MINIAODSIM.xml SUS-RunIISummer16MiniAODv2-00168_1_cfg.py


FINALOUTPUT=file_MINIAODSIM.root 


# Printing out some information about the result of each step
XML=LHE.xml
echo "getting stats from "${XML}
grep "TotalEvents" ${XML}
grep "Timing-tstoragefile-write-totalMegabytes"  ${XML}
grep "PeakValueRss" ${XML}
grep "AvgEventTime" ${XML}
grep "AvgEventCPU"  ${XML}
grep "TotalJobCPU"  ${XML}
grep "EventThroughput" ${XML}


# Printing out some information about the result of each step
XML=GEN-SIM.xml
echo "getting stats from "${XML}
grep "TotalEvents" ${XML}
grep "Timing-tstoragefile-write-totalMegabytes"  ${XML}
grep "PeakValueRss" ${XML}
grep "AvgEventTime" ${XML}
grep "AvgEventCPU"  ${XML}
grep "TotalJobCPU"  ${XML}
grep "EventThroughput" ${XML}


# Printing out some information about the result of each step
XML=GEN-SIM-RAW.xml
echo "getting stats from "${XML}
grep "TotalEvents" ${XML}
grep "Timing-tstoragefile-write-totalMegabytes"  ${XML}
grep "PeakValueRss" ${XML}
grep "AvgEventTime" ${XML}
grep "AvgEventCPU"  ${XML}
grep "TotalJobCPU"  ${XML}
grep "EventThroughput" ${XML}


# Printing out some information about the result of each step
XML=AODSIM.xml
echo "getting stats from "${XML}
grep "TotalEvents" ${XML}
grep "Timing-tstoragefile-write-totalMegabytes"  ${XML}
grep "PeakValueRss" ${XML}
grep "AvgEventTime" ${XML}
grep "AvgEventCPU"  ${XML}
grep "TotalJobCPU"  ${XML}
grep "EventThroughput" ${XML}


# Printing out some information about the result of each step
XML=MINIAODSIM.xml
echo "getting stats from "${XML}
grep "TotalEvents" ${XML}
grep "Timing-tstoragefile-write-totalMegabytes"  ${XML}
grep "PeakValueRss" ${XML}
grep "AvgEventTime" ${XML}
grep "AvgEventCPU"  ${XML}
grep "TotalJobCPU"  ${XML}
grep "EventThroughput" ${XML}


# For copying outputs when using some older CMSSW this stupid thing needs to be loaded
export LD_PRELOAD=/usr/lib64/gfal2-plugins//libgfal_plugin_xrootd.so 

gfal-copy -p -f -t 4200 --verbose file://`pwd`/${FINALOUTPUT} gsiftp://gftp.t2.ucsd.edu/${OUTPUTDIR}/${OUTPUTNAME}_${IFILE}.root --checksum ADLER32
echo "Bye."

date

