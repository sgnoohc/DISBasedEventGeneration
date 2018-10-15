import metis
from metis.CMSSWTask import CMSSWTask
from metis.Sample import DirectorySample
from metis.Sample import DummySample
from metis.StatsParser import StatsParser
from metis.CondorTask import CondorTask
from time import sleep
import os

import numpy as np

def main():

    main_dir = os.path.dirname(os.path.abspath(__file__))
    metis_path = os.path.dirname(os.path.dirname(metis.__file__))
    exec_path = main_dir + "/metis.sh"
    hadoop_path = "metis/"
    metis_dashboard_path = os.path.join(metis_path, "dashboard")
    job_tag = ""

    total_summary = {}

    os.chdir(metis_path)

    while True:

        masspoints = [125]

        tasks = []

        for mass in masspoints:

            miniaod = CondorTask(
                    ## Dummy sample as no input is needed in generating the events
                    #sample = DummySample(
                    #    N=3000,
                    #    dataset="/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8/PRIVATE-RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6_ext1-v1/MINIAODSIM"
                    #    ),
                    # Dummy sample as no input is needed in generating the events
                    sample = DummySample(
                        N=15000,
                        dataset="/VHToNonbb_M125_13TeV_amcatnloFXFX_madspin_pythia8/PRIVATE-RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6_ext2-v1/MINIAODSIM"
                        ),
                    tag                  = job_tag,
                    executable           = exec_path,
                    special_dir          = hadoop_path + "/private_miniaod",
                    output_name          = "output.root",
                    files_per_output     = 1,
                    condor_submit_params = {"sites" : "T2_US_UCSD"},
                    open_dataset         = True,
                    flush                = True,
                    #no_load_from_backup  = True,
                    )

            tasks.extend([miniaod])

        all_tasks_complete = True
        for task in tasks:
            task.process()
            summary = task.get_task_summary()
            total_summary[task.get_sample().get_datasetname()] = summary
            all_tasks_complete = all_tasks_complete and task.complete()

        # parse the total summary and write out the dashboard
        StatsParser(data=total_summary, webdir=metis_dashboard_path).do()

        # Print msummary table so I don't have to load up website
        os.system("msummary -p ext2 | tee summary.txt")
        os.system("chmod -R 755 {}".format(metis_dashboard_path))

        # If all done exit the loop
        if all_tasks_complete:
            print ""
            print "Job={} finished".format(job_tag)
            print ""
            break

        # Neat trick to not exit the script for force updating
        print 'Press Ctrl-C to force update, otherwise will sleep for 300 seconds'
        try:
            for i in range(0,300):
                sleep(1) # could use a backward counter to be preeety :)
        except KeyboardInterrupt:
            raw_input("Press Enter to force update, or Ctrl-C to quit.")
            print "Force updating..."

if __name__ == "__main__":
    main()
