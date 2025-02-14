import json
import os
import glob
import pandas
import argparse
import root_pandas
import numpy as np
import uproot
from collections import Counter

# def to_root(df,path,key='my_tree',mode='w',store_index=True):
  
#   column_name_counts = Counter(df.columns)
#   if max(column_name_counts.values()) > 1:
#       raise ValueError('DataFrame contains duplicated column names: ' +
#                         ' '.join({k for k, v in column_name_counts.items() if v > 1}))

#   # We don't want to modify the user's DataFrame here, so we make a shallow copy
#   df_ = df.copy(deep=False)

#   if store_index:
#     name = df_.index.name
#     if name is None:
#         # Handle the case where the index has no name
#         name = ''
#     df_['__index__' + name] = df_.index

#   # Convert categorical columns into something root_numpy can serialise
#   for col in df_.select_dtypes(['category']).columns:
#     name_components = ['__rpCaT', col, str(df_[col].cat.ordered)]
#     name_components.extend(df_[col].cat.categories)
#     if ['*' not in c for c in name_components]:
#         sep = '*'
#     else:
#         raise ValueError('Unable to find suitable separator for columns')
#     df_[col] = df_[col].cat.codes
#     df_.rename(index=str, columns={col: sep.join(name_components)}, inplace=True)

#   arr = df_.to_records (index=False)

#   if mode == 'a':
#     root_file = uproot.update(path)
#   elif mode == 'w':
#     root_file = uproot.recreate(path)
#   else:
#       raise ValueError('Unknown mode: {}. Must be "a" or "w".'.format(mode))
    
#   if not root_file:
#     raise IOError("cannot open file {0}".format(path))
#   if not root_file.IsWritable():
#     raise IOError("file {0} is not writable".format(path))

#   # Navigate to the requested directory
#   open_dirs = [root_file]
#   for dir_name in key.split('/')[:-1]:
#       current_dir = open_dirs[-1].Get(dir_name)
#       if not current_dir:
#           current_dir = open_dirs[-1].mkdir(dir_name)
#       current_dir.cd()
#       open_dirs.append(current_dir)

#   # The key is now just the top component
#   key = key.split('/')[-1]

#   # If a tree with that name exists, we want to update it \\ You are dealing with uproot now... 
#   tree = open_dirs[-1].Get(key)
#   if not tree:
#       tree = None
#   tree = array2tree(arr, name=key, tree=tree)
#   tree.Write(key, ROOT.TFile.kOverwrite)
#   root_file.Close()




# years = [ '2016UL_preVFP', '2017', '2018' ]
years = [ b'2016UL_pre', b'2017', b'2018' ]
procs_dict = {"Data":"Data",
              "ggH_M125": "ggH", "ttH_M125":"ttH", "VBFH_M125":"VBFH", "VH_M125":"VH", 
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
    default = "/home/users/azecchin/Analysis/HiggsDNA/output/heft_presel_FF_syst_condor_MVAscore/"
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

out_dir = "/home/users/azecchin/Analysis/FinalFit/CMSSW_10_2_13/src/flashggFinalFit/files_systs/"+ str(args.tag) + "/"
#out_dir = '/home/users/fsetti/HHggTauTau/coupling_scan/CMSSW_10_2_13/src/flashggFinalFit/files_systs/'+ str(args.tag) + '/'

os.system("rm -rf %s"%(out_dir))
os.system("mkdir -p %s"%(out_dir))

os.system("mkdir -p %s/Data"%(out_dir))
os.system("mkdir -p %s/2016"%(out_dir))
os.system("mkdir -p %s/2017"%(out_dir))
os.system("mkdir -p %s/2018"%(out_dir))

with open(str(args.input)+'/summary.json',"r") as f_in:
  procs_id_map = json.load(f_in)
procs = procs_id_map["sample_id_map"]
# print ("procs {}".format(procs))

#Process Data
#no systematics on Data
file = pandas.read_parquet(str(args.input)+'merged_nominal.parquet', engine='pyarrow') 
print(file)
df=file[ (file.process_id == 0) ]
df['CMS_hgg_mass'] = df['Diphoton_mass']
for sr in range(args.nSRs):
  dfs = df.loc[ ( df.mva_score < args.mvas[sr] ) & ( df.mva_score >= args.mvas[sr+1] ) & ( ( df.Diphoton_mass < 120 ) | ( df.Diphoton_mass > 130 ) ) ]
  print("Adding {} events to allData".format(len(dfs)))
  dfs.to_root(out_dir+'/Data/'+'/allData.root',key='Data_13TeV_SR'+str(sr+1), mode='a')

#Process MCs
files = glob.glob(str(args.input)+'/*.parquet')
for file_ in files:
  glob_df = pandas.read_parquet(file_, engine='pyarrow')

  print ("Now processing: ", file_)
  for proc in procs.keys():

    if "Data" in proc:
      continue

    if proc not in procs_dict.keys():
      print("\n\n WARNING Process {} was not found in the process dictionary, Skipping...".format(proc.split("/")[-1].split("_201")[0]) )
      continue
    
    proc_df = glob_df[glob_df["process_id"]==procs[proc]]
    print("for all years we have {} events for {}".format(len(proc_df),proc))
    for year in years:
      df = proc_df[proc_df["year"]==year]
      print("for year {} we have {} events for {}".format(year,len(df),proc))
      if year == b'2016UL_pre':
        try:
          df_ext1 = df[df["year"]==b'2016UL_pos']
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
      df['dZ'] = np.ones(len(df['Diphoton_mass']))
      df['weight'] = df['weight_central'] * 2
      if "ttHH_HEFT" in proc: #selecting HEFT inputs
        print ("\033[93m \n\n Rescaling HEFT input {} to bbgg BR \033[0m".format(proc))
        df['weight'] = df['weight']*0.002651 #ggbb BR
      df['weight_central'] = df['weight']
      yield_systematics = [ key for key in df.keys() if ( "weight_" in key ) and ( "_up" in key or "_down" in key )]
      rename_sys = {}
      for sys in yield_systematics:
        #a bit of gymnastics to get the inputs right for Mr. flashggFinalFit
        sys_central = sys.replace("_up","_central")
        sys_central = sys.replace("_down","_central")
        if 'btag' in sys_central:
          sys_central = 'weight_btag_deepjet_sf_SelectedJet_central'
        df[sys] = df[sys] / df[sys_central]
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
      year_str = ''
      if year == b'2016UL_pre':
        year_str = '2016'
      if year == b'2017':
        year_str = '2017'
      if year == b'2018':
        year_str = '2018'

      proc_tag = ''
      # if 'EFT' in proc.split("/")[-1]:
      #   proc_tag = 'ggHHbm' + proc.split("/")[-1].split("node_")[-1].split("_201")[0]
      # else: 
      proc_tag = procs_dict[proc.split("/")[-1].split("_201")[0]]

      '''
      Temporary fix to get limits
      '''
      for sr in range(args.nSRs):
        dfs = df.loc[ ( df.mva_score < args.mvas[sr] ) & ( df.mva_score >= args.mvas[sr+1] ) & (df.event % 2 == 1) ]
        print("Adding {} events to {}".format(len(dfs),year_str+"_"+proc_tag))
        dfs.to_root(out_dir+year_str+'/'+proc_tag+'_125_13TeV.root',''+proc_tag+'_125_13TeV_SR'+str(sr+1)+tag, mode='a')

