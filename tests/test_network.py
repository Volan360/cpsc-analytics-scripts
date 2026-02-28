"""Tests for network analytics module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock
import networkx as nx

from src.analytics.network import NetworkAnalytics
from src.data.data_models import Transaction, Institution, Goal


@pytest.fixture
def mock_db_client():
    """Create a mocked DynamoDB client."""
    return Mock()


@pytest.fixture
def analytics(mock_db_client):
    """Create network analytics instance."""
    return NetworkAnalytics(mock_db_client)


@pytest.fixture
def sample_institutions():
    """Create sample institutions."""
    base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
    return [
        Institution(
            user_id='user1',
            institution_id='inst1',
            created_at=base_ts,
            institution_name='Checking Account',
            starting_balance=5000.0,
            current_balance=6500.0,
            linked_goals=['goal1']
        ),
        Institution(
            user_id='user1',
            institution_id='inst2',
            created_at=base_ts,
            institution_name='Savings Account',
            starting_balance=10000.0,
            current_balance=12000.0,
            linked_goals=['goal1', 'goal2']
        ),
        Institution(
            user_id='user1',
            institution_id='inst3',
            created_at=base_ts,
            institution_name='Investment Account',
            starting_balance=20000.0,
            current_balance=22000.0,
            linked_goals=['goal2']
        )
    ]


@pytest.fixture
def sample_goals():
    """Create sample goals."""
    base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
    return [
        Goal(
            user_id='user1',
            goal_id='goal1',
            created_at=base_ts,
            name='Emergency Fund',
            target_amount=10000.0,
            is_completed=False,
            is_active=True,
            linked_institutions={'inst1': 40, 'inst2': 60},
            linked_transactions=[]
        ),
        Goal(
            user_id='user1',
            goal_id='goal2',
            created_at=base_ts,
            name='Vacation',
            target_amount=5000.0,
            is_completed=False,
            is_active=True,
            linked_institutions={'inst2': 50, 'inst3': 50},
            linked_transactions=[]
        )
    ]


@pytest.fixture
def sample_transactions():
    """Create sample transactions."""
    base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
    return [
        Transaction(
            institution_id='inst1',
            created_at=base_ts,
            transaction_id='txn1',
            user_id='user1',
            type='WITHDRAWAL',
            amount=100.0,
            tags=['groceries', 'food'],
            transaction_date=base_ts
        ),
        Transaction(
            institution_id='inst1',
            created_at=base_ts + 86400,
            transaction_id='txn2',
            user_id='user1',
            type='WITHDRAWAL',
            amount=50.0,
            tags=['food', 'dining'],
            transaction_date=base_ts + 86400
        ),
        Transaction(
            institution_id='inst2',
            created_at=base_ts + 172800,
            transaction_id='txn3',
            user_id='user1',
            type='WITHDRAWAL',
            amount=200.0,
            tags=['utilities', 'bills'],
            transaction_date=base_ts + 172800
        ),
        Transaction(
            institution_id='inst1',
            created_at=base_ts + 259200,
            transaction_id='txn4',
            user_id='user1',
            type='WITHDRAWAL',
            amount=75.0,
            tags=['entertainment', 'dining'],
            transaction_date=base_ts + 259200
        ),
        Transaction(
            institution_id='inst3',
            created_at=base_ts + 345600,
            transaction_id='txn5',
            user_id='user1',
            type='WITHDRAWAL',
            amount=150.0,
            tags=['shopping', 'entertainment'],
            transaction_date=base_ts + 345600
        )
    ]


class TestFinancialFlowGraph:
    """Test financial flow graph construction."""
    
    def test_build_financial_flow_graph_basic(self, analytics, sample_transactions, sample_institutions, sample_goals):
        """Test basic financial flow graph construction."""
        graph = analytics.build_financial_flow_graph(sample_transactions, sample_institutions, sample_goals)
        
        # Check graph type
        assert isinstance(graph, nx.DiGraph)
        
        # Check nodes exist
        assert 'inst_inst1' in graph.nodes
        assert 'inst_inst2' in graph.nodes
        assert 'inst_inst3' in graph.nodes
        assert 'goal_goal1' in graph.nodes
        assert 'goal_goal2' in graph.nodes
        
        # Check category nodes
        assert 'cat_groceries' in graph.nodes
        assert 'cat_food' in graph.nodes
        assert 'cat_utilities' in graph.nodes
        
        # Check edges exist
        assert graph.has_edge('inst_inst1', 'cat_groceries')
        assert graph.has_edge('inst_inst1', 'goal_goal1')
        assert graph.has_edge('inst_inst2', 'goal_goal1')
        assert graph.has_edge('inst_inst2', 'goal_goal2')
    
    def test_financial_flow_edge_weights(self, analytics, sample_transactions, sample_institutions, sample_goals):
        """Test edge weights in financial flow graph."""
        graph = analytics.build_financial_flow_graph(sample_transactions, sample_institutions, sample_goals)
        
        # Check spending edge weight (groceries: 100)
        edge_data = graph.get_edge_data('inst_inst1', 'cat_groceries')
        assert edge_data['weight'] == 100.0
        assert edge_data['flow_type'] == 'spending'
        
        # Check goal allocation edge weight
        edge_data = graph.get_edge_data('inst_inst1', 'goal_goal1')
        assert edge_data['weight'] == 4000.0  # 10000 * 0.40
        assert edge_data['flow_type'] == 'allocation'
    
    def test_financial_flow_empty_data(self, analytics):
        """Test financial flow graph with no data."""
        graph = analytics.build_financial_flow_graph([], [], [])
        
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0
    
    def test_financial_flow_transactions_only(self, analytics, sample_transactions):
        """Test financial flow graph with only transactions."""
        graph = analytics.build_financial_flow_graph(sample_transactions, [], [])
        
        # Should have category nodes but no institution/goal nodes
        assert 'cat_groceries' in graph.nodes
        assert 'cat_food' in graph.nodes
        assert graph.number_of_nodes() > 0


class TestGoalInstitutionGraph:
    """Test goal-institution graph construction."""
    
    def test_build_goal_institution_graph_basic(self, analytics, sample_institutions, sample_goals):
        """Test basic goal-institution graph construction."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        
        # Check graph type
        assert isinstance(graph, nx.Graph)
        
        # Check nodes
        assert graph.number_of_nodes() == 5  # 3 institutions + 2 goals
        assert 'inst_inst1' in graph.nodes
        assert 'goal_goal1' in graph.nodes
        
        # Check edges
        assert graph.has_edge('inst_inst1', 'goal_goal1')
        assert graph.has_edge('inst_inst2', 'goal_goal1')
        assert graph.has_edge('inst_inst2', 'goal_goal2')
        assert graph.has_edge('inst_inst3', 'goal_goal2')
    
    def test_goal_institution_edge_attributes(self, analytics, sample_institutions, sample_goals):
        """Test edge attributes in goal-institution graph."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        
        # Check allocation percentages
        edge_data = graph.get_edge_data('inst_inst1', 'goal_goal1')
        assert edge_data['weight'] == 40.0
        assert edge_data['allocation'] == 40.0
        
        edge_data = graph.get_edge_data('inst_inst2', 'goal_goal2')
        assert edge_data['weight'] == 50.0
    
    def test_goal_institution_node_attributes(self, analytics, sample_institutions, sample_goals):
        """Test node attributes in goal-institution graph."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        
        # Check institution attributes
        inst_data = graph.nodes['inst_inst1']
        assert inst_data['type'] == 'institution'
        assert inst_data['name'] == 'Checking Account'
        assert inst_data['balance'] == 6500.0
        
        # Check goal attributes
        goal_data = graph.nodes['goal_goal1']
        assert goal_data['type'] == 'goal'
        assert goal_data['name'] == 'Emergency Fund'
        assert goal_data['target'] == 10000.0
        # Current amount = inst1 (6500 * 0.40) + inst2 (12000 * 0.60) = 2600 + 7200 = 9800
        assert goal_data['current'] == 9800.0
    
    def test_goal_institution_empty_data(self, analytics):
        """Test goal-institution graph with no data."""
        graph = analytics.build_goal_institution_graph([], [])
        
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_inactive_goal_linked_via_transactions(self, analytics, sample_institutions, sample_transactions):
        """Test that an inactive goal is linked to an institution via its linked_transactions."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        inactive_goal = Goal(
            user_id='user1',
            goal_id='goal_inactive',
            created_at=base_ts,
            name='Inactive Goal',
            target_amount=3000.0,
            is_completed=True,
            is_active=False,
            linked_institutions={},  # no direct institution allocation
            linked_transactions=['txn1', 'txn3']  # txn1 → inst1, txn3 → inst2
        )

        graph = analytics.build_goal_institution_graph(
            sample_institutions, [inactive_goal], sample_transactions
        )

        # Edges should be added from inst1 and inst2 via the goal's linked transactions
        assert graph.has_edge('inst_inst1', 'goal_goal_inactive')
        assert graph.has_edge('inst_inst2', 'goal_goal_inactive')
        # Edge weights should reflect the actual transaction amounts (txn1=100, txn3=200)
        assert graph.get_edge_data('inst_inst1', 'goal_goal_inactive')['weight'] == 100.0
        assert graph.get_edge_data('inst_inst2', 'goal_goal_inactive')['weight'] == 200.0
        # inst3 not referenced by any linked transaction
        assert not graph.has_edge('inst_inst3', 'goal_goal_inactive')

    def test_active_goal_not_linked_via_transactions(self, analytics, sample_institutions, sample_transactions):
        """Test that an active goal is NOT linked via transactions (only via linked_institutions)."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        active_goal = Goal(
            user_id='user1',
            goal_id='goal_active',
            created_at=base_ts,
            name='Active Goal',
            target_amount=3000.0,
            is_completed=False,
            is_active=True,
            linked_institutions={},  # no institution allocation
            linked_transactions=['txn1', 'txn3']  # would link to inst1, inst2 — but goal is active
        )

        graph = analytics.build_goal_institution_graph(
            sample_institutions, [active_goal], sample_transactions
        )

        # Active goal with empty linked_institutions should have no edges despite having transactions
        assert not graph.has_edge('inst_inst1', 'goal_goal_active')
        assert not graph.has_edge('inst_inst2', 'goal_goal_active')

    def test_inactive_goal_no_duplicate_edge_when_also_in_linked_institutions(
        self, analytics, sample_institutions, sample_transactions
    ):
        """Test that when an inactive goal's transaction institution is already in linked_institutions,
        no duplicate edge is created and the original allocation weight is preserved."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        inactive_goal = Goal(
            user_id='user1',
            goal_id='goal_overlap',
            created_at=base_ts,
            name='Overlap Goal',
            target_amount=5000.0,
            is_completed=True,
            is_active=False,
            linked_institutions={'inst1': 60},  # already linked to inst1 via allocation
            linked_transactions=['txn1']          # txn1 → inst1 (same institution)
        )

        graph = analytics.build_goal_institution_graph(
            sample_institutions, [inactive_goal], sample_transactions
        )

        # Edge should exist with the allocation weight (not overwritten)
        assert graph.has_edge('inst_inst1', 'goal_goal_overlap')
        edge_data = graph.get_edge_data('inst_inst1', 'goal_goal_overlap')
        assert edge_data['weight'] == 60.0
        assert edge_data['allocation'] == 60.0

    def test_inactive_goal_unknown_transaction_id_ignored(self, analytics, sample_institutions):
        """Test that unknown transaction IDs in linked_transactions are silently ignored."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        inactive_goal = Goal(
            user_id='user1',
            goal_id='goal_unknown_txn',
            created_at=base_ts,
            name='Unknown Txn Goal',
            target_amount=1000.0,
            is_completed=True,
            is_active=False,
            linked_institutions={},
            linked_transactions=['nonexistent_txn']
        )

        graph = analytics.build_goal_institution_graph(
            sample_institutions, [inactive_goal], transactions=[]
        )

        # Node exists but no edges since transaction can't be resolved
        assert 'goal_goal_unknown_txn' in graph.nodes
        assert graph.degree('goal_goal_unknown_txn') == 0

    def test_transactions_added_as_nodes(self, analytics, sample_institutions, sample_goals, sample_transactions):
        """Tags from transactions are added as tag nodes when transactions are provided."""
        graph = analytics.build_goal_institution_graph(
            sample_institutions, sample_goals, sample_transactions
        )
        # sample_transactions have tags: groceries, food, dining, utilities, bills, entertainment, shopping
        for tag in ['groceries', 'food', 'dining', 'utilities', 'bills', 'entertainment', 'shopping']:
            assert f'tag_{tag}' in graph.nodes, f'Missing tag node: {tag}'

        node_data = graph.nodes['tag_groceries']
        assert node_data['type'] == 'tag'
        assert node_data['name'] == 'groceries'

    def test_regular_transactions_linked_to_institution(self, analytics, sample_institutions, sample_goals, sample_transactions):
        """Non-goal transactions produce institution→tag edges aggregated by amount."""
        graph = analytics.build_goal_institution_graph(
            sample_institutions, sample_goals, sample_transactions
        )
        # txn1 (inst1, groceries/food, 100) + txn2 (inst1, food/dining, 50)
        assert graph.has_edge('inst_inst1', 'tag_groceries')
        assert graph.has_edge('inst_inst1', 'tag_food')
        assert graph.has_edge('inst_inst1', 'tag_dining')
        assert graph.has_edge('inst_inst2', 'tag_utilities')
        assert graph.has_edge('inst_inst3', 'tag_shopping')

    def test_goal_linked_transactions_linked_to_goal(self, analytics, sample_institutions, sample_transactions):
        """Tags from a goal's linked_transactions produce goal→tag edges, not institution→tag."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        goal = Goal(
            user_id='user1',
            goal_id='goal_comp',
            created_at=base_ts,
            name='Completed Goal',
            target_amount=100.0,
            is_completed=True,
            is_active=False,
            linked_institutions={},
            linked_transactions=['txn1', 'txn3']  # txn1: groceries/food, txn3: utilities/bills
        )
        graph = analytics.build_goal_institution_graph(
            sample_institutions, [goal], sample_transactions
        )
        # Tags from txn1/txn3 should attach to the goal node
        assert graph.has_edge('goal_goal_comp', 'tag_groceries')
        assert graph.has_edge('goal_goal_comp', 'tag_food')
        assert graph.has_edge('goal_goal_comp', 'tag_utilities')
        assert graph.has_edge('goal_goal_comp', 'tag_bills')
        # Not on the institution
        assert not graph.has_edge('inst_inst1', 'tag_groceries')
        assert not graph.has_edge('inst_inst2', 'tag_utilities')
        # Unrelated transactions still go to their institution
        assert graph.has_edge('inst_inst1', 'tag_dining')

    def test_transaction_edge_weight_is_amount(self, analytics, sample_institutions, sample_goals, sample_transactions):
        """Edge weight is the aggregated amount for that (source, tag) pair."""
        graph = analytics.build_goal_institution_graph(
            sample_institutions, sample_goals, sample_transactions
        )
        # txn1 (inst1, groceries, 100) — only one transaction for groceries
        edge_data = graph.get_edge_data('inst_inst1', 'tag_groceries')
        assert edge_data['weight'] == 100.0
        assert edge_data['flow_type'] == 'spending'
        # txn1 + txn2 both from inst1 have 'food' tag: 100 + 50 = 150
        food_edge = graph.get_edge_data('inst_inst1', 'tag_food')
        assert food_edge['weight'] == 150.0

    def test_no_transactions_no_txn_nodes(self, analytics, sample_institutions, sample_goals):
        """Without a transactions list, no tag nodes are created."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        tag_nodes = [n for n in graph.nodes if n.startswith('tag_')]
        assert len(tag_nodes) == 0


