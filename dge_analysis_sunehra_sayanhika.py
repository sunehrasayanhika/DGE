# -*- coding: utf-8 -*-
"""DGE_Analysis_Sunehra_Sayanhika.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1JpQSs1YzMkQS34Opdy5Vt_ecswEt7d-s

##  Downloading Dataset
"""

if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

BiocManager::install("GEOquery")

library(GEOquery)

library(tidyverse)
library(dplyr)

# Get a GSE series
gse <- getGEO("GSE171663", GSEMatrix = TRUE, AnnotGPL = TRUE) #GSE171663

"""## Check Data"""

list(gse[1])

names(gse)

"""## Check Metadata"""

metadata <- pData(gse[[1]])
metadata

headCount <- head(metadata, n = 5)
t(metadata)

metadata[,1:2]

"""## Check Count Data"""

exp <- exprs(gse[[1]])

exp

"""## Get Suppl Data"""

rownames(pheno1)
colnames(exp1)
rownames(pheno1) == colnames(exp1)

sup <- getGEOSuppFiles("GSE171663")

data <- read.table("/content/GSE171663_gene_expression_matrix.txt.gz", header = TRUE, sep = "\t")
data

data <- data[c(7,13:28)]

data

# Replace column names of data3 from column 2 to 17 with row names of pheno2
colnames(data)[2:17] <- rownames(metadata)

data

# Check for duplicates in the first column
duplicated_rows <- duplicated(data[,1])
sum(duplicated_rows)  # This will show how many duplicates exist

# If you want to see the duplicate values:
data[,1][duplicated_rows]

# Find all occurrences of these values
dup_rows <- which(data[,1] %in% c('ENSG00000252404','ENSG00000280466','ENSG00000253060','ENSG00000284862','ENSG00000284917','ENSG00000286169','ENSG00000280987','ENSG00000168255','ENSG00000285292','ENSG00000258724','ENSG00000269900','ENSG00000234323','ENSG00000284024'))
print("Rows containing occurences:")
print(dup_rows)

# Show the full rows to see if they're actually different data points
print("Full data for these rows:")
print(data[dup_rows,])

# Remove duplicate rows based on Feature	ID
data <- data[!duplicated(data$`ID`), ]
data

# Now set Feature	ID as the row names
rownames(data) <- data$`ID`
data <- data[, -1]  # Remove the Feature	ID column after setting it as row names

# Check the result
data

counts <- data[rowSums(data) > 10,]
counts

condition <- factor(c("C","S","S","S","C","S","S","S","C","S","S","S","C","S","S","S"))

colData <- data.frame(row.names = colnames(counts), condition = condition)
colData

# Install required packages if not already installed
if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")
BiocManager::install("DESeq2")

# Load required libraries
suppressMessages({
  library(DESeq2)
})

#Create a DESeqDataSet object:
# Round values to the nearest integer
counts <- round(counts)

counts[counts < 0] <- NA

counts <- na.omit(counts)

counts

dds <- DESeqDataSetFromMatrix(countData = counts, colData = colData, design = ~ condition)

sampleTable <- data.frame(counts)

directory <- "/content/GSE171663"

ddsHTSeq <- DESeqDataSetFromHTSeqCount(sampleTable = sampleTable,
                                       design= ~ condition)

#Run the DESeq2 analysis: This step performs normalization and statistical testing.
dds <- DESeq(dds)

#Calculate variance-stabilized transformed (vst) counts: This helps in visualization and downstream analysis.
vsData <- vst(dds, blind = FALSE)

#Create a Principal Component Analysis (PCA) plot: This plot shows how samples cluster based on their expression patterns.
plotPCA(vsData, intgroup = "condition")

#Create a Dispersion plot: This plot helps assess the variability between replicates across different expression levels.
plotDispEsts(dds)

#Get results from the differential expression analysis:
res <- results(dds, contrast = c("condition", "S", "C"))

"""**Final results**"""

res

write.csv(res, file = "finalresults.csv")

#Filter for significant genes: Use a p-value cutoff (e.g., 0.05) and possibly a fold change threshold.
sigs <- res[!is.na(res$padj),]
sigs <- sigs[sigs$padj < 0.05,]

upreg <- subset(res, log2FoldChange > 1.5)
upreg[upreg$padj < 0.5,]

