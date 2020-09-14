

def print_results(dir_name,attacker_budget,results, alg='minimax'):
    with open(dir_name+'/'+alg+'/attacker_budget_'+str(attacker_budget)+'.csv', 'w', newline='') as csvfile:
        fieldnames = [alg+'_attacker_budget', alg+'_defender_budget', alg+'_attacker_cost',
                      alg+'_defender_cost', alg+'_value', alg+'_funds', alg+'_actions']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)