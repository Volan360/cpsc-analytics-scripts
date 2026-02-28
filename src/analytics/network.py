"""Network analysis module using NetworkX for relationship analytics."""

from typing import List, Dict, Any, Tuple, Set
from datetime import datetime
import networkx as nx
from collections import defaultdict

from ..data.data_models import Transaction, Institution, Goal
from ..utils import date_utils


class NetworkAnalytics:
    """Analyze relationships between financial entities using graph theory."""
    
    def __init__(self, db_client):
        """
        Initialize network analytics.
        
        Args:
            db_client: DynamoDB client for data access
        """
        self.db_client = db_client
    
    def analyze(
        self,
        user_id: str,
        start_date: str = None,
        end_date: str = None,
        graph_type: str = 'financial_flow'
    ) -> Dict[str, Any]:
        """
        Analyze network relationships for a user.

        For ``goal_institution`` graphs the full transaction history is always
        used (no date filter) so that completed/inactive goals — whose
        ``linked_transactions`` were created at completion time — are always
        connected to their institutions regardless of the requested period.

        For ``financial_flow`` and ``tag_network`` graphs, ``start_date`` and
        ``end_date`` are required and transactions are filtered to that window.

        Args:
            user_id: User identifier
            start_date: Analysis start date (ISO format); not used for goal_institution
            end_date: Analysis end date (ISO format); not used for goal_institution
            graph_type: 'financial_flow' | 'goal_institution' | 'tag_network'

        Returns:
            Dictionary containing graph analysis results
        """
        institutions = self.db_client.get_institutions(user_id)
        goals = self.db_client.get_goals(user_id)

        if graph_type == 'goal_institution':
            # Fetch ALL transactions — no date filter — so inactive goals whose
            # completion transactions fall outside any requested window are still
            # linked to their institutions.
            all_transactions = self.db_client.get_all_user_transactions(user_id)
            graph = self.build_goal_institution_graph(institutions, goals, all_transactions)
        elif graph_type in ('financial_flow', 'tag_network'):
            start_ts = date_utils.iso_to_timestamp(start_date)
            end_ts = date_utils.iso_to_timestamp(end_date)
            transactions = self.db_client.get_all_user_transactions(
                user_id, start_ts, end_ts
            )
            if graph_type == 'financial_flow':
                graph = self.build_financial_flow_graph(transactions, institutions, goals)
            else:
                graph = self.build_tag_network(transactions)
        else:
            raise ValueError(f"Unknown graph_type: {graph_type}")

        # Calculate metrics
        centrality = self.calculate_centrality_metrics(graph)
        communities = self.detect_communities(graph)

        result = {
            'user_id': user_id,
            'graph_type': graph_type,
            'graph_stats': {
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges(),
                'density': nx.density(graph) if graph.number_of_nodes() > 1 else 0.0,
                'is_connected': nx.is_connected(graph.to_undirected()) if graph.number_of_nodes() > 0 else False
            },
            'nodes': self._serialize_nodes(graph),
            'edges': self._serialize_edges(graph),
            'centrality': centrality,
            'communities': communities,
        }
        # Only include period when dates were actually applied
        if graph_type != 'goal_institution' and start_date and end_date:
            result['period'] = {'start': start_date, 'end': end_date}
        return result
    
    def build_financial_flow_graph(
        self,
        transactions: List[Transaction],
        institutions: List[Institution],
        goals: List[Goal]
    ) -> nx.DiGraph:
        """
        Build a directed graph showing money flow between entities.
        
        Nodes: Institutions, Goals, Transaction Categories
        Edges: Money flow (weighted by amount)
        
        Args:
            transactions: List of transactions
            institutions: List of institutions
            goals: List of goals
        
        Returns:
            NetworkX DiGraph
        """
        G = nx.DiGraph()
        
        # Add institution nodes
        for inst in institutions:
            G.add_node(
                f"inst_{inst.institution_id}",
                type='institution',
                name=inst.institution_name,
                balance=inst.current_balance
            )
        
        # Add goal nodes
        for goal in goals:
            # Calculate current amount based on linked institutions
            current_amount = goal.calculate_current_amount(institutions) if institutions else 0.0
            G.add_node(
                f"goal_{goal.goal_id}",
                type='goal',
                name=goal.name,
                target=goal.target_amount,
                current=current_amount
            )
        
        # Add category nodes and edges from transactions
        institution_category_flows = defaultdict(lambda: defaultdict(float))
        
        for txn in transactions:
            inst_node = f"inst_{txn.institution_id}"
            
            for tag in txn.tags:
                category_node = f"cat_{tag}"
                
                # Add category node if not exists
                if category_node not in G:
                    G.add_node(category_node, type='category', name=tag)
                
                # Track flow from institution to category (only count WITHDRAWALs)
                if txn.type == 'WITHDRAWAL':
                    institution_category_flows[inst_node][category_node] += txn.amount
        
        # Add edges for institution -> category flows (only if institution exists in graph)
        for inst_node, categories in institution_category_flows.items():
            if inst_node in G:  # Only add edge if institution node exists
                for cat_node, amount in categories.items():
                    G.add_edge(inst_node, cat_node, weight=amount, flow_type='spending')
        
        # Add edges for goal allocations
        for goal in goals:
            goal_node = f"goal_{goal.goal_id}"
            for inst_id, percentage in goal.linked_institutions.items():
                inst_node = f"inst_{inst_id}"
                if inst_node in G:
                    # Weight by goal target amount * percentage
                    weight = goal.target_amount * (percentage / 100.0)
                    G.add_edge(inst_node, goal_node, weight=weight, flow_type='allocation')

        # For inactive goals, also derive institution links from linked_transactions
        txn_lookup = {txn.transaction_id: txn for txn in transactions}
        for goal in goals:
            if not goal.is_active and goal.linked_transactions:
                goal_node = f"goal_{goal.goal_id}"
                for txn_id in goal.linked_transactions:
                    txn = txn_lookup.get(txn_id)
                    if txn:
                        inst_node = f"inst_{txn.institution_id}"
                        if inst_node in G and not G.has_edge(inst_node, goal_node):
                            G.add_edge(
                                inst_node, goal_node,
                                weight=0, flow_type='inactive_allocation'
                            )

        return G
    
    def build_goal_institution_graph(
        self,
        institutions: List[Institution],
        goals: List[Goal],
        transactions: List[Transaction] = None
    ) -> nx.Graph:
        """
        Build an undirected graph showing goal-institution relationships.

        Active goals are linked to institutions via their ``linked_institutions``
        allocation map.  Inactive goals (``is_active=False``) are linked to an
        institution when they contain at least one transaction in
        ``linked_transactions`` whose ``institution_id`` matches that institution.
        
        Args:
            institutions: List of institutions
            goals: List of goals
            transactions: Optional list of transactions used to resolve
                institution links for inactive goals
        
        Returns:
            NetworkX Graph
        """
        G = nx.Graph()
        
        # Add institution nodes
        for inst in institutions:
            G.add_node(
                f"inst_{inst.institution_id}",
                type='institution',
                name=inst.institution_name,
                balance=inst.current_balance
            )
        
        # Add goal nodes and edges
        for goal in goals:
            goal_node = f"goal_{goal.goal_id}"
            current_amount = goal.calculate_current_amount(institutions) if institutions else 0.0
            G.add_node(
                goal_node,
                type='goal',
                name=goal.name,
                target=goal.target_amount,
                current=current_amount,
                is_completed=goal.is_completed,
                is_active=goal.is_active
            )
            
            # Add edges with allocation percentages (active goals use linked_institutions)
            for inst_id, percentage in goal.linked_institutions.items():
                inst_node = f"inst_{inst_id}"
                if inst_node in G:
                    G.add_edge(
                        inst_node,
                        goal_node,
                        weight=percentage,
                        allocation=percentage
                    )

        # For inactive goals, also derive institution links from linked_transactions.
        # Use the actual transaction amounts so the edge weight reflects real money moved.
        # Pre-sum per (inst, goal) pair to handle multiple transactions to the same institution.
        txn_lookup = {txn.transaction_id: txn for txn in transactions} if transactions else {}
        if transactions:
            for goal in goals:
                if not goal.is_active and goal.linked_transactions:
                    goal_node = f"goal_{goal.goal_id}"
                    # Accumulate amounts per institution before adding edges
                    inst_amounts: Dict[str, float] = defaultdict(float)
                    for txn_id in goal.linked_transactions:
                        txn = txn_lookup.get(txn_id)
                        if txn:
                            inst_amounts[txn.institution_id] += txn.amount
                    for inst_id, amount in inst_amounts.items():
                        inst_node = f"inst_{inst_id}"
                        # Only add if the edge wasn't already created via linked_institutions
                        if inst_node in G and not G.has_edge(inst_node, goal_node):
                            G.add_edge(
                                inst_node,
                                goal_node,
                                weight=amount,
                                allocation=None
                            )

        # Add aggregated tag nodes: goal-linked transactions → goal→tag edges;
        # all other transactions → institution→tag edges
        if transactions:
            # Map txn_id -> goal_node for every transaction referenced by a goal
            txn_to_goal: Dict[str, str] = {}
            for goal in goals:
                for txn_id in goal.linked_transactions:
                    txn_to_goal[txn_id] = f"goal_{goal.goal_id}"

            # Accumulate amounts by (source_node, tag)
            tag_flows: Dict[Tuple[str, str], float] = defaultdict(float)
            for txn in transactions:
                linked_goal = txn_to_goal.get(txn.transaction_id)
                if linked_goal and linked_goal in G:
                    source = linked_goal
                else:
                    source = f"inst_{txn.institution_id}"
                    if source not in G:
                        continue
                for tag in txn.tags:
                    # Skip goal-completion tag — the inst→goal edge already represents this flow
                    if tag == 'goal-completion':
                        continue
                    tag_flows[(source, tag)] += txn.amount

            # Add tag nodes and edges
            for (source, tag), total in tag_flows.items():
                tag_node = f"tag_{tag}"
                if tag_node not in G:
                    G.add_node(tag_node, type='tag', name=tag)
                if not G.has_edge(source, tag_node):
                    G.add_edge(source, tag_node, weight=total, flow_type='spending')
                else:
                    G[source][tag_node]['weight'] += total

        return G
    
    def build_tag_network(self, transactions: List[Transaction]) -> nx.Graph:
        """
        Build an undirected graph showing co-occurrence of transaction tags.
        
        Edges connect tags that appear together in transactions,
        weighted by co-occurrence frequency.
        
        Args:
            transactions: List of transactions
        
        Returns:
            NetworkX Graph
        """
        G = nx.Graph()
        
        # Track tag co-occurrences
        tag_pairs = defaultdict(int)
        tag_amounts = defaultdict(float)
        
        for txn in transactions:
            # Add nodes for each tag
            for tag in txn.tags:
                if tag not in G:
                    G.add_node(tag, type='tag', name=tag)
                tag_amounts[tag] += txn.amount
            
            # Add edges for co-occurring tags
            tags = sorted(txn.tags)  # Sort for consistent ordering
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    pair = (tag1, tag2)
                    tag_pairs[pair] += 1
        
        # Add edges with weights
        for (tag1, tag2), count in tag_pairs.items():
            G.add_edge(tag1, tag2, weight=count, co_occurrences=count)
        
        # Update node attributes with total amounts
        for tag, amount in tag_amounts.items():
            if tag in G:
                G.nodes[tag]['total_amount'] = amount
        
        return G
    
    def calculate_centrality_metrics(self, graph: nx.Graph) -> Dict[str, Any]:
        """
        Calculate various centrality metrics for the graph.
        
        Args:
            graph: NetworkX graph
        
        Returns:
            Dictionary of centrality metrics
        """
        if graph.number_of_nodes() == 0:
            return {
                'degree_centrality': {},
                'betweenness_centrality': {},
                'closeness_centrality': {},
                'pagerank': {}
            }
        
        # Convert to undirected for some metrics
        undirected_graph = graph.to_undirected() if isinstance(graph, nx.DiGraph) else graph
        
        result = {
            'degree_centrality': {},
            'betweenness_centrality': {},
            'closeness_centrality': {},
            'pagerank': {}
        }
        
        # Degree centrality
        degree_cent = nx.degree_centrality(undirected_graph)
        result['degree_centrality'] = self._top_k_nodes(degree_cent, k=10)
        
        # Betweenness centrality (nodes on shortest paths)
        if undirected_graph.number_of_nodes() > 2:
            betweenness = nx.betweenness_centrality(undirected_graph)
            result['betweenness_centrality'] = self._top_k_nodes(betweenness, k=10)
        
        # Closeness centrality (average distance to all other nodes)
        if nx.is_connected(undirected_graph):
            closeness = nx.closeness_centrality(undirected_graph)
            result['closeness_centrality'] = self._top_k_nodes(closeness, k=10)
        
        # PageRank (importance based on connections)
        try:
            if isinstance(graph, nx.DiGraph):
                pagerank = nx.pagerank(graph)
            else:
                pagerank = nx.pagerank(undirected_graph)
            result['pagerank'] = self._top_k_nodes(pagerank, k=10)
        except:
            pass  # PageRank may fail on some graph structures
        
        return result
    
    def detect_communities(self, graph: nx.Graph) -> Dict[str, Any]:
        """
        Detect communities/clusters in the graph.
        
        Args:
            graph: NetworkX graph
        
        Returns:
            Dictionary containing community information
        """
        if graph.number_of_nodes() == 0:
            return {
                'num_communities': 0,
                'communities': [],
                'modularity': 0.0
            }
        
        # Convert to undirected
        undirected_graph = graph.to_undirected() if isinstance(graph, nx.DiGraph) else graph
        
        # Use greedy modularity optimization
        try:
            communities_generator = nx.community.greedy_modularity_communities(undirected_graph)
            communities = [list(community) for community in communities_generator]
            
            # Calculate modularity
            modularity = nx.community.modularity(
                undirected_graph,
                [set(comm) for comm in communities]
            )
            
            return {
                'num_communities': len(communities),
                'communities': [
                    {
                        'id': i,
                        'nodes': sorted(community),
                        'size': len(community)
                    }
                    for i, community in enumerate(communities)
                ],
                'modularity': modularity
            }
        except:
            return {
                'num_communities': 0,
                'communities': [],
                'modularity': 0.0
            }
    
    def find_shortest_path(
        self,
        graph: nx.Graph,
        source: str,
        target: str
    ) -> Dict[str, Any]:
        """
        Find shortest path between two nodes.
        
        Args:
            graph: NetworkX graph
            source: Source node ID
            target: Target node ID
        
        Returns:
            Dictionary containing path information
        """
        undirected_graph = graph.to_undirected() if isinstance(graph, nx.DiGraph) else graph
        
        try:
            path = nx.shortest_path(undirected_graph, source, target)
            length = len(path) - 1
            
            return {
                'exists': True,
                'path': path,
                'length': length
            }
        except nx.NetworkXNoPath:
            return {
                'exists': False,
                'path': [],
                'length': float('inf')
            }
    
    def calculate_clustering_coefficients(self, graph: nx.Graph) -> Dict[str, float]:
        """
        Calculate clustering coefficient for nodes.
        
        The clustering coefficient measures how likely neighbors
        of a node are to be connected to each other.
        
        Args:
            graph: NetworkX graph
        
        Returns:
            Dictionary mapping node IDs to clustering coefficients
        """
        undirected_graph = graph.to_undirected() if isinstance(graph, nx.DiGraph) else graph
        
        if undirected_graph.number_of_nodes() == 0:
            return {}
        
        clustering = nx.clustering(undirected_graph)
        return self._top_k_nodes(clustering, k=10)
    
    def _serialize_nodes(self, graph: nx.Graph) -> List[Dict[str, Any]]:
        """Serialize graph nodes to dictionary format."""
        return [
            {
                'id': node,
                'attributes': data
            }
            for node, data in graph.nodes(data=True)
        ]
    
    def _serialize_edges(self, graph: nx.Graph) -> List[Dict[str, Any]]:
        """Serialize graph edges to dictionary format."""
        return [
            {
                'source': source,
                'target': target,
                'attributes': data
            }
            for source, target, data in graph.edges(data=True)
        ]
    
    def _top_k_nodes(
        self,
        node_values: Dict[str, float],
        k: int = 10
    ) -> Dict[str, float]:
        """
        Get top k nodes by value.
        
        Args:
            node_values: Dictionary mapping node IDs to values
            k: Number of top nodes to return
        
        Returns:
            Dictionary of top k nodes
        """
        sorted_nodes = sorted(
            node_values.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return dict(sorted_nodes[:k])
