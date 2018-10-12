#!/bin/env python

import dis_client


#############################################################
def main():

    get_parent_dataset_name()

#############################################################
# Input  : dataset name (e.g. "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8...../MINIAODSIM")
# Output : parent dataset_name (e.g. "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8...../AODSIM")
def get_parent_dataset_name():

    # Get the driver
    dataset_name = "/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8/RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/MINIAODSIM"
    driver = get_driver(dataset_name)

    # Grep the line with the tag "--filein"
    return get_input_dataset_name(driver)

#############################################################
# Input  : driver command of a dataset
# Output : strips the input used for "--filein" option when cmsDriver.py was called
# Error  : Checks whether "--filein" exists
# Note   : The --filein format assumes of the form "dbs:/DATASETNAME"
#                        i.e. important chars -->  ^^^^^            ^
def get_input_dataset_name(driver):

    cmsDriverCommand = ""
    # Grep the line with the tag "--filein"
    for line in driver.split("\n"):
        if line.find("--filein") != -1:
             cmsDriverCommand = line

    if cmsDriverCommand == "":
        print "ERROR - Failed to find a line with '--filein' option"
        print "The cmsDriver command string that was used to search was :"
        print driver
        sys.exit(256)

    return cmsDriverCommand.rsplit("--filein")[1].rsplit("--")[0].strip()[5:-1]

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

    return cmsDriver


if __name__ == "__main__":

    main()
