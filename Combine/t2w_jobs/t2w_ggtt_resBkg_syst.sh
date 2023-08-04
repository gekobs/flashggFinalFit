#!/bin/bash

cd /home/users/azecchin/Analysis/BiasStudy/CMSSW_10_2_13/src/flashggFinalFit/Combine

eval `scramv1 runtime -sh`

text2workspace.py Datacard.txt -o Datacard_ggtt_resBkg_syst.root -m 125 higgsMassRange=122,128 -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel   --PO "map=.*/ttHHggbb.*:r[1,0,2]"   --PO "map=.*/ttHHggWW.*:r[1,0,2]"   --PO "map=.*/ttHHggTauTau.*:r[1,0,2]"