#!/usr/bin/env bash
#SBATCH --job-name=fast-nahar
#SBATCH --account=hkg02
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mail-type=ALL
#SBATCH --mail-user=hkg02@mail.aub.edu
#SBATCH --array=1-77%10

module load python/3


START=1933
END=2009
USCOUNTER=1
for ((i=START;i<=END;i++)); do
   if [ $USCOUNTER -eq $SLURM_ARRAY_TASK_ID ]; then
    echo $i
    python train_fasttext.py --archive nahar --wordNgrams 4 --dim 300 --ws 5 --minCount 100 --model skipgram --neg 15 --lr 0.001 --year ${i}
   fi
   USCOUNTER=$(expr $USCOUNTER + 1)
done