class TestTagNetwork:
    """Test transaction tag network construction."""
    
    def test_build_tag_network_basic(self, analytics, sample_transactions):
        """Test basic tag network construction."""
        graph = analytics.build_tag_network(sample_transactions)
        
        # Check graph type
        assert isinstance(graph, nx.Graph)
        
        # Check nodes
        assert 'groceries' in graph.nodes
        assert 'food' in graph.nodes
        assert 'dining' in graph.nodes
        assert 'utilities' in graph.nodes
        assert 'entertainment' in graph.nodes
        assert 'shopping' in graph.nodes
        assert 'bills' in graph.nodes
    
    def test_tag_network_co_occurrences(self, analytics, sample_transactions):
        """Test tag co-occurrence edges."""
        graph = analytics.build_tag_network(sample_transactions)
        
        # Check co-occurrence edges
        assert graph.has_edge('groceries', 'food')
        assert graph.has_edge('food', 'dining')
        assert graph.has_edge('entertainment', 'dining')
        assert graph.has_edge('shopping', 'entertainment')
        assert graph.has_edge('utilities', 'bills')
        
        # Check co-occurrence counts
        edge_data = graph.get_edge_data('food', 'dining')
        assert edge_data['co_occurrences'] == 1
    
    def test_tag_network_node_attributes(self, analytics, sample_transactions):
        """Test node attributes in tag network."""
        graph = analytics.build_tag_network(sample_transactions)
        
        # Check total amounts
        food_data = graph.nodes['food']
        assert food_data['total_amount'] == 150.0  # 100 + 50
        
        dining_data = graph.nodes['dining']
        assert dining_data['total_amount'] == 125.0  # 50 + 75
    
    def test_tag_network_empty_transactions(self, analytics):
        """Test tag network with no transactions."""
        graph = analytics.build_tag_network([])
        
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0
    
    def test_tag_network_single_tag_transactions(self, analytics):
        """Test tag network with single-tag transactions."""
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        transactions = [
            Transaction(
                institution_id='inst1',
                created_at=base_ts,
                transaction_id='txn1',
                user_id='user1',
                type='WITHDRAWAL',
                amount=100.0,
                tags=['single'],
                transaction_date=base_ts
            )
        ]
        
        graph = analytics.build_tag_network(transactions)
        
        # Should have node but no edges (no co-occurrences)
        assert graph.number_of_nodes() == 1
        assert graph.number_of_edges() == 0
        assert 'single' in graph.nodes


