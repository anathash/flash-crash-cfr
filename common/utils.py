def init_sigma(node, output = None):
    output = dict()
    def init_sigma_recursive(node):
        inf = node.inf_set()
        if inf in output:
            for action in node.actions:
                if action not in output[inf]:
                    print('stop')
        output[node.inf_set()] = {str(action): 1. / len(node.actions) for action in node.actions}
        for k in node.children:
            init_sigma_recursive(node.children[k])
    init_sigma_recursive(node)
    return output

def init_empty_node_maps(node, output = None):
    output = dict()
    def init_empty_node_maps_recursive(node):
        output[node.inf_set()] = {action: 0. for action in node.actions}
        for k in node.children:
            init_empty_node_maps_recursive(node.children[k])
    init_empty_node_maps_recursive(node)
    return output
