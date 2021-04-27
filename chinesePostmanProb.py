import itertools
import copy
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

def get_shortest_paths_distances(graph, pairs, edge_weight_name):
    distances = {}
    for pair in pairs:
        distances[pair] = nx.dijkstra_path_length(graph, pair[0], pair[1], weight=edge_weight_name)
    return distances

def create_complete_graph(pair_weights, flip_weights=True):
    g = nx.Graph()
    for k, v in pair_weights.items():
        wt_i = -v if flip_weights else v
        g.add_edge(k[0], k[1], **{'distance': v, 'weight':wt_i})
    return g

def add_augmenting_path_to_graph(graph, min_weight_pairs):
    graph_aug = nx.MultiGraph(graph.copy())
    for pair in min_weight_pairs:
        graph_aug.add_edge(pair[0], pair[1], **{'distance': nx.dijkstra_path_length(graph, pair[0], pair[1]), 'trail': 'augmented'})
    return graph_aug

def create_eulerian_circuit(graph_augmented, graph_original, starting_node=None):
    euler_circuit = []
    naive_circuit = list(nx.eulerian_circuit(graph_augmented, source=starting_node))

    for edge in naive_circuit:
        edge_data = graph_augmented.get_edge_data(edge[0], edge[1])

        if edge_data[0]['trail'] != 'augmented':
            edge_att = graph_original[edge[0]][edge[1]]
            euler_circuit.append((edge[0], edge[1], edge_att))
        else:
            aug_path = nx.shortest_path(graph_original, edge[0], edge[1], weight='distance')
            aug_path_pairs = list(zip(aug_path[:-1], aug_path[1:]))

            print('Filling in edges for augmented edge: {}'.format(edge))
            print('Augmenting path: {}'.format(' => '.join(aug_path)))
            print('Augmenting path pairs: {}\n'.format(aug_path_pairs))

            for edge_aug in aug_path_pairs:
                edge_aug_att = graph_original[edge_aug[0]][edge_aug[1]]
                euler_circuit.append((edge_aug[0], edge_aug[1], edge_aug_att))

    return euler_circuit

def create_cpp_edgelist(euler_circuit):
    cpp_edgelist = {}

    for i, e in enumerate(euler_circuit):
        edge = frozenset([e[0], e[1]])
        if edge in cpp_edgelist:
            cpp_edgelist[edge][2]['sequence'] += ', ' + str(i)
            cpp_edgelist[edge][2]['visits'] += 1
        else:
            cpp_edgelist[edge] = e
            cpp_edgelist[edge][2]['sequence'] = str(i)
            cpp_edgelist[edge][2]['visits'] = 1
    return list(cpp_edgelist.values())


edgelist = pd.read_csv('edgelist.csv')
nodelist = pd.read_csv('nodelist.csv')

g = nx.Graph()

for i, elrow in edgelist.iterrows():
    g.add_edge(elrow[0], elrow[1], **elrow[2:].to_dict())

for i, nlrow in nodelist.iterrows():
    nx.set_node_attributes(g, {nlrow['id']: nlrow[1:].to_dict()})

node_positions = {node[0]: (node[1]['X'], -node[1]['Y']) for node in g.nodes(data=True)}

edge_colors = [e[2]['color'] for e in list(g.edges(data=True))]

nodes_odd_degree = [v for v, d in g.degree() if d % 2 == 1]

odd_node_pairs = list(itertools.combinations(nodes_odd_degree, 2))

odd_node_pairs_shortest_paths = get_shortest_paths_distances(g, odd_node_pairs, 'distance')

g_odd_complete = create_complete_graph(odd_node_pairs_shortest_paths,flip_weights=True)

odd_matching = nx.algorithms.max_weight_matching(g_odd_complete, True)

g_aug = add_augmenting_path_to_graph(g, odd_matching)

euler_circuit = create_eulerian_circuit(g_aug, g, 'stadium')

cpp_edgelist = create_cpp_edgelist(euler_circuit)

g_cpp = nx.Graph(cpp_edgelist)

plt.figure(figsize=(20,16))

edge_colors = [e[2]['color'] for e in g_cpp.edges(data=True)]
nx.draw_networkx(g_cpp, pos=node_positions, node_size=10, node_color='black', edge_color=edge_colors, with_labels=False, alpha=.5)
edge_labels = nx.get_edge_attributes(g_cpp, 'sequence')
nx.draw_networkx_edge_labels(g_cpp, pos=node_positions, edge_labels=edge_labels, font_size=6)
plt.axis('off')
plt.show()
