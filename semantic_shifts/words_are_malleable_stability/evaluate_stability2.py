import pickle
import os
from itertools import cycle
from bidi import algorithm as bidialg
import arabic_reshaper
from words_are_malleable2 import get_stability_combined_one_word
import fasttext
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import csv
# from ar_corrector.corrector import Corrector
import time
import argparse


def mkdir(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def filter_stability_neighbors(stability_neigh, stability_comb):
    """ filter out the unwanted neighbors of words from the neighbors-based approach i.e.
        keep only the words in the common vocabulary
    """
    stability_neigh_filtered = {}
    for k in stability_comb:
        stability_neigh_filtered[k] = stability_neigh[k]
    return stability_neigh_filtered


def print_items(anydict):
    for k, v in anydict.items():
        print(k, v)


def save_heads_tails_all(stabilities_comb, stabilities_neigh, stabilities_lin, n=25, verbose=True, save_heads_tails=True,
                    save_dir=None,
                    file_name=None):
    """ gets the top n most unstable words, and the top n most stable words """
    # sort the stabilities dictionary by increasing order of stabilities (items at the beginning
    # have low stability - items at the end have high stability)
    stabilities_comb = {k: v for k, v in sorted(stabilities_comb.items(), key=lambda item: item[1])}
    stabilities_neigh = {k: v for k, v in sorted(stabilities_neigh.items(), key=lambda item: item[1])}
    stabilities_lin = {k: v for k, v in sorted(stabilities_lin.items(), key=lambda item: item[1])}

    iterations = [(stabilities_comb, 'Combination'), (stabilities_neigh, 'Neighbor-based'),
                  (stabilities_lin, 'Linear-Mapping')
                  ]

    heads_all = {}
    tails_all = {}

    for item in iterations:
        stabilities, name = item[0], item[1]
        # first n items = heads = the most unstable words
        heads = {k: stabilities[k] for k in list(stabilities)[:n]}
        # last n items = tails = the most stable words
        tails = {k: stabilities[k] for k in list(stabilities)[-n:]}

        heads_mod = [(k, v) for k, v in heads.items()]
        tails_mod = [(k, v) for k, v in tails.items()]

        if verbose:
            print('{} - heads:'.format(name))
            print_items(heads)
            print('{} - tails:'.format(name))
            print_items(tails)

        heads_all[name] = heads
        tails_all[name] = tails

        if save_heads_tails:
            mkdir(save_dir)
            with open(os.path.join(save_dir, '{}_{}.csv'.format(file_name, name)), 'w', encoding='utf-8-sig', newline='') as f:
                r = csv.writer(f)
                r.writerow(['heads', 'tails'])

                for i in range(len(heads_mod)):
                    r.writerow([heads_mod[i][0] + "," + str(heads_mod[i][1]), tails_mod[i][0] + "," + str(tails_mod[i][1])])

    return heads_all, tails_all


def get_heads_tails(stabilities, n, verbose=True):
    """ gets the top n most unstable words, and the top n most stable words """
    # sort the stabilities dictionary by increasing order of stabilities (items at the beginning
    # have low stability - items at the end have high stability)
    stabilities = {k: v for k, v in sorted(stabilities.items(), key=lambda item: item[1])}

    # first n items = heads = the most unstable words
    heads = {k: stabilities[k] for k in list(stabilities)[:n]}
    # last n items = tails = the most stable words
    tails = {k: stabilities[k] for k in list(stabilities)[-n:]}
    if verbose:
        print('heads:')
        print_items(heads)
        print('tails:')
        print_items(tails)
    return heads, tails


def get_stability_words(stabilities, words):
    """ prints the stability value of each word """
    for w in words:
        if w in stabilities:
            print('{}: {}'.format(w, str(stabilities[w])))
        else:
            print('word {} not found in teh dictionary'.format(w))


def jaccard_similarity(listoflists):
    inter = set.intersection(*map(set, listoflists))
    un = set().union(*listoflists)
    return float(len(inter) / len(un))

# ax[0].set_xlabel("Combined" if i == 0 else "Neighbor-based" if i == 1 else "Linear-Mapping")


def generate_stability_heatmap(words, stability_dicts_combined, stability_dicts_neighbor,
                               stability_dicts_linear,
                               years, save_dir, fig_name):
    yticks = [bidialg.get_display(arabic_reshaper.reshape(w)) for w in words]
    numxticks = len(stability_dicts_combined)
    fig, ax = plt.subplots(nrows=1, ncols=3)
    data_comb, data_neigh, data_lin = [], [], []
    for w in words:
        stab_vals_comb, stab_vals_neigh, stab_vals_lin = [], [], []
        for j in range(len(years)):
            stab_vals_comb.append(stability_dicts_combined[j][w])
            stab_vals_neigh.append(stability_dicts_neighbor[j][w])
            stab_vals_lin.append(stability_dicts_linear[j][w])
        data_comb.append(stab_vals_comb)
        data_neigh.append(stab_vals_neigh)
        data_lin.append(stab_vals_lin)

    data_comb = np.array(data_comb)
    sns.heatmap(data_comb, vmin=-0.1, vmax=1.0, yticklabels=yticks, cmap="YlGnBu", cbar=False, ax=ax[0])
    ax[0].set_xlabel("Combined")
    ax[0].set_xticks(list(range(numxticks)))
    ax[0].set_xticklabels(years, rotation=90)

    data_neigh = np.array(data_neigh)
    sns.heatmap(data_neigh, vmin=-0.1, vmax=1.0, yticklabels=yticks, cmap="YlGnBu", cbar=False, ax=ax[1])
    ax[1].set_xlabel("Neighbor-based")
    ax[1].set_xticks(list(range(numxticks)))
    ax[1].set_xticklabels(years, rotation=90)

    data_lin = np.array(data_lin)
    sns.heatmap(data_lin, vmin=-0.1, vmax=1.0, yticklabels=yticks, cmap="YlGnBu", cbar=False, ax=ax[2])
    ax[2].set_xticks(list(range(numxticks)))
    ax[2].set_xlabel("Linear-Mapping")
    ax[2].set_xticklabels(years, rotation=90)

    mkdir(save_dir)
    plt.tight_layout()
    fig = plt.gcf()
    fig.set_size_inches(20, 10)
    fig.tight_layout()
    plt.savefig(os.path.join(save_dir, fig_name + '_stabilities_heatmap.png'))
    plt.close()


def plot_jaccard_similarity_tails(stability_dicts_combined, stability_dicts_neighbor, stability_dicts_linear, n_sizes,
                                  save_dir, fig_name):
    """ get the jaccard similarity between the tails of the different stability
        approaches for different sizes of n. Ideally, because words in tails should be stable,
        they must be present in the tails of any corpus used.
    """
    jaccard_sims_comb, jaccard_sims_neigh, jaccard_sims_lin = [], [], []
    for n in n_sizes:
        # get the jaccard similarity over the "combined"-based dictionaries
        all_tails = []
        for stab_dict in stability_dicts_combined:
            _, tails = get_heads_tails(stab_dict, n, verbose=False)
            all_tails.append(tails)
        jaccard = jaccard_similarity(all_tails)
        jaccard_sims_comb.append(jaccard)

        # get the jaccard similarity over the "neighbor"-based dictionaries
        all_tails = []
        for stab_dict in stability_dicts_neighbor:
            _, tails = get_heads_tails(stab_dict, n, verbose=False)
            all_tails.append(tails)
        jaccard = jaccard_similarity(all_tails)
        jaccard_sims_neigh.append(jaccard)

        # get the jaccard similarity over the "linear"-based dictionaries
        all_tails = []
        for stab_dict in stability_dicts_linear:
            _, tails = get_heads_tails(stab_dict, n, verbose=False)
            all_tails.append(tails)
        jaccard = jaccard_similarity(all_tails)
        jaccard_sims_lin.append(jaccard)

    lines = ["--", "-.", ":"]
    linecycler = cycle(lines)
    plt.figure()
    for i in range(len(lines)):
        if i == 0:
            plt.plot(list(n_sizes), jaccard_sims_comb, next(linecycler), label="Combination")
        elif i == 1:
            plt.plot(list(n_sizes), jaccard_sims_neigh, next(linecycler), label="Neighbors-based")
        else:
            plt.plot(list(n_sizes), jaccard_sims_lin, next(linecycler), label="Linear-Mapping")
    plt.legend()
    plt.xlabel('tail sizes')
    plt.ylabel('jaccard similarity')
    plt.xlim([n_sizes[0], n_sizes[-1]])
    # plt.ylim([0, max(max(jaccard_sims_comb), max(jaccard_sims_neigh), max(jaccard_sims_lin))])
    plt.ylim([0, 0.1])
    mkdir(save_dir)
    plt.savefig(os.path.join(save_dir, fig_name + '_jaccard_similarities.png'))
    plt.close()


def plot_delta_ranks_words(ranks_comb, ranks_neigh, ranks_lin, words,
                           save_dir, fig_name):
    deltas_neigh, deltas_lin = [], []
    words_decoded = []
    for w in words:
        drneigh = ranks_neigh[w] - ranks_comb[w]  # get the delta rank
        drlin = ranks_lin[w] - ranks_comb[w]  # get the delta rank
        deltas_neigh.append(drneigh)  # add to list
        deltas_lin.append(drlin)  # add to list
        words_decoded.append(
            bidialg.get_display(arabic_reshaper.reshape(w)))  # decode arabic word to make it appear in matplotlib
    plt.bar(words_decoded, deltas_neigh, label='Combination vs. Neighbor-based')
    plt.bar(words_decoded, deltas_lin, label='Combination vs. Linear Mapping', bottom=deltas_neigh)
    plt.xticks(rotation=90)
    plt.ylabel(r'$\Delta$' + 'rank')
    plt.legend()
    fig = plt.gcf()
    fig.set_size_inches(12, 6)
    fig.tight_layout()
    mkdir(save_dir)
    plt.savefig(os.path.join(save_dir, fig_name + '_delta_ranks.png'))
    plt.close()


def get_ranks(stability_combined, stability_neighbors, stability_linear):
    # sort the stabilities dictionary by increasing order of stabilities (items at the beginning
    # have low stability - items at the end have high stability)
    stability_combined = {k: v for k, v in sorted(stability_combined.items(), key=lambda item: item[1])}
    stability_neighbors = {k: v for k, v in sorted(stability_neighbors.items(), key=lambda item: item[1])}
    stability_linear = {k: v for k, v in sorted(stability_linear.items(), key=lambda item: item[1])}

    values_combined = list(stability_combined.values())
    values_neighbor = list(stability_neighbors.values())
    values_linear = list(stability_linear.values())

    ranks_combined, ranks_neigh, ranks_lin = [], [], []

    ranks_combined.append(1)  # for the first value, its rank is 1
    ranks_neigh.append(1)  # for the first value, its rank is 1
    ranks_lin.append(1)

    # get the rankings per value for the combined
    rank = 1
    for i in range(1, len(values_combined[1:]) + 1):
        if round(values_combined[i], 5) == round(values_combined[i - 1], 5):
            ranks_combined.append(rank)
        else:
            rank += 1
            ranks_combined.append(rank)
    print(len(ranks_combined) == len(values_combined))

    # get the rankings per value for the neighbors
    rank = 1
    for i in range(1, len(values_neighbor[1:]) + 1):
        if round(values_neighbor[i], 8) == round(values_neighbor[i - 1], 8):
            ranks_neigh.append(rank)
        else:
            rank += 1
            ranks_neigh.append(rank)
    print(len(ranks_neigh) == len(values_neighbor))

    # get the rankings per value for the linear
    rank = 1
    for i in range(1, len(values_linear[1:]) + 1):
        if round(values_linear[i], 8) == round(values_linear[i - 1], 8):
            ranks_lin.append(rank)
        else:
            rank += 1
            ranks_lin.append(rank)
    print(len(ranks_lin) == len(values_linear))

    ranks_combined = dict(zip(list(stability_combined.keys()), ranks_combined))
    ranks_neigh = dict(zip(list(stability_neighbors.keys()), ranks_neigh))
    ranks_lin = dict(zip(list(stability_linear.keys()), ranks_lin))

    return ranks_combined, ranks_neigh, ranks_lin


# cannot decide yet on summary because our words are oov and nearest
# neighs of oov are also oov, should we also get stability values
# for these ?

def get_contrastive_viewpoint_summary(w, n, k, model1, model2, mat_name, dir_name_matrices,
                                      save_dir, file_name, viewpoint1_name='1982', viewpoint2_name='1983',
                                      thresh=0.5):
    """ get a contrastive viewpoint summary of a word of length n. For a certain
        word:
        1. we get its top k nearest neighbors.
        2. Then for each nearest neighbor, we add it into the summary if its stability is equal to or less than a certain threshold.
    """
    summary1, summary2 = [], []

    nns1 = [n[1] for n in model1.get_nearest_neighbors(w, k)]
    nns2 = [n[1] for n in model2.get_nearest_neighbors(w, k)]

    count = 0
    for nn in nns1:
        if count == n:
            break
        st = get_stability_combined_one_word(w=nn, model1=model1, model2=model2, mat_name=mat_name,
                                             dir_name_matrices=dir_name_matrices)

        if st <= thresh:
            summary1.append((st, nn))
            count += 1
    count = 0
    for nn in nns2:
        if count == n:
            break
        st = get_stability_combined_one_word(w=nn, model1=model1, model2=model2, mat_name=mat_name,
                                             dir_name_matrices=dir_name_matrices)

        if abs(st) <= thresh:
            summary2.append((st, nn))
            count += 1

    mkdir(save_dir)
    with open(os.path.join(save_dir, '{}.txt'.format(file_name)), 'a', encoding='utf-8') as f:
        f.write('w: {}\n'.format(w))
        f.write('viewpoint {}\n'.format(viewpoint1_name))
        for i, s in enumerate(summary1):
            if i % 10 != 0 or i == 0:
                f.write(s[1] + ", ")
            else:
                f.write(s[1] + "\n")
        f.writelines('\n')
        f.writelines('\n')
        f.writelines('-------------------------------------------------------------------------------------------\n')
        f.write('w: {}\n'.format(w))
        f.write('viewpoint {}\n'.format(viewpoint2_name))
        for i, s in enumerate(summary2):
            if i % 10 != 0 or i == 0:
                f.write(s[1] + ", ")
            else:
                f.write(s[1] + "\n")
        f.writelines('\n')
        f.writelines('\n')
        f.writelines('========================================================================================================================================')
        f.writelines('\n')
    f.close()

    return summary1, summary2


def perform_paired_t_test(ranks_comb, ranks_neigh, ranks_lin, save_dir, file_name):
    # get test-statistic and p-value results
    result_comb_neigh = stats.ttest_rel(list(ranks_comb.values()), list(ranks_neigh.values()))
    result_comb_lin = stats.ttest_rel(list(ranks_comb.values()), list(ranks_lin.values()))

    # get the average rank of each method
    avg_rank_comb = np.mean(list(ranks_comb.values()))
    avg_rank_neigh = np.mean(list(ranks_neigh.values()))
    avg_rank_lin = np.mean(list(ranks_lin.values()))

    print('avg rank combined: {}'.format(np.mean(list(ranks_comb.values()))))
    print('avg rank neighbors: {}'.format(np.mean(list(ranks_neigh.values()))))
    print('avg rank linear: {}'.format(np.mean(list(ranks_lin.values()))))

    df = pd.DataFrame(columns=['Avg. Rank Comb', 'Avg. Rank Neigh', 'Avg. Rank Lin',
                               'ttest_comb_neigh', 'ttest_comb_lin',
                               'pval_comb_neigh', 'pval_comb_lin'])

    df = df.append({
        'Avg. Rank Comb': avg_rank_comb,
        'Avg. Rank Neigh': avg_rank_neigh,
        'Avg. Rank Lin': avg_rank_lin,
        'ttest_comb_neigh': result_comb_neigh[0],
        'ttest_comb_lin': result_comb_lin[0],
        'pval_comb_neigh': result_comb_neigh[1],
        'pval_comb_lin': result_comb_lin[1]
    }, ignore_index=True)

    if result_comb_neigh[1] < 0.05:
        print(result_comb_neigh)
        print('accept H1 for comb-neigh')
    else:
        print(result_comb_neigh)
        print('accept H0 for comb-neigh')

    if result_comb_lin[1] < 0.05:
        print(result_comb_lin)
        print('accept H1 for comb-lin')
    else:
        print(result_comb_lin)
        print('accept H0 for comb-lin')

    mkdir(save_dir)
    df.to_csv(os.path.join(save_dir, file_name + '.csv'), index=False)


def read_keywords(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        words = f.readlines()
    words = [w[:-1] for w in words if '\n' in w]
    return words


def save_summary(original_word, summary, year, save_dir, filename):
    mkdir(save_dir)
    with open(os.path.join(save_dir, filename + '.txt'), 'a', encoding='utf-8') as f:
        f.write('\nplease manually correct the summaries below for the word: {} in year: {}\n'.format(original_word, year))
        words = [w[1] for w in summary] # words are the neighbors
        for w in words:
            f.write('{}:\n'.format(w))
        f.write('\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n')
    f.close()


def store_summary_corrections(summary, save_dir, filename):
    t1 = time.time()
    corr = Corrector()
    corrections = {}
    words = [w[1] for w in summary]
    for w in words:
        corrections[w] = []
        print('w: {}'.format(w))

        # if the word is correct then no need for doing any corrections
        check = input('does the word {} have a correct spelling ?'.format(w))
        if check == 'y':
            corrections[w].append(w)
            continue

        # if the word contains a space then its a phrase (i.e more than one word)
        if ' ' in w:
            corrc = corr.contextual_correct(w)
            print('correction: {}'.format(corrc))
            include = input('is {} a correct word to include?'.format(corrc))
            if include == 'y':
                corrections[w].append(corrc)
        else:
            for i in range(1, len(w)):
                new_str = w[:i] + ' ' + w[i:]
                print(new_str)
                corrc = corr.contextual_correct(new_str)
                include = input('is {} a correct word to include?'.format(corrc))
                if include == 'y':
                    corrections[w].append(corrc)
                    cont = input('would you like to continue (y) or move to another word (n)?')
                    if cont == 'y':
                        continue
                    else:  # move to another word
                        break
                print('------------------------------')
            if corrections[w] == []:
                addwordmanually = input('Do you want to manually add the correction for word {}'.format(w))
                if addwordmanually == 'y':
                    wordfromuser = input('Please insert the correction: ')
                    corrections[w].append(wordfromuser)
                    print('------------------------------')
        print('=================================================')
    t2 = time.time()
    print('time taken: {} mins'.format((t2 - t1) / 60))
    for k, v in corrections.items():
        print('{}: {}'.format(k, v))
        print('???????????????????????????')
    mkdir(save_dir)
    with open(os.path.join(save_dir, '{}.pkl'.format(filename)), 'wb') as f:
        pickle.dump(corrections, f)
    return corrections


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--path1', default='D:/fasttext_embeddings/ngrams4-size300-window5-mincount100-negative15-lr0.001/ngrams4-size300-window5-mincount100-negative15-lr0.001/', help='path to trained models files for first embedding')
    parser.add_argument('--path2', default='D:/fasttext_embeddings/ngrams4-size300-window5-mincount100-negative15-lr0.001/ngrams4-size300-window5-mincount100-negative15-lr0.001/', help='path to trained models files for second embedding')
    parser.add_argument('--start_year', default='1983', help="start year to get summaries of")
    parser.add_argument('--end_year', default='2009', help="end year to get summaries of")
    parser.add_argument("--archive", default="nahar", help="name of the source archive")
    parser.add_argument("--words_file", default="from_DrFatima/sentiment_keywords.txt", help="path to txt file that contains words of interest")
    parser.add_argument("--dir_name_matrices", default="D:/fasttext_embeddings/results_diachronic_new/", help="path to folder that contains stability values of words")
    args = parser.parse_args()

    path1 = args.path1
    path2 = args.path2

    sentiment_words = read_keywords(args.words_file) # for sentiment/emotion analysis

    years = list(range(int(args.start_year), int(args.end_year)+1))
    paths = [
        os.path.join(args.dir_name_matrices + "{}/".format(args.archive), '{}_{}_{}_{}/t1k100/'.format(args.archive, y-1, args.archive, y)) for y in years
    ]

    results_dir = 'output_diachronic_new/{}/'.format(args.archive)

    for i, path in enumerate(paths):
        if os.path.exists(path):
            dict_combined = os.path.join(path, 'stabilities_combined.pkl')
            print('path: {}'.format(path))

            if os.path.exists(dict_combined):
                # load pickle file of stabilities
                with open(dict_combined, 'rb') as handle:
                    stabilities_comb = pickle.load(handle)
                    print('loaded combined stabilities dictionary from {}'.format(path))
                print('================================================================')

            model1 = fasttext.load_model(os.path.join(path1, '{}.bin'.format(years[i] - 1)))
            model2 = fasttext.load_model(os.path.join(path2, '{}.bin'.format(years[i])))

            print('loaded model1: {}'.format(os.path.join(path1, '{}.bin'.format(years[i] - 1))))
            print('loaded model2: {}'.format(os.path.join(path1, '{}.bin'.format(years[i]))))

            dir_name_matrices = os.path.join(args.dir_name_matrices, '{}/{}_{}_{}_{}/linear_numsteps80000/matrices/'.format(args.archive, args.archive, str(years[i] - 1), args.archive, str(years[i])))

            # create a mapping between word and a numeric index
            word2idx = dict(zip(sentiment_words, list(range(len(sentiment_words)))))
            years_checked = {}
            for z, w in enumerate(sentiment_words):

                summary_v1, summary_v2 = get_contrastive_viewpoint_summary(w, n=20, k=100, model1=model1, model2=model2,
                                                                           mat_name='trans',
                                                                           dir_name_matrices=dir_name_matrices,
                                                                           save_dir=results_dir + 'summaries/',
                                                                           file_name='sentiment_keywords',
                                                                           viewpoint1_name='{}'.format(years[i] - 1),
                                                                           viewpoint2_name='{}'.format(years[i]),
                                                                           thresh=0.5)

                if w not in years_checked:
                    years_checked[w] = []

                if years[i] - 1 not in years_checked[w]:
                    # save_summary(original_word=w, summary=summary_v1, year=years[i] - 1, save_dir='summaries/manual/', filename='summaries_azarbonyad')
                    save_summary(original_word=w, summary=summary_v1, year=years[i] - 1, save_dir='summaries_new/manual/{}/'.format(args.archive), filename='summaries_azarbonyad')
                    # save_summary(original_word=w, summary=summary_v1, year=years[i] - 1, save_dir='summaries_new/manual/assafir/', filename='summaries_azarbonyad')
                    years_checked[w].append(years[i] - 1)

                if years[i] not in years_checked[w]:
                    # save_summary(original_word=w, summary=summary_v2, year=years[i], save_dir='summaries/manual/', filename='summaries_azarbonyad')
                    save_summary(original_word=w, summary=summary_v2, year=years[i], save_dir='summaries_new/manual/{}/'.format(args.archive), filename='summaries_azarbonyad')
                    # save_summary(original_word=w, summary=summary_v2, year=years[i], save_dir='summaries_new/manual/assafir/', filename='summaries_azarbonyad')
                    years_checked[w].append(years[i])