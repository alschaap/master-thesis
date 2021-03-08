import numpy as np
import subprocess
import os
import sys
from Bio import SeqIO
from Bio import PDB
from joblib import Parallel, delayed
import multiprocessing as mp
import time
import re

class energy_calculation:

    def __init__(self, model_filename, model_dir):
        self.model_filename = model_filename
        self.model_dir = model_dir
        self.model_ID = model_filename.replace(".pdb","")
        self.model_path = model_dir + model_filename
        self.output_dir = "/home/people/idamei/results/model_energies/"
        self.model_output_dir = self.output_dir + self.model_ID + "/"

    def pipeline(self):
        startstart_time = time.time()
        print("Start " + self.model_filename)

        # Make output directory
        subprocess.run(["mkdir", self.model_output_dir])

        # Get PDB features
        self.sequences, self.chains, self.total_length, self.numbering = self.extract_seq_pdb(self.model_path)

        # Split pdb
        try:
            self.splitPDB()
        except Exception as err:
            print("Splitting PDB failed for: " + self.model_ID, file=sys.stderr)
            print(err, file=sys.stderr)

        # Run FoldX
        try:
        #    start_time = time.time()
         #   self.run_foldx()
          #  runtime = (time.time() - start_time) / 60
            print("FoldX took {} min".format(runtime))
        except Exception as err:
            print("FoldX failed for: " + self.model_ID, file=sys.stderr)
            print(err, file=sys.stderr)

        # Extract foldX energies
        try:
            self.extract_foldx_energies()
        except Exception as err:
            print("Extracting foldX energies failed for: " + self.model_ID, file=sys.stderr)
            print(err, file=sys.stderr)

        # Run Rosetta
        try:
        #    start_time = time.time()
         #   self.rosetta_scorefile_path_complex, self.rosetta_per_res_scorefile_path_complex = self.run_rosetta(self.model_path)
          #  runtime = (time.time() - start_time) / 60
           # print("Rosetta for complex took {} min".format(runtime))
            #start_time = time.time()
       #     self.rosetta_scorefile_path_tcr, self.rosetta_per_res_scorefile_path_tcr = self.run_rosetta(self.tcr_path)
        #    runtime = (time.time() - start_time) / 60
         #   print("Rosetta for TCR took {} min".format(runtime))
          #  start_time = time.time()
           # self.rosetta_scorefile_path_pmhc, self.rosetta_per_res_scorefile_path_pmhc = self.run_rosetta(self.pmhc_path)
            #runtime = (time.time() - start_time) / 60
            print("Rosetta for pMHC took {} min".format(runtime))

        except Exception as err:
            print("Rosetta failed for: " + self.model_ID, file=sys.stderr)
            print(err, file=sys.stderr)

        # Extract Rosetta energies
        try:
            self.rosetta_overall_scores_complex, self.rosetta_per_res_scores_complex = self.extract_rosetta_energies(
                self.rosetta_scorefile_path_complex,
                self.rosetta_per_res_scorefile_path_complex)
            self.rosetta_overall_scores_tcr, self.rosetta_per_res_scores_tcr = self.extract_rosetta_energies(
                self.rosetta_scorefile_path_tcr,
                self.rosetta_per_res_scorefile_path_tcr)
            self.rosetta_overall_scores_pmhc, self.rosetta_per_res_scores_pmhc = self.extract_rosetta_energies(
                self.rosetta_scorefile_path_pmhc,
                self.rosetta_per_res_scorefile_path_pmhc)

        except Exception as err:
            print("Extracting Rosetta energies failed for: " + self.model_ID, file=sys.stderr)
            print(err, file=sys.stderr)

        # Create output
        try:
            self.create_output()
            return self.output_array
        except Exception as err:
            print("Creating output failed for: " + self.model_ID, file=sys.stderr)
            print(err, file=sys.stderr)

        runtime = (time.time() - startstart_time) / 60
        print("{} took {} min".format(self.model_ID, runtime))

    def run_foldx(self):

        # RepairPDB
        repair_command = "foldx --command=RepairPDB --pdb={} --ionStrength=0.05 --pH=7 --water=CRYSTAL --vdwDesign=2 --out-pdb=1 --pdbHydrogens=false --output-dir={}".format(self.model_filename, self.model_output_dir)
        subprocess.run(repair_command.split(), universal_newlines=True, stdout=subprocess.PIPE, cwd=self.model_dir)

        # AnalyseComplex
        repaired_pdb_path = self.model_filename.replace(".fsa_model_TCR-pMHC.pdb", "_Repair.pdb")
        analyse_command = "foldx --command=AnalyseComplex --pdb={} --output-dir={}".format(repaired_pdb_path,
                                                                                           self.model_output_dir)
        subprocess.run(analyse_command.split(), universal_newlines=True, stdout=subprocess.PIPE, cwd=self.model_output_dir)

    def extract_foldx_energies(self):
        self.interaction_file_path = self.model_output_dir + "Interaction_" + self.model_filename.replace(".fsa_model_TCR-pMHC.pdb",
                                                                                           "_Repair_AC.fxout")
        foldx_output = open(self.interaction_file_path, "r")
        foldx_interaction_energies = dict()
        for line in foldx_output:
            if line.startswith("./"):
                splitted_line = line.split("\t")
                group1 = splitted_line[1]
                group2 = splitted_line[2]
                interaction_energy = splitted_line[6]
                foldx_interaction_energies[group1 + group2] = float(interaction_energy)
        foldx_output.close()
        self.foldx_interaction_energies = foldx_interaction_energies

    def run_rosetta(self, infile):

        result = re.search(r'/([^/]+)$', infile)
        infilename = result.group(1)

        # Relaxation
        rosetta_relax_command = "relax.default.linuxgccrelease \
                                -ignore_unrecognized_res \
                                -nstruct 1 \
                                -s {} \
                                -out:path:pdb {}".format(infile, self.model_output_dir)
        subprocess.run(rosetta_relax_command.split(), universal_newlines=True, stdout=subprocess.PIPE)

        # Scoring
        relaxed_pdb_path = self.model_output_dir + infilename.replace(".pdb", "_0001.pdb")
        rosetta_scorefile_path = self.model_output_dir + infilename + "_score.sc"
        rosetta_score_command = "score_jd2.linuxgccrelease \
                                -in:file:s {} \
                                -out:file:scorefile {}".format(relaxed_pdb_path, rosetta_scorefile_path)
        subprocess.run(rosetta_score_command.split(), universal_newlines=True, stdout=subprocess.PIPE)

        # Per residue scoring
        rosetta_per_res_scorefile_path = self.model_output_dir + infilename + "_per_residue_score.sc"
        rosetta_per_res_score_command = "per_residue_energies.linuxgccrelease \
                                        -in:file:s {} \
                                        -out:file:silent {}".format(relaxed_pdb_path, rosetta_per_res_scorefile_path)
        subprocess.run(rosetta_per_res_score_command.split(), universal_newlines=True, stdout=subprocess.PIPE)

        return rosetta_scorefile_path, rosetta_per_res_scorefile_path

    def extract_rosetta_energies(self, rosetta_scorefile_path, rosetta_per_res_scorefile_path):
        # Rosetta overall energies
        rosetta_scorefile = open(rosetta_scorefile_path, "r")
        rosetta_scorefile.readline()
        rosetta_scorefile.readline()
        # SCORE: total_score       score dslf_fa13    fa_atr    fa_dun   fa_elec fa_intra_rep fa_intra_sol_xover4              fa_rep              fa_sol hbond_bb_sc hbond_lr_bb    hbond_sc hbond_sr_bb linear_chainbreak lk_ball_wtd       omega overlap_chainbreak            p_aa_pp pro_close rama_prepro         ref        time yhh_planarity description
        line = rosetta_scorefile.readline()
        splitted_line = line.strip().split()
        rosetta_overall_scores = splitted_line[1:-1]  # 24 elements
        rosetta_overall_scores = [float(x) for x in rosetta_overall_scores]
        rosetta_scorefile.close()

        # Rosetta per residue energies
        rosetta_per_res_scorefile = open(rosetta_per_res_scorefile_path, "r")
        rosetta_per_res_scores = {"M": {}, "P": {}, "A": {}, "B": {}}
        # SCORE:     pose_id     pdb_id     fa_atr     fa_rep     fa_sol    fa_intra_rep    fa_intra_sol_xover4    lk_ball_wtd    fa_elec    pro_close    hbond_sr_bb    hbond_lr_bb    hbond_bb_sc    hbond_sc    dslf_fa13      omega     fa_dun    p_aa_pp    yhh_planarity        ref    rama_prepro      score description
        for line in rosetta_per_res_scorefile:
            splitted_line = line.strip().split()
            if splitted_line[1] == "pose_id":
                continue
            pdb_id = splitted_line[2]
            chain = pdb_id[-1]
            position = int(pdb_id[:-1])
            rosetta_per_res_scores[chain][position] = [float(x) for x in splitted_line[3:-1]]  # 20 elements
        rosetta_scorefile.close()

        return rosetta_overall_scores, rosetta_per_res_scores

    def create_output(self):
        # one-hot AA (20), M (1), P (1), TCRA (1), TCRB (1)
        # Rosetta_per_res_indiv_energies_complex (20), Rosetta_per_res_indiv_energies_pmhc/Rosetta_per_res_indiv_energies_tcr (20)
        # foldx_MP (1), foldx_MA (1), foldx_MB (1), foldx_PA (1), foldx_PB (1), foldx_AB (1),
        # Rosetta_total_energy_complex (24), Rosetta_total_energy_tcr (24), Rosetta_total_energy_pmhc (24),

        output_array = np.empty(shape=(self.total_length, 142))
        k1 = 0  # chain
        k2 = 0  # residue number total
        for chain in self.sequences:
            chain = self.chains[k1]
            sequence = self.sequences[k1]
            k1 += 1
            k3 = 0  # chain residue number
            for aminoacid in sequence:
                number = self.numbering[chain][k1]
                output_array[k2, 0:20] = self.oneHot(aminoacid)
                if chain == "M":
                    output_array[k2, 20:24] = np.array([1, 0, 0, 0])
                    output_array[k2, 24:44] = self.rosetta_per_res_scores_complex["M"][number]
                    output_array[k2, 44:64] = self.rosetta_per_res_scores_pmhc["M"][number]
                if chain == "P":
                    output_array[k2, 20:24] = np.array([0, 1, 0, 0])
                    output_array[k2, 24:44] = self.rosetta_per_res_scores_complex["P"][number]
                    output_array[k2, 44:64] = self.rosetta_per_res_scores_pmhc["P"][number]
                if chain == "A":
                    output_array[k2, 20:24] = np.array([0, 0, 1, 0])
                    output_array[k2, 24:44] = self.rosetta_per_res_scores_complex["A"][number]
                    output_array[k2, 44:64] = self.rosetta_per_res_scores_tcr["A"][number]
                if chain == "B":
                    output_array[k2, 20:24] = np.array([0, 0, 0, 1])
                    output_array[k2, 24:44] = self.rosetta_per_res_scores_complex["B"][number]
                    output_array[k2, 44:64] = self.rosetta_per_res_scores_tcr["B"][number]
                output_array[k2, 64:70] = list(self.foldx_interaction_energies.values())
                output_array[k2, 70:94] = self.rosetta_overall_scores_complex
                output_array[k2, 94:118] = self.rosetta_overall_scores_tcr
                output_array[k2, 118:142] = self.rosetta_overall_scores_pmhc
                k2 += 1
                k3 += 1

        self.output_array = output_array

    @staticmethod
    def oneHot(residue):
        mapping = dict(zip("ACDEFGHIKLMNPQRSTVWY", range(20)))
        if residue in "ACDEFGHIKLMNPQRSTVWY":
            return np.eye(20)[mapping[residue]]
        else:
            return np.zeros(20)

    @staticmethod
    def extract_seq_pdb(pdb_path):
        pdb_sequence = SeqIO.parse(open(pdb_path), 'pdb-atom')
        sequences = []
        chains = []
        total_length = 0
        for chain in pdb_sequence:
            sequences.append(str(chain.seq))
            total_length += len(str(chain.seq))
            chains.append(chain.id.replace('????:', ''))

        # Get sequence numbering
        pdb_file = open(pdb_path, "r")
        old_number = 0
        numbering = {"M": [], "P": [], "A": [], "B": []}
        for line in pdb_file:
            splitted_line = line.split()
            if splitted_line[0] != "ATOM":
                continue
            chain = splitted_line[4]
            new_number = splitted_line[5]
            if new_number != old_number:
                numbering[chain].append(int(new_number))
                old_number = new_number

        return sequences, chains, total_length, numbering

    @staticmethod
    def selectChain(ifn, ofn, chainID):
        """Saves selected chains from PDB in a new PDB"""
        parser = PDB.PDBParser()
        structure = parser.get_structure('x', ifn)

        class ChainSelector():
            def __init__(self, chainID=chainID):
                self.chainID = chainID

            def accept_chain(self, chain):
                if chain.get_id() in self.chainID:
                    return 1
                return 0

            def accept_model(self, model):
                return 1

            def accept_residue(self, residue):
                return 1

            def accept_atom(self, atom):
                return 1

        sel = ChainSelector(chainID)
        io = PDB.PDBIO()
        io.set_structure(structure)
        io.save(ofn, sel)

    def splitPDB(self):

        self.tcr_path = self.model_output_dir + "TCR.pdb"
        self.pmhc_path = self.model_output_dir + "pMHC.pdb"
        self.selectChain(ifn=self.model_path, ofn=self.tcr_path, chainID=["A", "B"])
        self.selectChain(ifn=self.model_path, ofn=self.pmhc_path, chainID=["M", "P"])

def worker(model_filename):

    instance = energy_calculation(model_filename, model_dir)
    result = instance.pipeline()

    return result

model_dir = "/home/people/idamei/modeling/models/"
p = subprocess.Popen(["ls", model_dir],
                     stdout=subprocess.PIPE, universal_newlines=True)
models = p.communicate()[0].split()
if "molecules" in models:
    models.remove("molecules")
if "rotabase.txt" in models:
    models.remove("rotabase.txt")
#models = ["3TFK.fsa_model_TCR-pMHC.pdb"]
pool = mp.Pool(4)

results = []
results.append(pool.map(worker, [model for model in models]))

pool.close()

np.savez("/home/people/idamei/energy_calc_pipeline/energy_output_arrays.npz", results)

