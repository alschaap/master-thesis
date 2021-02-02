#!/usr/bin/env python
# coding: utf-8

import numpy as np
import subprocess
import os
from Bio import SeqIO
from joblib import Parallel, delayed
import multiprocessing as mp
from datetime import datetime

### Functions ###

def oneHot(residue):
    mapping = dict(zip("ACDEFGHIKLMNPQRSTVWY", range(20)))
    if residue in "ACDEFGHIKLMNPQRSTVWY":
        return np.eye(20)[mapping[residue]]
    else:
        return np.zeros(20)
    
def reverseOneHot(encoding):
    mapping = dict(zip(range(20),"ACDEFGHIKLMNPQRSTVWY"))
    seq=''
    for i in range(len(encoding)):
        if np.max(encoding[i])>0:
            seq+=mapping[np.argmax(encoding[i])]
    return seq

def extract_seq_pdb(pdb_path):
    pdb_sequence = SeqIO.parse(open(pdb_path), 'pdb-atom')
    sequences = []
    chains = []
    total_length = 0
    for chain in pdb_sequence:
        sequences.append(str(chain.seq))
        total_length += len(str(chain.seq))
        chains.append(chain.id.replace('????:', ''))
    return sequences, chains, total_length

def run_foldx(model_path):

    foldx_output_path = "/home/people/idamei/energy_calc_pipeline/foldx_output"
    # RepairPDB
    repair_command = "foldx --command=RepairPDB --pdb={} --ionStrength=0.05 --pH=7 --water=CRYSTAL --vdwDesign=2 --out-pdb=1 --pdbHydrogens=false".format(model)
    subprocess.run(repair_command.split(),
                        stdout=subprocess.PIPE, universal_newlines=True)
    
    # AnalyseComplex
    analyse_command = "foldx --command=AnalyseComplex --pdb=" + model.replace(".pdb", "_Repair.pdb")
    subprocess.run(analyse_command.split(),
                        stdout=subprocess.PIPE, universal_newlines=True)

def extract_foldx_energies(foldx_output_path):
    foldx_output = open(foldx_output_path, "r")
    foldx_interaction_energies = dict()
    for line in foldx_output:
        if line.startswith("./"):
            splitted_line = line.split("\t")
            group1 = splitted_line[1]
            group2 = splitted_line[2]
            interaction_energy = splitted_line[6]
            foldx_interaction_energies[group1+group2] = float(interaction_energy)    
    return foldx_interaction_energies

def run_rosetta(model):
    # Relaxation
    rosetta_relax_command = "relax.default.linuxgccrelease \
                             -fa_max_dis 9 \
                             -relax:constrain_relax_to_start_coords \
                             -ignore_unrecognized_res \
                             -missing_density_to_jump \
                             -nstruct 1 \
                             -relax:coord_constrain_sidechains \
                             -relax:cartesian \
                             -beta \
                             -score:weights beta_nov16_cart \
                             -ex1 \
                             -ex2 \
                             -relax:min_type lbfgs_armijo_nonmonotone \
                             -out:suffix _bn15_calibrated \
                             -flip_HNQ \
                             -no_optH false \
                             -s model_TCR-pMHC.pdb \
                             -out:path:pdb /home/people/idamei/rosetta/amelie_rosetta/relax_output \
                             -out:path:score /home/people/idamei/rosetta/amelie_rosetta/expeced_output"
    subprocess.run(rosetta_relax_command.split(),
                        stdout=subprocess.PIPE, universal_newlines=True)
    
    # Scoring
    rosetta_score_command = 
    subprocess.run(rosetta_score_command.split(),
                        stdout=subprocess.PIPE, universal_newlines=True)
    
def extract_rosetta_energies(rosetta_output_path)
    
def create_output(pdb_path, foldx_interaction_energies):
    # one-hot AA, M, P, TCR, foldx_MP, foldx_MA, foldx_MB, foldx_PA, foldx_PB, foldx_AB, 
    # Rosetta_total_energy, Rosetta_per_res_indiv_energies
    
    # Extract sequence from PDB
    sequences, chains, total_length = extract_seq_pdb(pdb_path)
    
    # Create output_array
    output_array = np.empty(shape=(total_length,29))
    k1 = 0
    k2 = 0
    for chain in sequences:
        chain = chains[k1]
        k1 += 1
        for aminoacid in chain:
            output_array[k2,0:20] = oneHot(aminoacid)
            if chain == "M":
                output_array[k2,20:23] = np.array([1, 0, 0])
            if chain == "P":
                output_array[k2,20:23] = np.array([0, 1, 0])
            if chain == "A" or chain == "B":
                output_array[k2,20:23] = np.array([0, 0, 1])
            output_array[k2,23:30] = list(foldx_interaction_energies.values())
            k2 += 1
    
    return output_array

def pipeline(model):
    
    try:
        # FoldX
        run_foldx(model)
    
        # Extract foldX energies
        foldx_interaction_path = "/home/ida/foldx/Interaction_" + model.replace(".pdb", "_Repair_AC.fxout")
        foldx_interaction_energies = extract_foldx_energies(foldx_interaction_path)

        # Rosetta
        run_rosetta(model)

        # Extract Rosetta energies
        rosetta_output_path = 
        extract_rosetta_energies(rosetta_output_path)

        # Create output
        model_path = "/home/ida/foldx/" + model
        output_array = create_output(model_path, foldx_interaction_energies)

    return output_array

    except error as err:
        print("Error: " err)
    

# Calculate energy with FoldX
models = ["5men_model_TCR-pMHC.pdb", "5nmf_model_TCR-pMHC.pdb", "3tkf_model_TCR-pMHC.pdb", "5isz_model_TCR-pMHC.pdb"]

pool = mp.Pool(4)

results = []
results.append(pool.map(pipeline, [model for model in models]))

pool.close()


