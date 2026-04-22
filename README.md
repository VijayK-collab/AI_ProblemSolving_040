🧠 1. Map Coloring Problem
📌 Problem Description

The Map Coloring Problem is a classic problem in graph theory where each region (node) of a map must be colored such that:

No two adjacent regions share the same color
The total number of colors used is minimized

This problem is widely used in:

Map design
Register allocation in compilers
Scheduling problems
⚙️ Algorithms Used
1. Greedy Algorithm
Assigns the smallest possible color to each node
Fast but not always optimal
2. Welsh-Powell Algorithm
Sorts nodes based on degree (highest first)
Produces better results than simple greedy
3. DSatur Algorithm
Chooses node with highest saturation (different neighbor colors)
Often gives near-optimal solutions
4. Backtracking Algorithm
Tries all possibilities
Guarantees minimum number of colors
Slower for large graphs
▶️ Execution Steps

Run the program:

python MapColoringProblem.py
Choose mode:
Add Node
Add Edge
Delete / Move
Create a graph manually or load preset
Select algorithm from dropdown
Click Run Coloring
View:
Colored graph
Statistics (colors used, time, steps)
📊 Sample Output

Example:

Algorithm: Welsh-Powell
Nodes: 7
Edges: 9
Colors Used: 3
Steps: 7
Time: 1.25 ms

Visual Output:

Nodes colored differently
No adjacent nodes share same color
🚌 2. School Bus Route Optimization
📌 Problem Description

This project solves a simplified Vehicle Routing Problem (VRP):

Multiple buses must pick up students
Each bus has limited capacity
Total travel distance should be minimized

Goal:

Efficiently assign stops to buses
Optimize route paths
⚙️ Algorithms Used
1. Nearest Neighbor
Starts from depot/school
Visits nearest unvisited stop
Simple and fast
2. 2-Opt Optimization
Improves an existing route
Swaps edges to reduce distance
Removes unnecessary path crossings
3. Cluster-then-Route
Groups stops using clustering (k-means style)
Then applies routing within each cluster
Balances load across buses
▶️ Execution Steps

Run the program:

python SchoolBusRouteOptimization.py
Place elements:
School 🏫
Depot 🏭
Bus Stops 📍
Configure:
Number of buses
Capacity per bus
Choose algorithm
Click Optimize Routes
(Optional) Click Animate Route
📊 Sample Output

Example:

Algorithm: Cluster-then-Route
Total Stops: 12
Total Students: 84
Buses Used: 3
Total Distance: 1250 px
Average Distance: 416 px
Time: 3.45 ms

Route Example:

Bus 1:
DEPOT → S1 → S4 → S6 → SCHOOL
Students: 28/30

Bus 2:
DEPOT → S2 → S5 → S8 → SCHOOL
Students: 26/30

Visual Output:

Colored routes for each bus
Distance labels between stops
Animated movement of buses
📦 Project Structure
├── MapColoringProblem.py
├── SchoolBusRouteOptimization.py
└── README.md
🎯 Learning Outcomes

These projects help understand:

Graph Coloring & Chromatic Number
Greedy vs Optimal Algorithms
Heuristic Optimization Techniques
Real-world applications of algorithms
GUI-based algorithm visualization
🧑‍💻 Author

Vijay K

📜 License

This project is free for educational and academic use.
