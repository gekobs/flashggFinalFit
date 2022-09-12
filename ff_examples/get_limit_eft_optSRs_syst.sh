#!/usr/bin/env bash

set -x

source /cvmfs/cms.cern.ch/cmsset_default.sh
source /vols/grid/cms/setup.sh

cmsenv
source setup.sh

bm_tag=1
#tags=( "ggtautau_sr_eft_1_21Apr2022" "ggtautau_sr_eft_2_21Apr2022" "ggtautau_sr_eft_3_21Apr2022" "ggtautau_sr_eft_4_21Apr2022" "ggtautau_sr_eft_5_21Apr2022" "ggtautau_sr_eft_6_21Apr2022" "ggtautau_sr_eft_7_21Apr2022" "ggtautau_sr_eft_8_21Apr2022" "ggtautau_sr_eft_9_21Apr2022" "ggtautau_sr_eft_10_21Apr2022" "ggtautau_sr_eft_11_21Apr2022" "ggtautau_sr_eft_12_21Apr2022" )
tags=( "ggtautau_sr_eft_1_21Apr2022" )

for tag in "${tags[@]}"
do
	trees=/home/users/fsetti/HHggTauTau/coupling_scan/CMSSW_10_2_13/src/flashggFinalFit/files_systs/$tag/v0/
	
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
		procs=( "HHggttEFT" "VH" "ggH" "VBFH" "ttH" )
		#procs=( "ggH" "VBFH" "ttH" )
	
		for year in 2016 2017 2018
		#for year in 2017
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
	    rm -rf outdir_${tag}_packaged
	    python RunPackager.py --cats SR1 --exts ${tag}_2016,${tag}_2017,${tag}_2018 --batch local --massPoints 125 --mergeYears
	    python RunPlotter.py --procs all --cats SR1 --years 2016,2017,2018 --ext ${tag}_packaged
	    python RunPackager.py --cats SR2 --exts ${tag}_2016,${tag}_2017,${tag}_2018 --batch local --massPoints 125 --mergeYears
	    python RunPlotter.py --procs all --cats SR2 --years 2016,2017,2018 --ext ${tag}_packaged
	  popd
	}
	
	make_datacard(){

		mkdir -p /home/users/fsetti/HHggTauTau/inference/datacards_run2/ggtt/EFT_cards/${tag}

	  pushd Datacard
	   rm -rf yields_$tag
	
    python RunYields.py --inputWSDirMap 2016=${trees}/ws_signal_2016,2017=${trees}/ws_signal_2017,2018=${trees}/ws_signal_2018 --cats auto --procs auto --batch local --mergeYears --ext $tag --doSystematics --skipZeroes 
    #python RunYields.py --inputWSDirMap 2016=${trees}/ws_signal_2016,2017=${trees}/ws_signal_2017,2018=${trees}/ws_signal_2018 --cats auto --procs "${proc},ggH,ttH,VH,VBFH" --batch local --mergeYears --ext ${tag}"_bm"${bm_tag} --doSystematics --skipZeroes 
    python makeDatacard.py --years 2016,2017,2018 --ext ${tag}  --prune --pruneThreshold 0.000000001 --doSystematics
	  python prepareDatacard_eft.py
		mv Datacard_updated.txt /home/users/fsetti/HHggTauTau/inference/datacards_run2/ggtt/EFT_cards/${tag}/datacard_${bm_tag}.txt
  	popd
	}
	
	copy_files(){
			mkdir -p /home/users/fsetti/HHggTauTau/inference/datacards_run2/ggtt/EFT_cards/${tag}/Models/
			mkdir -p /home/users/fsetti/HHggTauTau/inference/datacards_run2/ggtt/EFT_cards/${tag}/Models/signal/
			mkdir -p /home/users/fsetti/HHggTauTau/inference/datacards_run2/ggtt/EFT_cards/${tag}/Models/background/
	
			cp Signal/outdir_packaged/CMS-HGG*.root /home/users/fsetti/HHggTauTau/inference/datacards_run2/ggtt/EFT_cards/${tag}/Models/signal/
			cp Background/outdir_$tag/CMS-HGG*.root /home/users/fsetti/HHggTauTau/inference/datacards_run2/ggtt/EFT_cards/${tag}/Models/background/
	}
	
	model_bkg
	model_sig
	make_datacard
	#copy_files

	bm_tag=$((bm_tag+1))
done
