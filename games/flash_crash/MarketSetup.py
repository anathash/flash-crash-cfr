import sys

import numpy
import numpy as np

'TODO: factor in initial price and market cap of assets'


def gen_bipartite_network(num_funds, num_assets, density, pref_attach, initial_capital, initial_leverage, sigma):
    a = np.zeros((num_funds, num_assets), numpy.int8)
    for i in range(num_funds):
        investments = {}
        total = a.sum(axis=1)
        for j in range(num_assets):
            investments[j] = total[j]
        rank = [0] * num_assets
        index = 1
        rank_sum = 0
        'Calculate preferential probability of selecting each asset'
        for (k, v) in sorted(investments.items(), key=lambda kv: kv[1]):
            asset_index = int(k)
            rank[asset_index] = index
            'prefer to scatter'
            if pref_attach < 0:
                rank[asset_index] = num_assets - rank[asset_index] + 1
            rank_sum += pow(index, pref_attach)
            index += 1

        asset_selection_prob = [0] * num_assets
        for j in range(num_assets):
            asset_selection_prob[j] = rank[j]/rank_sum
        'Calculate fund fractional investment to assets'
        'TODO: factor in initial asset price and make sure values are multiplications of single share price'
        frac = np.random.normal(density, sigma, 1)
        k_fund = min(max(int(frac * num_assets), 1), num_assets)
        'TODO: make sure distinct'
        assets_selected = np.random.choice(num_assets, k_fund, False, asset_selection_prob)
        'why is it important that its in descending order'
        investment_portions = np.random.normal(0, 1, k_fund)
        sum_inv = sum(investment_portions)
        normed_investment_portions = list(map(lambda x: x/sum_inv, investment_portions))
        for k in range(k_fund):
            a[i][assets_selected[k]] = normed_investment_portions[k]
        available_cash = initial_capital * (1 + initial_leverage)
        for j in range(num_assets):
            a[i][j] = int(round(available_cash * a[i][j]))
    return a


'Construct board and save class to file'
def save_netwrok_to_file(file_name, num_funds, num_assets, initial_capital, initial_leverage):
    params = {}

    params['num_funds'] = str(num_funds)
    params['num_assets'] = str(num_assets)
    initial_capitals = [initial_capital] * num_funds
    params['initial_capitals'] = str(initial_capitals)
    initial_leverages = [initial_leverage] * num_funds
    params['initial_leverages'] = str(initial_leverages)
    mtrx_str = ''
    for i in range(num_funds):
        for j in range(num_assets):
            mtrx_str += str(a[i][j]) + ','
        mtrx_str += ';'
    params['portfolio_matrix'] = mtrx_str

    np.save(file_name, params)
    return

def gen_network_and_save_to_file(file_name, num_funds, num_assets, density, pref_attach,
                                 initial_capital, initial_leverage, sigma):
    a = gen_bipartite_network(num_funds, num_assets, density, pref_attach, initial_capital, initial_leverage, sigma)
    params = {}

    params['num_funds'] = str(num_funds)
    params['num_assets'] = str(num_assets)
    initial_capitals = [initial_capital] * num_funds
    params['initial_capitals'] = str(initial_capitals)
    initial_leverages = [initial_leverage] * num_funds
    params['initial_leverages'] = str(initial_leverages)
    mtrx_str = ''
    for i in range(num_funds):
        for j in range(num_assets):
            mtrx_str += str(a[i][j]) + ','
        mtrx_str += ';'
    params['portfolio_matrix'] = mtrx_str

    np.save(file_name, params)
    return


if __name__ == '__main__':
    gen_network_and_save_to_file('../test/a.txt', 4, 3, 1, 1, 100, 2, 1)
"f.writelines(','.join(str(j) for j in i) + '\n' for i in a)"