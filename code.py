from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout
from PyQt5.QtGui import QPalette, QColor
import folium
from opencage.geocoder import OpenCageGeocode
import geopy.distance as geodesic
import networkx as nx

class LocationPlotterGUI(QWidget):
    def _init_(self):
        super()._init_()

        self.setWindowTitle("Location Plotter")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.city_label = QLabel("Enter the name of the city:")
        layout.addWidget(self.city_label)

        self.city_entry = QLineEdit()
        layout.addWidget(self.city_entry)

        self.location_label = QLabel("Enter locations to pin on the map. Type 'done' when finished:")
        layout.addWidget(self.location_label)

        self.location_entry = QLineEdit()
        layout.addWidget(self.location_entry)

        self.add_location_button = QPushButton("Add Location", clicked=self.add_location)
        layout.addWidget(self.add_location_button)

        self.plot_map_button = QPushButton("Plot Map", clicked=self.plot_map)
        layout.addWidget(self.plot_map_button)

        self.remove_edge_button = QPushButton("Remove Edge", clicked=self.remove_edge_gui)
        layout.addWidget(self.remove_edge_button)
        
        self.edge_remove_entry = QLineEdit()
        layout.addWidget(self.edge_remove_entry)

        self.setLayout(layout)

        self.locations = []
        self.graph = nx.Graph()

        # Apply styles for a colorful appearance
        self.apply_styles()

    def apply_styles(self):
        # Create a color palette
        palette = QPalette()

        # Background color
        palette.setColor(QPalette.Window, QColor(140, 140, 140))

        # Label text color
        palette.setColor(QPalette.WindowText, QColor(70, 70, 70))

        # Button colors
        palette.setColor(QPalette.Button, QColor(100, 160, 220))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        # Apply the palette to the application
        self.setPalette(palette)

        # Apply stylesheets for additional styling
        self.setStyleSheet(
            "QLineEdit { background-color: white; border: 1px solid gray; border-radius: 5px; }"
            "QPushButton { background-color: #649CDB; color: white; border: 1px solid #649CDB; border-radius: 5px; }"
            "QPushButton:hover { background-color: #3A77B9; }"
        )

    def get_coordinates(self, location):
        key = 'a2f071dc6740461695cc469750431092'  
        geocoder = OpenCageGeocode(key)

        results = geocoder.geocode(location)
        if results and len(results):
            first_result = results[0]
            return first_result['geometry']['lat'], first_result['geometry']['lng']
        else:
            print(f"Could not find coordinates for {location}")
            return None

    def calculate_distance(self, coord1, coord2):
        return geodesic.distance(coord1, coord2).kilometers

    def add_location(self):
        location = self.location_entry.text()
        if location.lower() != 'done':
            self.locations.append(location)
            self.location_entry.clear()

    def plot_map(self):
        city_name = self.city_entry.text()
        locations = self.locations

        city_coordinates = self.get_coordinates(city_name)
        if city_coordinates is None:
            print("Unable to get coordinates for the city.")
            return None

        # Clear existing graph
        self.graph.clear()

        # Create the first map
        map_object = folium.Map(location=city_coordinates, zoom_start=12)

        for i, location1 in enumerate(locations):
            coordinates1 = self.get_coordinates(location1)
            if coordinates1 is None:
                continue

            for j, location2 in enumerate(locations):
                if i != j:
                    coordinates2 = self.get_coordinates(location2)
                    if coordinates2 is not None:
                        distance = self.calculate_distance(coordinates1, coordinates2)
                        self.graph.add_edge(location1, location2, weight=distance)

        # Plotting with Christofides' Algorithm
        christofides_edges = self.christofides_algorithm(self.graph)
        
        total_length1 = 0
        for edge in christofides_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                folium.Marker(location=coordinates1, popup=edge[0]).add_to(map_object)
                folium.Marker(location=coordinates2, popup=edge[1]).add_to(map_object)
                folium.PolyLine([coordinates1, coordinates2], color="blue", weight=2.5).add_to(map_object)

                if edge[0] in self.graph and edge[1] in self.graph[edge[0]]:
                    total_length1 += self.graph[edge[0]][edge[1]]['weight']

        map_file_christofides = f"{city_name}_map_with_christofides_algorithm.html"
        map_object.save(map_file_christofides)
        print(f"\nCity map with Christofides' Algorithm saved as '{map_file_christofides}'")
        print(f"\nTotal length of edges in Plan A: {total_length1:.2f} kilometers")
        self.cost_of_costruction(total_length1)
        
        map_object = folium.Map(location=city_coordinates, zoom_start=12)

        # Continue with the rest of your code (e.g., plotting using Prim's algorithm)
        min_spanning_tree_edges = self.prim_algorithm(self.graph)

        for edge in min_spanning_tree_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                folium.Marker(location=coordinates1, popup=edge[0]).add_to(map_object)
                folium.Marker(location=coordinates2, popup=edge[1]).add_to(map_object)
                folium.PolyLine([coordinates1, coordinates2], color="red", weight=2.5).add_to(map_object)

        total_length2 = 0
        for edge in min_spanning_tree_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                total_length2 += self.graph[edge[0]][edge[1]]['weight']

        map_file_prims = f"{city_name}_map_with_mst_prims.html"
        map_object.save(map_file_prims)
        print(f"City map with Minimum Spanning Tree (Prim's algorithm) saved as '{map_file_prims}'")
        print(f"\nTotal length of edges in Plan B: {total_length2:.2f} kilometers")
        self.cost_of_costruction(total_length2)
        
    def cost_of_costruction(self,tot_dis):
        nodes=len(self.locations)
        
        print('\nUnderGround Metro by Tunneling')
        track_cost_u=tot_dis*125
        station_cost_u=nodes*5
        total_cost_u=track_cost_u+station_cost_u
        print(f'Total metro construction cost {total_cost_u:.2f} crores')
            
        print('\nElevated Metro by Bridges and Pillars')
        track_cost_e=tot_dis*37
        station_cost_e=nodes*8
        total_cost_e=track_cost_e+station_cost_e
        print(f'Total metro construction cost {total_cost_e:.2f} crores')
        
        
    def christofides_algorithm(self, graph):
        # Create a minimum spanning tree using Prim's algorithm
        min_spanning_tree_edges = self.prim_algorithm(graph)

        # Create a multigraph to handle odd-degree vertices
        multigraph = nx.MultiGraph(graph)
        multigraph.add_edges_from(min_spanning_tree_edges)

        # Find vertices with odd degree
        odd_degree_vertices = [node for node, degree in multigraph.degree() if degree % 2 == 1]

        # Find minimum-weight perfect matching on the subgraph induced by odd-degree vertices
        min_weight_matching_edges = self.minimum_weight_matching(multigraph, odd_degree_vertices)

        # Combine minimum spanning tree and minimum-weight perfect matching
        eulerian_circuit = self.combine_edges(min_spanning_tree_edges, min_weight_matching_edges)

        # Remove duplicates to get a Hamiltonian circuit
        hamiltonian_circuit = list(dict.fromkeys(eulerian_circuit))

        return hamiltonian_circuit

    def minimum_weight_matching(self, graph, vertices):
        # Convert multigraph to simple graph
        simple_graph = nx.Graph(graph)

        # Use max_weight_matching and remove duplicates to get minimum-weight perfect matching
        matching_edges = nx.algorithms.max_weight_matching(simple_graph, maxcardinality=True, weight='weight')
        return list(matching_edges)

    def combine_edges(self, edges1, edges2):
        # Combine two sets of edges into a single list
        combined_edges = []
        for edge in edges1:
            combined_edges.append(edge)
        for edge in edges2:
            combined_edges.append(edge)
        return combined_edges
    
    def prim_algorithm(self, graph):
        visited = set()
        start_node = list(graph.nodes)[0]
        visited.add(start_node)

        min_spanning_tree_edges = []

        while len(visited) < len(graph.nodes):
            min_edge = None
            min_edge_weight = float('inf')

            for node in visited:
                for neighbor, data in graph[node].items():
                    if neighbor not in visited and data['weight'] < min_edge_weight:
                        min_edge = (node, neighbor)
                        min_edge_weight = data['weight']

            min_spanning_tree_edges.append(min_edge)
            visited.add(min_edge[1])

        return min_spanning_tree_edges

    def remove_edge_gui(self):
        # Get edge to remove from the QLineEdit
        edge_to_remove = self.edge_remove_entry.text().split()
        
        if len(edge_to_remove) != 2:
            print("Invalid input. Please enter two locations separated by a space.")
            return

        location1, location2 = edge_to_remove
        if (location1, location2) in self.graph.edges or (location2, location1) in self.graph.edges:
            # Remove the edge from the graph
            self.graph.remove_edge(location1, location2)
            print(f"Edge ({location1}, {location2}) removed.")
        else:
            print(f"Edge ({location1}, {location2}) not found in the graph.")

        # Continue with plotting the updated graph
        self.plot_map_without_edge(location1, location2)
        
    def plot_map_without_edge(self,point1, point2):
        city_name = self.city_entry.text()
        locations = self.locations

        city_coordinates = self.get_coordinates(city_name)
        if city_coordinates is None:
            print("Unable to get coordinates for the city.")
            return None

        # Clear existing graph
        self.graph.clear()

        # Create the first map
        map_object = folium.Map(location=city_coordinates, zoom_start=12)

        for i, location1 in enumerate(locations):
            coordinates1 = self.get_coordinates(location1)
            if coordinates1 is None:
                continue

            for j, location2 in enumerate(locations):
                if i != j:
                    coordinates2 = self.get_coordinates(location2)
                    if coordinates2 is not None:
                        if location1!=point1 and location2!=point2:
                            distance = self.calculate_distance(coordinates1, coordinates2)
                            self.graph.add_edge(location1, location2, weight=distance)

        # Plotting with Christofides' Algorithm
        christofides_edges = self.christofides_algorithm(self.graph)
        
        total_length1 = 0
        for edge in christofides_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                folium.Marker(location=coordinates1, popup=edge[0]).add_to(map_object)
                folium.Marker(location=coordinates2, popup=edge[1]).add_to(map_object)
                folium.PolyLine([coordinates1, coordinates2], color="blue", weight=2.5).add_to(map_object)

                if edge[0] in self.graph and edge[1] in self.graph[edge[0]]:
                    total_length1 += self.graph[edge[0]][edge[1]]['weight']

        map_file_christofides = f"{city_name}_map_with_christofides_algorithm_new.html"
        map_object.save(map_file_christofides)
        print(f"\nCity map with Christofides' Algorithm saved as '{map_file_christofides}'")
        print(f"\nTotal length of edges in Plan A_new: {total_length1:.2f} kilometers")
        self.cost_of_costruction(total_length1)
        
        map_object = folium.Map(location=city_coordinates, zoom_start=12)

        # Continue with the rest of your code (e.g., plotting using Prim's algorithm)
        min_spanning_tree_edges = self.prim_algorithm(self.graph)

        for edge in min_spanning_tree_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                folium.Marker(location=coordinates1, popup=edge[0]).add_to(map_object)
                folium.Marker(location=coordinates2, popup=edge[1]).add_to(map_object)
                folium.PolyLine([coordinates1, coordinates2], color="red", weight=2.5).add_to(map_object)

        total_length2 = 0
        for edge in min_spanning_tree_edges:
            coordinates1 = self.get_coordinates(edge[0])
            coordinates2 = self.get_coordinates(edge[1])
            if coordinates1 is not None and coordinates2 is not None:
                total_length2 += self.graph[edge[0]][edge[1]]['weight']

        map_file_prims = f"{city_name}_map_with_mst_prims_new.html"
        map_object.save(map_file_prims)
        print(f"City map with Minimum Spanning Tree (Prim's algorithm) saved as '{map_file_prims}'")
        print(f"\nTotal length of edges in Plan B_new: {total_length2:.2f} kilometers")
        self.cost_of_costruction(total_length2)

app = QApplication([])
window = LocationPlotterGUI()
window.show()
app.exec_()