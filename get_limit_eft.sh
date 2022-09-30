#!/usr/bin/env bash

set -x

source /cvmfs/cms.cern.ch/cmsset_default.sh
# source /vols/grid/cms/setup.sh

tag=HEFT_BRggbb
trees=/home/users/azecchin/Analysis/FinalFit/CMSSW_10_2_13/src/flashggFinalFit/files_systs/$tag

cmsenv
source setup.sh

model_bkg(){
  pushd Trees2WS
    python trees2ws_data.py --inputConfig syst_config_ggtt.py --inputTreeFile $trees/Data/allData.root
  popd

  pushd Background
    rm -rf outdir_$tag
    sed -i "s/dummy/${tag}/g" config_ggtt.py

    python RunBackgroundScripts.py --inputConfig config_ggtt.py --mode fTestParallel

    sed -i "s/${tag}/dummy/g" config_ggtt.py
  popd
}


#Construct Signal Models (one per year)
model_sig(){
  procs=( "VH" "ggH" "VBFH" "ttH" "ttHHheftSM" "ttHHheft1" "ttHHheft2" "ttHHheft3" "ttHHheft4" "ttHHheft5" "ttHHheft6" "ttHHheft7" "ttHHheft8" "ttHHheft9" "ttHHheft10" "ttHHheft11" "ttHHheft12" "ttHHheft13" )
  
  for year in 2016 2017 2018
  # for year in 2018
  do
    rm -rf $trees/ws_signal_$year
    mkdir -p $trees/ws_signal_$year
    for proc in "${procs[@]}"
    do

      rm -rf $trees/$year/ws_$proc

      pushd Trees2WS
        python trees2ws.py --inputConfig syst_config_ggtt.py --inputTreeFile $trees/$year/${proc}_125_13TeV.root --inputMass 125 --productionMode $proc --year $year --doSystematics
      popd

      mv $trees/$year/ws_$proc/${proc}_125_13TeV_$proc.root $trees/ws_signal_$year/output_${proc}_M125_13TeV_pythia8_${proc}.root 

    done

    pushd Signal
     rm -rf outdir_${tag}_$year
     sed -i "s/dummy/${tag}/g" syst_config_ggtt_${year}_eft.py

     python RunSignalScripts.py --inputConfig syst_config_ggtt_${year}_eft.py --mode fTest --modeOpts "--doPlots"
     python RunSignalScripts.py --inputConfig syst_config_ggtt_${year}_eft.py --mode calcPhotonSyst
     python RunSignalScripts.py --inputConfig syst_config_ggtt_${year}_eft.py --mode signalFit --groupSignalFitJobsByCat --modeOpts "--skipVertexScenarioSplit " 

     sed -i "s/${tag}/dummy/g" syst_config_ggtt_${year}_eft.py
    popd
  done

  pushd Signal
    rm -rf outdir_packaged
    python RunPackager.py --cats SR1 --exts ${tag}_2016,${tag}_2017,${tag}_2018 --batch local --massPoints 125 --mergeYears
    python RunPlotter.py --procs all --cats SR1 --years 2016,2017,2018 --ext packaged
    python RunPackager.py --cats SR2 --exts ${tag}_2016,${tag}_2017,${tag}_2018 --batch local --massPoints 125 --mergeYears
    python RunPlotter.py --procs all --cats SR2 --years 2016,2017,2018 --ext packaged
  popd
}

make_datacard(){
  # mkdir -p /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/EFT_cards
  # mkdir -p /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/EFT_cards/${tag}
  mkdir -p /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/C2_cards
  mkdir -p /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/C2_cards/${tag}
  pushd Datacard
   rm -rf yields_$tag

  #  procs=( "ttHHheftSM" "ttHHheft1" "ttHHheft2" "ttHHheft3" "ttHHheft4" "ttHHheft5" "ttHHheft6" "ttHHheft7" "ttHHheft8" "ttHHheft9" "ttHHheft10" "ttHHheft11" "ttHHheft12" "ttHHheft13" )
  #  #procs=("ggHHbm4")
  #  for proc in "${procs[@]}"
  #  do

  #   substr="ttHHheft"
  #   bm_tag=${proc#$substr}
  #   echo "Before run yields ${proc}"
  #   python RunYields.py --inputWSDirMap 2016=${trees}/ws_signal_2016,2017=${trees}/ws_signal_2017,2018=${trees}/ws_signal_2018 --cats auto --procs "${proc},ggH,ttH,VH,VBFH" --batch local --mergeYears --ext ${tag}"_"${bm_tag} --skipZeroes 
  #   # python RunYields.py --inputWSDirMap 2018=${trees}/ws_signal_2018 --cats auto --procs "${proc},ggH,ttH,VH,VBFH" --batch local --mergeYears --ext ${tag}"_"${bm_tag} --doSystematics --skipZeroes 
  #   python makeDatacard.py --years 2016,2017,2018 --ext ${tag}"_"${bm_tag}  --prune --pruneThreshold 0.000000001 
  #   # python prepareDatacard.py
  #   python prepareDatacard_eft.py
  #   mv Datacard_updated.txt /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/EFT_cards/${tag}/datacard_${bm_tag}.txt
  #  done
   python RunYields.py --inputWSDirMap 2016=${trees}/ws_signal_2016,2017=${trees}/ws_signal_2017,2018=${trees}/ws_signal_2018 --cats auto --procs auto --batch local --mergeYears --ext $tag --skipZeroes --doSystematics --ignore-warnings
   #python RunYields.py --inputWSDirMap 2016=${trees}/ws_signal_2016,2017=${trees}/ws_signal_2017,2018=${trees}/ws_signal_2018 --cats auto --procs "ggHHkl0kt1,ggHHkl1kt1,ggHHkl2p45kt1,ggHHkl5kt1,ggHHkl0kt1WWdilep,ggHHkl1kt1WWdilep,ggHHkl2p45kt1WWdilep,ggHHkl5kt1WWdilep,ggH,ttH,VH,VBFH" --batch local --mergeYears --ext $tag #--doSystematics --skipZeroes 
   python makeDatacard.py --years 2016,2017,2018 --ext $tag --prune --pruneThreshold 0.000000001 --doSystematics
	 python prepareDatacard.py
   mv Datacard.txt /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/C2_cards/${tag}/datacard_fixBR.txt
  popd
}

copy_files(){
    mkdir -p /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/C2_cards/${tag}/Models/
    mkdir -p /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/C2_cards/${tag}/Models/signal/
    mkdir -p /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/C2_cards/${tag}/Models/background/

    cp Signal/outdir_packaged/CMS-HGG*.root /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/C2_cards/${tag}/Models/signal/
    cp Background/outdir_$tag/CMS-HGG*.root /home/users/azecchin/Analysis/inference/datacards_run2/ttHH/C2_cards/${tag}/Models/background/
}

    # model_bkg
    # model_sig
make_datacard
copy_files