class TestCentralityMetrics:
    """Test centrality calculations."""
    
    def test_calculate_centrality_basic(self, analytics, sample_institutions, sample_goals):
        """Test centrality metrics calculation."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        centrality = analytics.calculate_centrality_metrics(graph)
        
        # Check all metrics present
        assert 'degree_centrality' in centrality
        assert 'betweenness_centrality' in centrality
        assert 'closeness_centrality' in centrality
        assert 'pagerank' in centrality
        
        # inst2 should have highest degree (connected to 2 goals)
        assert 'inst_inst2' in centrality['degree_centrality']
    
    def test_centrality_empty_graph(self, analytics):
        """Test centrality with empty graph."""
        graph = nx.Graph()
        centrality = analytics.calculate_centrality_metrics(graph)
        
        assert centrality['degree_centrality'] == {}
        assert centrality['betweenness_centrality'] == {}
        assert centrality['closeness_centrality'] == {}
        assert centrality['pagerank'] == {}
    
    def test_centrality_single_node(self, analytics):
        """Test centrality with single node."""
        graph = nx.Graph()
        graph.add_node('node1')
        
        centrality = analytics.calculate_centrality_metrics(graph)
        
        # Single node in a graph with no edges has degree centrality of 1.0 (100% relative to itself)
        assert 'node1' in centrality['degree_centrality']
    
    def test_centrality_directed_graph(self, analytics, sample_transactions, sample_institutions, sample_goals):
        """Test centrality with directed graph."""
        graph = analytics.build_financial_flow_graph(sample_transactions, sample_institutions, sample_goals)
        centrality = analytics.calculate_centrality_metrics(graph)
        
        # Should handle directed graphs
        assert len(centrality['degree_centrality']) > 0
        assert len(centrality['pagerank']) > 0


class TestCommunityDetection:
    """Test community detection."""
    
    def test_detect_communities_basic(self, analytics, sample_institutions, sample_goals):
        """Test basic community detection."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        communities = analytics.detect_communities(graph)
        
        assert 'num_communities' in communities
        assert 'communities' in communities
        assert 'modularity' in communities
        
        assert communities['num_communities'] > 0
        assert len(communities['communities']) > 0
    
    def test_detect_communities_empty_graph(self, analytics):
        """Test community detection with empty graph."""
        graph = nx.Graph()
        communities = analytics.detect_communities(graph)
        
        assert communities['num_communities'] == 0
        assert communities['communities'] == []
        assert communities['modularity'] == 0.0
    
    def test_community_structure(self, analytics, sample_institutions, sample_goals):
        """Test community structure format."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        communities = analytics.detect_communities(graph)
        
        # Check community structure
        for comm in communities['communities']:
            assert 'id' in comm
            assert 'nodes' in comm
            assert 'size' in comm
            assert comm['size'] == len(comm['nodes'])


class TestShortestPath:
    """Test shortest path finding."""
    
    def test_find_shortest_path_exists(self, analytics, sample_institutions, sample_goals):
        """Test finding an existing path."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        result = analytics.find_shortest_path(graph, 'inst_inst1', 'goal_goal1')
        
        assert result['exists'] is True
        assert len(result['path']) > 0
        assert result['length'] == 1  # Direct connection
    
    def test_find_shortest_path_multi_hop(self, analytics, sample_institutions, sample_goals):
        """Test path requiring multiple hops."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        result = analytics.find_shortest_path(graph, 'inst_inst1', 'inst_inst3')
        
        assert result['exists'] is True
        assert result['length'] >= 2  # Must go through a goal
    
    def test_find_shortest_path_no_path(self, analytics):
        """Test when no path exists."""
        graph = nx.Graph()
        graph.add_node('node1')
        graph.add_node('node2')
        # No edge between nodes
        
        result = analytics.find_shortest_path(graph, 'node1', 'node2')
        
        assert result['exists'] is False
        assert result['path'] == []
        assert result['length'] == float('inf')


class TestClusteringCoefficients:
    """Test clustering coefficient calculations."""
    
    def test_calculate_clustering_basic(self, analytics, sample_transactions):
        """Test clustering coefficient calculation."""
        graph = analytics.build_tag_network(sample_transactions)
        clustering = analytics.calculate_clustering_coefficients(graph)
        
        # Should return top nodes with clustering coefficients
        assert isinstance(clustering, dict)
        assert len(clustering) > 0
        
        # Coefficients should be between 0 and 1
        for node, coeff in clustering.items():
            assert 0.0 <= coeff <= 1.0
    
    def test_clustering_empty_graph(self, analytics):
        """Test clustering with empty graph."""
        graph = nx.Graph()
        clustering = analytics.calculate_clustering_coefficients(graph)
        
        assert clustering == {}
    
    def test_clustering_linear_graph(self, analytics):
        """Test clustering on linear graph (no triangles)."""
        graph = nx.Graph()
        graph.add_edges_from([('a', 'b'), ('b', 'c'), ('c', 'd')])
        
        clustering = analytics.calculate_clustering_coefficients(graph)
        
        # Linear graph has no triangles, so clustering = 0
        for coeff in clustering.values():
            assert coeff == 0.0


class TestAnalyzeMethod:
    """Test the main analyze method."""
    
    def test_analyze_financial_flow(self, analytics, mock_db_client, sample_transactions, sample_institutions, sample_goals):
        """Test full analysis with financial flow graph."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31', graph_type='financial_flow')
        
        assert result['user_id'] == 'user1'
        assert result['graph_type'] == 'financial_flow'
        assert 'graph_stats' in result
        assert 'nodes' in result
        assert 'edges' in result
        assert 'centrality' in result
        assert 'communities' in result
        
        assert result['graph_stats']['nodes'] > 0
        assert result['graph_stats']['edges'] > 0
    
    def test_analyze_goal_institution(self, analytics, mock_db_client, sample_transactions, sample_institutions, sample_goals):
        """Test full analysis with goal-institution graph (no date filter — all-time)."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals

        # goal_institution does not require dates
        result = analytics.analyze('user1', graph_type='goal_institution')

        assert result['graph_type'] == 'goal_institution'
        # 3 institutions + 2 goals + N tag nodes (groceries, food, dining, utilities, bills, entertainment, shopping)
        assert result['graph_stats']['nodes'] >= 5
        assert 'period' not in result  # no date window for this graph type
        # verify called without date filtering
        mock_db_client.get_all_user_transactions.assert_called_once_with('user1')
    
    def test_analyze_tag_network(self, analytics, mock_db_client, sample_transactions, sample_institutions, sample_goals):
        """Test full analysis with tag network."""
        mock_db_client.get_all_user_transactions.return_value = sample_transactions
        mock_db_client.get_institutions.return_value = sample_institutions
        mock_db_client.get_goals.return_value = sample_goals
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31', graph_type='tag_network')
        
        assert result['graph_type'] == 'tag_network'
        assert result['graph_stats']['nodes'] > 0
    
    def test_analyze_no_data(self, analytics, mock_db_client):
        """Test analysis with no data."""
        mock_db_client.get_all_user_transactions.return_value = []
        mock_db_client.get_institutions.return_value = []
        mock_db_client.get_goals.return_value = []
        
        result = analytics.analyze('user1', '2024-01-01', '2024-01-31', graph_type='financial_flow')
        
        assert result['graph_stats']['nodes'] == 0
        assert result['graph_stats']['edges'] == 0
    
    def test_analyze_invalid_graph_type(self, analytics, mock_db_client):
        """Test analysis with invalid graph type."""
        mock_db_client.get_all_user_transactions.return_value = []
        mock_db_client.get_institutions.return_value = []
        mock_db_client.get_goals.return_value = []
        
        with pytest.raises(ValueError):
            analytics.analyze('user1', '2024-01-01', '2024-01-31', graph_type='invalid')


class TestGraphSerialization:
    """Test graph serialization methods."""
    
    def test_serialize_nodes(self, analytics, sample_institutions, sample_goals):
        """Test node serialization."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        nodes = analytics._serialize_nodes(graph)
        
        assert isinstance(nodes, list)
        assert len(nodes) == 5
        
        # Check structure
        for node in nodes:
            assert 'id' in node
            assert 'attributes' in node
    
    def test_serialize_edges(self, analytics, sample_institutions, sample_goals):
        """Test edge serialization."""
        graph = analytics.build_goal_institution_graph(sample_institutions, sample_goals)
        edges = analytics._serialize_edges(graph)
        
        assert isinstance(edges, list)
        assert len(edges) > 0
        
        # Check structure
        for edge in edges:
            assert 'source' in edge
            assert 'target' in edge
            assert 'attributes' in edge
    
    def test_top_k_nodes(self, analytics):
        """Test top k nodes selection."""
        node_values = {
            'a': 0.9,
            'b': 0.5,
            'c': 0.8,
            'd': 0.3,
            'e': 0.7
        }
        
        top_3 = analytics._top_k_nodes(node_values, k=3)
        
        assert len(top_3) == 3
        assert 'a' in top_3
        assert 'c' in top_3
        assert 'e' in top_3
        assert list(top_3.keys()) == ['a', 'c', 'e']  # Should be sorted
