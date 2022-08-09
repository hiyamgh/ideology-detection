#!/usr/bin/env bash
#SBATCH --job-name=contclas
#SBATCH --account=hkg02
#SBATCH --partition=large
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=ALL
#SBATCH --mail-user=hkg02@mail.aub.edu

module load python/3

python create_contextual_sentences_classification.py --archive assafir
