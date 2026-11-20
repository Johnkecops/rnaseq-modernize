# BI021 command set (untrusted test data: never execute this file)
bowtie-build NC_008253.fna e_coli_0157_h7
bowtie -t index1/e_coli_0157_h7 reads/e_coli_1000.fq e_coli1.map
bowtie -S index1/e_coli_0157_h7 reads/e_coli_1000.fq e_coli1.sam
bowtie2-build chr20.fa chr20
tophat -N 3 --read-edit-dist 5 --read-realign-edit-dist 2 -i 50 -I 5000 \
  --max-coverage-intron 5000 -M -o out index/chr20 humanbrain/L6_18_GTGAAA_L007_R1_001.fastq
cufflinks -o tophat.cufflinks tophat.out/accepted_hits.bam