"""**Upregulated**"""

upreg

downreg <- subset(res, log2FoldChange < 1.5)
downreg[downreg$padj < 0.5,]

"""**Downregulated**"""

downreg

write.csv(upreg, file = "upreg.csv")
write.csv(downreg, file = "downreg.csv")

#Save significant genes to a CSV file:
write.csv(sigs, file = "significant_genes.csv")



# Install pheatmap if not already installed
if (!require("pheatmap", quietly = TRUE)) {
  install.packages("pheatmap")
}

# Install EnhancedVolcano using BiocManager
if (!require("EnhancedVolcano", quietly = TRUE)) {
  BiocManager::install("EnhancedVolcano")
}

# Load required libraries
suppressMessages({
  library(pheatmap)
  library(EnhancedVolcano)
})

# Set file paths
output_dir <- "results"
dir.create(output_dir, showWarnings = FALSE)

"""LFC shrink does not"""

# 4. Normalization and variance stabilization
dds <- DESeq(dds)
vsd <- vst(dds, blind = FALSE)

# 5. Diagnostic plots
# Count distribution plot
png(file.path(output_dir, "count_distribution.png"))
hist(log2(counts(dds) + 1), main = "Log2 Count Distribution", xlab = "Log2 Counts")
dev.off()

# PCA plot
pcaData <- plotPCA(vsd, intgroup = "condition", returnData = TRUE)
percentVar <- round(100 * attr(pcaData, "percentVar"))
png(file.path(output_dir, "PCA_plot.png"))
ggplot(pcaData, aes(PC1, PC2, color = condition)) +
  geom_point(size = 3) +
  xlab(paste0("PC1: ", percentVar[1], "% variance")) +
  ylab(paste0("PC2: ", percentVar[2], "% variance")) +
  ggtitle("PCA of VST-transformed counts") +
  theme_minimal()
dev.off()

# Sample correlation heatmap
sampleDists <- dist(t(assay(vsd)))
sampleDistMatrix <- as.matrix(sampleDists)
rownames(sampleDistMatrix) <- colnames(vsd)
colnames(sampleDistMatrix) <- colnames(vsd)
png(file.path(output_dir, "sample_correlation_heatmap.png"))
pheatmap(sampleDistMatrix, clustering_distance_rows = sampleDists,
         clustering_distance_cols = sampleDists, main = "Sample Correlation Heatmap")
dev.off()

# Dispersion plot
png(file.path(output_dir, "dispersion_plot.png"))
plotDispEsts(dds, main = "Dispersion Estimates")
dev.off()

# 6. Differential expression analysis
res <- results(dds, alpha = 0.05)
res <- lfcShrink(dds, coef = "condition", type = "apeglm")

# 7. Multiple testing correction
res <- res[order(res$padj), ]
res$significant <- ifelse(res$padj < 0.05, "Yes", "No")

# 8. Diagnostic DE plots
# MA plot
png(file.path(output_dir, "MA_plot.png"))
plotMA(res, main = "MA Plot", ylim = c(-5, 5))
dev.off()

# Volcano plot
png(file.path(output_dir, "volcano_plot.png"))
EnhancedVolcano(res,
                lab = rownames(res),
                x = 'log2FoldChange',
                y = 'padj',
                title = 'Volcano Plot',
                pCutoff = 0.05,
                FCcutoff = 1)
dev.off()

# Heatmap of top differentially expressed genes
topGenes <- head(rownames(res[order(res$padj), ]), 20)
png(file.path(output_dir, "heatmap_top_DE_genes.png"))
pheatmap(assay(vsd)[topGenes, ],
         cluster_rows = TRUE,
         cluster_cols = TRUE,
         show_rownames = TRUE,
         annotation_col = sample_info["condition"],
         main = "Top DE Genes")
dev.off()

# 9. Export results
normalized_counts <- counts(dds, normalized = TRUE)
write.csv(normalized_counts, file = file.path(output_dir, "normalized_counts.csv"))

# Export differential expression results table
res_df <- as.data.frame(res)
write.csv(res_df, file = file.path(output_dir, "differential_expression_results.csv"))

# 10. Summary output
cat("Total DE genes (p-adj < 0.05):", sum(res$padj < 0.05, na.rm = TRUE), "\n")
cat("Top DE genes saved in", output_dir, "\n")