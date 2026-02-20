"""Tests for visualization modules."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import plotly.graph_objects as go

from src.visualization.charts import ChartGenerator
from src.visualization.reports import ReportGenerator
from src.visualization.s3_uploader import S3Uploader


class TestChartGenerator:
    """Test suite for chart generation."""
    
    @pytest.fixture
    def chart_gen(self):
        """Create chart generator instance."""
        return ChartGenerator()
    
    def test_create_line_chart(self, chart_gen):
        """Test line chart creation."""
        data = {
            'Income': [1000, 1200, 1100, 1300],
            'Expenses': [800, 900, 850, 950]
        }
        x_axis = ['Jan', 'Feb', 'Mar', 'Apr']
        
        fig = chart_gen.create_line_chart(
            data=data,
            x_axis=x_axis,
            title='Monthly Cash Flow'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert fig.data[0].name == 'Income'
        assert fig.data[1].name == 'Expenses'
        assert list(fig.data[0].x) == x_axis
    
    def test_create_bar_chart_vertical(self, chart_gen):
        """Test vertical bar chart creation."""
        categories = ['Groceries', 'Utilities', 'Entertainment']
        values = [500.0, 200.0, 150.0]
        
        fig = chart_gen.create_bar_chart(
            categories=categories,
            values=values,
            title='Spending by Category'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert list(fig.data[0].x) == categories
        assert list(fig.data[0].y) == values
    
    def test_create_bar_chart_horizontal(self, chart_gen):
        """Test horizontal bar chart creation."""
        categories = ['Groceries', 'Utilities']
        values = [500.0, 200.0]
        
        fig = chart_gen.create_bar_chart(
            categories=categories,
            values=values,
            title='Spending by Category',
            orientation='h'
        )
        
        assert isinstance(fig, go.Figure)
        assert fig.data[0].orientation == 'h'
        assert list(fig.data[0].y) == categories
        assert list(fig.data[0].x) == values
    
    def test_create_pie_chart(self, chart_gen):
        """Test pie chart creation."""
        labels = ['Groceries', 'Utilities', 'Entertainment']
        values = [500.0, 200.0, 150.0]
        
        fig = chart_gen.create_pie_chart(
            labels=labels,
            values=values,
            title='Spending Distribution'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert list(fig.data[0].labels) == labels
        assert list(fig.data[0].values) == values
        assert fig.data[0].hole == 0.0  # Regular pie
    
    def test_create_donut_chart(self, chart_gen):
        """Test donut chart creation."""
        labels = ['Groceries', 'Utilities']
        values = [500.0, 200.0]
        
        fig = chart_gen.create_pie_chart(
            labels=labels,
            values=values,
            title='Spending Distribution',
            donut=True
        )
        
        assert fig.data[0].hole == 0.4  # Donut style
    
    def test_create_stacked_bar_chart(self, chart_gen):
        """Test stacked bar chart creation."""
        categories = ['Jan', 'Feb', 'Mar']
        data_series = {
            'Groceries': [100, 120, 110],
            'Utilities': [50, 55, 52]
        }
        
        fig = chart_gen.create_stacked_bar_chart(
            categories=categories,
            data_series=data_series,
            title='Monthly Category Comparison'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2
        assert fig.layout.barmode == 'stack'
    
    def test_create_area_chart(self, chart_gen):
        """Test area chart creation."""
        data = {
            'Balance': [1000, 1100, 1050, 1200]
        }
        x_axis = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
        
        fig = chart_gen.create_area_chart(
            data=data,
            x_axis=x_axis,
            title='Account Balance Over Time'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].fill == 'tozeroy'
    
    def test_create_stacked_area_chart(self, chart_gen):
        """Test stacked area chart creation."""
        data = {
            'Account A': [1000, 1100, 1050],
            'Account B': [500, 550, 600]
        }
        x_axis = ['Jan', 'Feb', 'Mar']
        
        fig = chart_gen.create_area_chart(
            data=data,
            x_axis=x_axis,
            title='Accounts Over Time',
            stacked=True
        )
        
        assert len(fig.data) == 2
        assert fig.data[0].stackgroup == 'one'
    
    def test_create_scatter_plot(self, chart_gen):
        """Test scatter plot creation."""
        x_data = [100, 200, 300, 400]
        y_data = [10, 25, 20, 35]
        labels = ['A', 'B', 'C', 'D']
        
        fig = chart_gen.create_scatter_plot(
            x_data=x_data,
            y_data=y_data,
            labels=labels,
            title='Correlation Analysis'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].mode == 'markers'
        assert list(fig.data[0].x) == x_data
        assert list(fig.data[0].y) == y_data
    
    def test_create_heatmap(self, chart_gen):
        """Test heatmap creation."""
        z_data = [
            [10, 20, 30],
            [15, 25, 35],
            [12, 22, 32]
        ]
        x_labels = ['Jan', 'Feb', 'Mar']
        y_labels = ['Cat1', 'Cat2', 'Cat3']
        
        fig = chart_gen.create_heatmap(
            z_data=z_data,
            x_labels=x_labels,
            y_labels=y_labels,
            title='Spending Heatmap'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert list(fig.data[0].x) == x_labels
        assert list(fig.data[0].y) == y_labels
    
    def test_create_network_graph_empty(self, chart_gen):
        """Test network graph with no data."""
        fig = chart_gen.create_network_graph(
            nodes=[],
            edges=[],
            title='Empty Network'
        )
        
        assert isinstance(fig, go.Figure)
    
    def test_create_network_graph_basic(self, chart_gen):
        """Test network graph creation."""
        nodes = [
            {'id': 'node1', 'attributes': {'type': 'institution', 'name': 'Bank A'}},
            {'id': 'node2', 'attributes': {'type': 'goal', 'name': 'Goal A'}},
            {'id': 'node3', 'attributes': {'type': 'category', 'name': 'Groceries'}}
        ]
        edges = [
            {'source': 'node1', 'target': 'node2', 'attributes': {'weight': 100}},
            {'source': 'node1', 'target': 'node3', 'attributes': {'weight': 50}}
        ]
        
        fig = chart_gen.create_network_graph(
            nodes=nodes,
            edges=edges,
            title='Financial Network'
        )
        
        assert isinstance(fig, go.Figure)
        # Should have edge traces + node traces (one per type)
        assert len(fig.data) >= 2
    
    def test_create_gauge_chart(self, chart_gen):
        """Test gauge chart creation."""
        fig = chart_gen.create_gauge_chart(
            value=75.0,
            title='Goal Progress',
            max_value=100.0
        )
        
        assert isinstance(fig, go.Figure)
        assert fig.data[0].value == 75.0
        assert fig.data[0].mode == 'gauge+number+delta'
    
    def test_create_sankey_diagram(self, chart_gen):
        """Test Sankey diagram creation."""
        sources = ['Income', 'Income', 'Savings']
        targets = ['Groceries', 'Utilities', 'Emergency Fund']
        values = [500, 200, 300]
        
        fig = chart_gen.create_sankey_diagram(
            sources=sources,
            targets=targets,
            values=values,
            title='Money Flow'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'sankey'
    
    def test_create_sankey_custom_labels(self, chart_gen):
        """Test Sankey diagram with custom labels."""
        sources = ['A', 'A']
        targets = ['B', 'C']
        values = [100, 200]
        node_labels = ['Account A', 'Category B', 'Category C']
        
        fig = chart_gen.create_sankey_diagram(
            sources=sources,
            targets=targets,
            values=values,
            title='Flow',
            node_labels=node_labels
        )
        
        assert list(fig.data[0].node['label']) == node_labels
    
    def test_create_radar_chart(self, chart_gen):
        """Test radar chart creation."""
        categories = ['Savings', 'Goals', 'Diversity', 'Utilization', 'Regularity']
        values = [85, 75, 60, 90, 70]
        
        fig = chart_gen.create_radar_chart(
            categories=categories,
            values=values,
            title='Financial Health Score'
        )
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == 'scatterpolar'
        assert list(fig.data[0].theta) == categories
        assert list(fig.data[0].r) == values
    
    def test_create_radar_chart_with_comparison(self, chart_gen):
        """Test radar chart with comparison series."""
        categories = ['A', 'B', 'C']
        values = [80, 70, 85]
        comparison = [60, 75, 65]
        
        fig = chart_gen.create_radar_chart(
            categories=categories,
            values=values,
            title='Comparison',
            comparison_values=comparison
        )
        
        assert len(fig.data) == 2  # Main + comparison
        assert fig.data[0].type == 'scatterpolar'
        assert fig.data[1].type == 'scatterpolar'
    
    def test_save_chart_html(self, chart_gen, tmp_path):
        """Test saving chart as HTML."""
        fig = chart_gen.create_pie_chart(
            labels=['A', 'B'],
            values=[50, 50],
            title='Test'
        )
        
        filename = str(tmp_path / 'test_chart.html')
        result = chart_gen.save_chart_html(fig, filename)
        
        assert result == filename
        assert (tmp_path / 'test_chart.html').exists()


class TestReportGenerator:
    """Test suite for report generation."""
    
    @pytest.fixture
    def report_gen(self):
        """Create report generator instance."""
        return ReportGenerator()
    
    @pytest.fixture
    def sample_cash_flow_data(self):
        """Sample cash flow analytics data."""
        return {
            'user_id': 'user1',
            'period': {'start': '2024-01-01', 'end': '2024-01-31'},
            'summary': {
                'total_deposits': 5000.0,
                'total_withdrawals': 3000.0,
                'net_cash_flow': 2000.0,
                'savings_rate': 40.0
            }
        }
    
    @pytest.fixture
    def sample_category_data(self):
        """Sample category analytics data."""
        return {
            'user_id': 'user1',
            'period': {'start': '2024-01-01', 'end': '2024-01-31'},
            'summary': {
                'total_amount': 1000.0,
                'unique_categories': 5,
                'transaction_count': 20
            },
            'top_categories': [
                {'rank': 1, 'name': 'Groceries', 'amount': 500.0, 'percentage': 50.0},
                {'rank': 2, 'name': 'Utilities', 'amount': 300.0, 'percentage': 30.0}
            ],
            'diversity': {
                'gini_coefficient': 0.3
            }
        }
    
    @pytest.fixture
    def sample_goal_data(self):
        """Sample goal analytics data."""
        return {
            'user_id': 'user1',
            'summary': {
                'total_goals': 3,
                'active_goals': 2,
                'at_risk_count': 1,
                'average_progress': 65.0
            },
            'goals': [
                {
                    'name': 'Emergency Fund',
                    'target_amount': 10000.0,
                    'current_amount': 7000.0,
                    'progress_percent': 70.0,
                    'is_on_track': True
                }
            ]
        }
    
    @pytest.fixture
    def sample_network_data(self):
        """Sample network analytics data."""
        return {
            'user_id': 'user1',
            'period': {'start': '2024-01-01', 'end': '2024-01-31'},
            'graph_stats': {
                'nodes': 10,
                'edges': 15,
                'density': 0.45,
                'is_connected': True
            },
            'communities': {
                'num_communities': 2,
                'modularity': 0.6
            }
        }
    
    def test_generate_cash_flow_report(self, report_gen, sample_cash_flow_data):
        """Test cash flow report generation."""
        charts = []  # Empty charts for test
        html = report_gen.generate_cash_flow_report(
            sample_cash_flow_data,
            charts,
            user_name='Test User'
        )
        
        assert isinstance(html, str)
        assert 'Cash Flow Analysis Report' in html
        assert 'Test User' in html
        assert '2024-01-01' in html
        assert '$5,000.00' in html
        assert '40.0%' in html
    
    def test_generate_category_report(self, report_gen, sample_category_data):
        """Test category report generation."""
        charts = []
        html = report_gen.generate_category_report(
            sample_category_data,
            charts
        )
        
        assert isinstance(html, str)
        assert 'Category Analysis Report' in html
        assert 'Groceries' in html
        assert '$500.00' in html
    
    def test_generate_goal_report(self, report_gen, sample_goal_data):
        """Test goal report generation."""
        charts = []
        html = report_gen.generate_goal_report(
            sample_goal_data,
            charts
        )
        
        assert isinstance(html, str)
        assert 'Goal Progress Report' in html
        assert 'Emergency Fund' in html
        assert '70.0%' in html
    
    def test_generate_network_report(self, report_gen, sample_network_data):
        """Test network report generation."""
        charts = []
        html = report_gen.generate_network_report(
            sample_network_data,
            charts
        )
        
        assert isinstance(html, str)
        assert 'Network Analysis Report' in html
        assert '10' in html  # Node count
        assert '15' in html  # Edge count
    
    def test_generate_health_score_report(self, report_gen):
        """Test health score report generation."""
        health_data = {
            'overall_score': 78.5,
            'rating': 'Good',
            'period_days': 30,
            'computed_at': '2024-01-15T10:30:00',
            'components': {
                'savings_rate': {'score': 85.0, 'weight': 0.25, 'contribution': 21.25},
                'goal_progress': {'score': 75.0, 'weight': 0.25, 'contribution': 18.75},
                'spending_diversity': {'score': 70.0, 'weight': 0.20, 'contribution': 14.0},
                'account_utilization': {'score': 82.0, 'weight': 0.15, 'contribution': 12.3},
                'transaction_regularity': {'score': 80.0, 'weight': 0.15, 'contribution': 12.0}
            },
            'recommendations': [
                'Keep up the great work!',
                'Try to increase diversity'
            ]
        }
        
        charts = []
        html = report_gen.generate_health_score_report(
            health_data,
            charts,
            user_name='Test User'
        )
        
        assert isinstance(html, str)
        assert 'Financial Health Score Report' in html
        assert 'Test User' in html
        assert '78.5' in html or '78' in html
        assert 'Good' in html
        assert 'Score Breakdown' in html
    
    def test_save_report(self, report_gen, tmp_path):
        """Test saving report to file."""
        html_content = '<html><body>Test Report</body></html>'
        filename = str(tmp_path / 'test_report.html')
        
        result = report_gen.save_report(html_content, filename)
        
        assert result == filename
        assert (tmp_path / 'test_report.html').exists()
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Test Report' in content
    
    def test_generate_insights_positive_cash_flow(self, report_gen):
        """Test insight generation for positive cash flow."""
        data = {
            'summary': {
                'net_cash_flow': 1000.0,
                'savings_rate': 25.0
            }
        }
        
        insights = report_gen._generate_cash_flow_insights(data)
        
        assert len(insights) > 0
        assert any('Positive' in insight for insight in insights)
    
    def test_generate_insights_negative_cash_flow(self, report_gen):
        """Test insight generation for negative cash flow."""
        data = {
            'summary': {
                'net_cash_flow': -500.0,
                'savings_rate': -5.0
            }
        }
        
        insights = report_gen._generate_cash_flow_insights(data)
        
        assert len(insights) > 0
        assert any('Negative' in insight for insight in insights)


class TestS3Uploader:
    """Test suite for S3 uploader."""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create mock S3 client."""
        mock_client = Mock()
        mock_client.upload_file = Mock()
        mock_client.put_object = Mock()
        mock_client.generate_presigned_url = Mock(return_value='https://example.com/presigned')
        mock_client.list_objects_v2 = Mock(return_value={'Contents': []})
        mock_client.delete_object = Mock()
        mock_client.head_bucket = Mock()
        return mock_client
    
    @pytest.fixture
    def uploader(self, mock_s3_client):
        """Create S3 uploader with mocked client."""
        with patch('boto3.Session') as mock_session:
            mock_session.return_value.client.return_value = mock_s3_client
            uploader = S3Uploader('test-bucket', region='us-east-1')
            uploader.s3_client = mock_s3_client
            return uploader
    
    def test_upload_string(self, uploader, mock_s3_client):
        """Test uploading string content."""
        result = uploader.upload_string(
            content='<html>Test</html>',
            s3_key='test.html',
            content_type='text/html'
        )
        
        assert result['bucket'] == 'test-bucket'
        assert result['key'] == 'test.html'
        assert 'url' in result
        mock_s3_client.put_object.assert_called_once()
    
    def test_generate_presigned_url(self, uploader, mock_s3_client):
        """Test presigned URL generation."""
        url = uploader.generate_presigned_url('test.html', expiration=3600)
        
        assert url == 'https://example.com/presigned'
        mock_s3_client.generate_presigned_url.assert_called_once()
    
    def test_upload_chart_html(self, uploader, mock_s3_client):
        """Test chart HTML upload with organized naming."""
        result = uploader.upload_chart_html(
            html_content='<html>Chart</html>',
            user_id='user123',
            chart_type='cash_flow'
        )
        
        assert result['bucket'] == 'test-bucket'
        assert 'user123' in result['key']
        assert 'cash_flow' in result['key']
        assert 'presigned_url' in result
    
    def test_upload_report(self, uploader, mock_s3_client):
        """Test report upload with organized naming."""
        result = uploader.upload_report(
            html_content='<html>Report</html>',
            user_id='user123',
            report_type='monthly'
        )
        
        assert result['bucket'] == 'test-bucket'
        assert 'user123' in result['key']
        assert 'reports' in result['key']
        assert 'presigned_url' in result
    
    def test_list_user_reports(self, uploader, mock_s3_client):
        """Test listing user reports."""
        mock_s3_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'reports/user123/report1.html',
                    'Size': 1024,
                    'LastModified': Mock(isoformat=lambda: '2024-01-01')
                }
            ]
        }
        
        reports = uploader.list_user_reports('user123')
        
        assert len(reports) == 1
        assert 'key' in reports[0]
        assert 'user123' in reports[0]['key']
    
    def test_list_user_reports_empty(self, uploader, mock_s3_client):
        """Test listing reports when none exist."""
        mock_s3_client.list_objects_v2.return_value = {}
        
        reports = uploader.list_user_reports('user123')
        
        assert reports == []
    
    def test_delete_object(self, uploader, mock_s3_client):
        """Test object deletion."""
        result = uploader.delete_object('test.html')
        
        assert result is True
        mock_s3_client.delete_object.assert_called_once()
    
    def test_check_bucket_exists(self, uploader, mock_s3_client):
        """Test bucket existence check."""
        result = uploader.check_bucket_exists()
        
        assert result is True
        mock_s3_client.head_bucket.assert_called_once()
    
    def test_check_bucket_not_exists(self, uploader, mock_s3_client):
        """Test bucket existence check when bucket doesn't exist."""
        from botocore.exceptions import ClientError
        mock_s3_client.head_bucket.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'HeadBucket'
        )
        
        result = uploader.check_bucket_exists()
        
        assert result is False
