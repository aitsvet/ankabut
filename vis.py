from pyvis.network import Network
import numpy as np

def visualize_authors_keywords(db, dst):
    correlation_matrix = np.array([[1, 0.8, 0.3], [0.8, 1, 0.5], [0.3, 0.5, 1]])
    distance_matrix = 1 - correlation_matrix

    net = Network()
    for i in range(len(distance_matrix)):
        for j in range(i + 1, len(distance_matrix)):
            net.add_node(i)
            net.add_node(j)
            net.add_edge(i, j, weight=distance_matrix[i][j])

    net.toggle_physics(True)
    net.show_buttons(True)
    net.show(dst, notebook=False)