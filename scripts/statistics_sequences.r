library(stringr)
library(dplyr)
library(reshape2)
library(ggplot2)

### LOAD DATA ###
data <- read.csv("/home/ida/master-thesis/data/temporary_data/all_data_numbered_origin_vdjdbnames.csv")
# Remove entries that are not in final dataset
IDs_in_final <- read.table("/home/ida/master-thesis/data/IDs_in_train_set.txt")
data <- data[data$X.ID %in% IDs_in_final$V1,]
# Make numeric
data$cdr3a_loop_length <- as.numeric(lapply(data$CDR3a, str_length))
data$cdr3b_loop_length <- as.numeric(lapply(data$CDR3b, str_length))

### COUNTS ###
unique(data$peptide)
length(unique(data$peptide))
length(unique(data$CDR3a))
length(unique(data$CDR3b))

### BARPLOTS OF GERM LINES ###
pdf("/home/ida/master-thesis/results/0503_sequence_statistics/j_gene_alpha.pdf", width = 10)
ggplot(data = data, aes(x = j_alpha_vdjdb_name, fill = origin)) +
  geom_bar(position = "dodge") +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  xlab("J gene TCRa")
dev.off()

pdf("/home/ida/master-thesis/results/0503_sequence_statistics/v_gene_alpha.pdf", width = 10)
ggplot(data = data, aes(x = v_alpha_vdjdb_name, fill = origin)) +
  geom_bar(position = "dodge") +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  xlab("V gene TCRa")
dev.off()

pdf("/home/ida/master-thesis/results/0503_sequence_statistics/j_gene_beta.pdf", width = 10)
ggplot(data = data, aes(x = j_beta_vdjdb_name, fill = origin)) +
  geom_bar(position = "dodge") +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  xlab("J gene beta")
dev.off()

pdf("/home/ida/master-thesis/results/0503_sequence_statistics/v_gene_beta.pdf", width = 10)
ggplot(data = data, aes(x = v_beta_vdjdb_name, fill = origin)) +
  geom_bar(position = "dodge") +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  xlab("V gene beta")
dev.off()

### HISTOGRAMS OF LOOP LENGTH ###
data$binder = as.factor(data$binder)
levels(data$binder) <- c("Negatives", "Positives")
pdf("/home/ida/master-thesis/results/0503_sequence_statistics/loop_length_cdr3a_binder.pdf", height = 2, width = 3.5)
ggplot(data, aes(x = cdr3a_loop_length)) +
  geom_histogram(binwidth = 0.5) +
  facet_grid(cols = vars(binder)) +
  xlab("Loop length of CDR3a")
dev.off()

pdf("/home/ida/master-thesis/results/0503_sequence_statistics/loop_length_cdr3b_binder.pdf", height = 2, width = 3.5)
ggplot(data, aes(x = cdr3b_loop_length)) +
  geom_histogram(binwidth = 0.5) +
  facet_grid(cols = vars(binder)) +
  xlab("Loop length of CDR3b")
dev.off()

### BARPLOT OF PEPTIDES ###
pdf("/home/ida/master-thesis/results/0503_sequence_statistics/peptide_barplot.pdf", height = 5)
ggplot(data, aes(x = peptide, fill = origin)) +
  geom_bar(position = "dodge") +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))
dev.off()

### FOR EACH PEPTIDE DISTRIBUTION OF GERM LINES ###

library(RColorBrewer)
library(Polychrome)
P18 = unname(createPalette(18,  c("#ff0000", "#00ff00", "#0000ff")))
n <- 18
qual_col_pals = brewer.pal.info[brewer.pal.info$category == 'qual',]
col_vector = unlist(mapply(brewer.pal, qual_col_pals$maxcolors, rownames(qual_col_pals)))
colors = sample(col_vector, n)

pdf("/home/ida/master-thesis/results/0503_sequence_statistics/j_gene_alpha_per_peptide.pdf", width = 10)
ggplot(data = data[data$binder==1,], aes(x = j_alpha_vdjdb_name, fill = peptide)) +
  geom_bar() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  xlab("J gene TCRa") +
  scale_fill_manual(values = P18)
dev.off()

pdf("/home/ida/master-thesis/results/0503_sequence_statistics/v_gene_alpha_per_peptide.pdf", width = 10)
ggplot(data = data[data$binder==1,], aes(x = v_alpha_vdjdb_name, fill = peptide)) +
  geom_bar() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  xlab("V gene TCRa") +
  scale_fill_manual(values = P18)
dev.off()

pdf("/home/ida/master-thesis/results/0503_sequence_statistics/j_gene_beta_per_peptide.pdf", width = 10)
ggplot(data = data[data$binder==1,], aes(x = j_beta_vdjdb_name, fill = peptide)) +
  geom_bar() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  xlab("J gene TCRb") +
  scale_fill_manual(values = P18)
dev.off()

pdf("/home/ida/master-thesis/results/0503_sequence_statistics/v_gene_beta_per_peptide.pdf", width = 10)
ggplot(data = data[data$binder==1,], aes(x = v_beta_vdjdb_name, fill = peptide)) +
  geom_bar() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1)) +
  xlab("V gene TCRb") +
  scale_fill_manual(values = P18)
dev.off()
