import os
import glob
import pandas
import argparse
import root_pandas
import numpy as np

years = [ '2016UL_preVFP', '2017', '2018' ]
procs_dict = {"ggH_M125": "ggH", "ttH_M125":"ttH", "VBFH_M125":"VBFH", "VH_M125":"VH", "Data":"Data",
              "ttHH_ggbb": "ttHHheftSM",
              "ttHH_HEFT_c2_1_ggbb": "ttHHheft1",
              "ttHH_HEFT_c2_2_ggbb": "ttHHheft2",
              "ttHH_HEFT_c2_3_ggbb": "ttHHheft3",
              "ttHH_HEFT_c2_4_ggbb": "ttHHheft4",
              "ttHH_HEFT_c2_5_ggbb": "ttHHheft5",
              "ttHH_HEFT_c2_6_ggbb": "ttHHheft6",
              "ttHH_HEFT_c2_7_ggbb": "ttHHheft7",
              "ttHH_HEFT_kt_2_ggbb": "ttHHheft8",
              "ttHH_HEFT_kt_3_ggbb": "ttHHheft9",
              "ttHH_HEFT_kl_2_ggbb": "ttHHheft10",
              "ttHH_HEFT_kl_3_ggbb": "ttHHheft11",
              "ttHH_HEFT_kl_0p5_ggbb": "ttHHheft12",
              "ttHH_HEFT_kl_0p5_c2_1_ggbb": "ttHHheft13",
                 }

parser = argparse.ArgumentParser()

parser.add_argument(
    "--input",
    help = "path to input parquet directory",
    type = str,
    default = "/home/users/azecchin/Analysis/HiggsDNA/output/heft_FF_syst/"
)

parser.add_argument(
    "--tag",
    help = "unique tag to identify batch of processed samples",
    type = str,
    default = "test"
)
parser.add_argument(
    "--mvas",
  nargs="*",
    help = "mva limits to SRs",
    type = float,
    default = [0.9903,  0.966974]  
)
parser.add_argument(
    "--nSRs",
    help = "number of Signal Regions",
    type = int,
    default = 2
)


args = parser.parse_args()

args.mvas+=[99]
args.mvas.sort(reverse=True)

out_dir = "/home/users/azecchin/Analysis/FinalFit/CMSSW_10_2_13/src/flashggFinalFit/files_systs/" + str(args.tag) + "/"
#out_dir = '/home/users/fsetti/HHggTauTau/coupling_scan/CMSSW_10_2_13/src/flashggFinalFit/files_systs/' + str(args.tag) + '/'

os.system("rm -rf %s"%(out_dir))
os.system("mkdir -p %s"%(out_dir))

os.system("mkdir -p %s/Data"%(out_dir))
os.system("mkdir -p %s/2016"%(out_dir))
os.system("mkdir -p %s/2017"%(out_dir))
os.system("mkdir -p %s/2018"%(out_dir))

procs = glob.glob(str(args.input)+'/*')
print ("procs {}".format(procs))

#Process Data
files = glob.glob(str(args.input)+'/Data*/*.parquet')
for file_ in files:
  df = pandas.read_parquet(file_, engine='pyarrow')
  df['CMS_hgg_mass'] = df['Diphoton_mass']
  for sr in range(args.nSRs):
    dfs = df.loc[ ( df.bdt_score < args.mvas[sr] ) & ( df.bdt_score >= args.mvas[sr+1] ) & ( ( df.Diphoton_mass < 120 ) | ( df.Diphoton_mass > 130 ) ) ]
    print("Adding {} events to allData".format(len(dfs)))
    dfs.to_root(out_dir+'/Data/'+'/allData.root',key='Data_13TeV_SR'+str(sr+1), mode='a')

for proc in procs[:]:

  if "Data" in proc:
    continue

  if proc.split("/")[-1].split("_201")[0] not in procs_dict.keys():
    print("\n\n WARNING Process {} was not found in the process dictionary, Skipping...".format(proc.split("/")[-1].split("_201")[0]) )
    continue
  
  for year in years:
    if year not in proc.split("/")[-1]:
      continue
  
    #get all files including systematic variations
    files = glob.glob(proc+'/*.parquet')
    
    for file_ in files:
      print ("Now processing: ", file_)
      df = pandas.read_parquet(file_, engine='pyarrow')
      if year == '2016UL_preVFP':
        try:
          df_ext1 = pandas.read_parquet(file_.replace("2016UL_preVFP","2016UL_postVFP"), engine='pyarrow')
          df = pandas.concat([ df, df_ext1 ], ignore_index=True)
        except:
          print ("Not finding 2016UL_postVFP for this sample: ", proc )
          print ("Most likely it is data")
        
      tag  =  ''
      if 'nominal' not in file_.split("/")[-1]:
        if 'up' in file_.split("/")[-1]:
          tag  = file_.split("merged")[-1]
          tag  = tag.split("_up")[0]
          tag  += 'Up01sigma'
        if 'down' in file_.split("/")[-1]:
          tag  = file_.split("merged")[-1]
          tag  = tag.split("_down")[0]
          tag  += 'Down01sigma'
      if 'scale' in file_.split("/")[-1]:
        tag = '_MCScale' + tag
      if 'smear' in file_.split("/")[-1]:
        tag = '_MCSmear' + tag

      #Define hgg_mass & dZ variable
      df['CMS_hgg_mass'] = df['Diphoton_mass']
      df['dZ']  = np.ones(len(df['Diphoton_mass']))
      df['weight'] = df['weight_central'] * 2
      df['weight_central'] = df['weight'] 
      yield_systematics  = [ key for key in df.keys() if ( "weight_" in key ) and ( "_up" in key or "_down" in key )]
      rename_sys  = {}
      for sys in yield_systematics:
        #a bit of gymnastics to get the inputs right for Mr. flashggFinalFit
        sys_central = sys.replace("_up","_central")
        sys_central = sys.replace("_down","_central")
        if 'btag' in sys_central:
          sys_central = 'weight_btag_deepjet_sf_SelectedJet_central'
        df[sys]     = df[sys] / df[sys_central]
        if "_up" in sys:
          if 'btag' in sys:
            rename_sys[sys] = sys.replace("_up","")
            rename_sys[sys] += "Up01sigma"
            continue
          rename_sys[sys] = sys.replace("_up","Up01sigma")
        if "_down" in sys:
          if 'btag' in sys:
            rename_sys[sys] = sys.replace("_down","")
            rename_sys[sys] += "Down01sigma"
            continue
          rename_sys[sys] = sys.replace("_down","Down01sigma")
      #print(rename_sys)
      df = df.rename(columns=rename_sys)

      #Process Signal
      year_str = year
      if '2016' in year:
        year_str = '2016'

      proc_tag = ''
      # if 'EFT' in proc.split("/")[-1]:
      #   proc_tag = 'ggHHbm' + proc.split("/")[-1].split("node_")[-1].split("_201")[0]
      # else: 
      proc_tag = procs_dict[proc.split("/")[-1].split("_201")[0]]

      '''
      Temporary fix to get limits
      '''
      for sr in range(args.nSRs):
          dfs = df.loc[ ( df.bdt_score < args.mvas[sr] ) & ( df.bdt_score >= args.mvas[sr+1] ) & (df.event % 2 == 1) ]
          dfs.to_root(out_dir+year_str+'/'+proc_tag+'_125_13TeV.root',''+proc_tag+'_125_13TeV_SR'+str(sr+1)+tag, mode='a')

