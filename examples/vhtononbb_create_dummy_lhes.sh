#!/bin/bash

MASSPOINTS="125" #200 is already created

for MASS in ${MASSPOINTS}; do
    mkdir -p /hadoop/cms/store/user/phchang/metis/private/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8_PRIVATE-TEST-RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6_ext1-v1/lhe/;
    for i in $(seq 1 10); do
        echo "Dummy lhe file for metis to pick up" > /hadoop/cms/store/user/phchang/metis/private/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8_PRIVATE-TEST-RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6_ext1-v1/lhe/events_$i.lhe;
    done
done

