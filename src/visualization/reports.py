"""Report generation utilities for financial analytics."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Template
import plotly.graph_objects as go


class ReportGenerator:
    """Generate HTML reports for financial analytics."""
    
    def __init__(self):
        """Initialize report generator."""
        self.report_template = self._create_base_template()
    
    def generate_cash_flow_report(
        self,
        analytics_data: Dict[str, Any],
        charts: List[go.Figure],
        user_name: Optional[str] = None
    ) -> str:
        """
        Generate cash flow analysis report.
        
        Args:
            analytics_data: Cash flow analytics results
            charts: List of Plotly figures
            user_name: Optional user name for personalization
        
        Returns:
            HTML report string
        """
        summary = analytics_data.get('summary', {})
        period = analytics_data.get('period', {})
        
        report_data = {
            'title': 'Cash Flow Analysis Report',
            'user_name': user_name or 'User',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period_start': period.get('start', 'N/A'),
            'period_end': period.get('end', 'N/A'),
            'metrics': [
                {
                    'name': 'Total Deposits',
                    'value': f"${summary.get('total_deposits', 0):,.2f}",
                    'icon': '💰'
                },
                {
                    'name': 'Total Withdrawals',
                    'value': f"${summary.get('total_withdrawals', 0):,.2f}",
                    'icon': '💸'
                },
                {
                    'name': 'Net Cash Flow',
                    'value': f"${summary.get('net_cash_flow', 0):,.2f}",
                    'icon': '📊'
                },
                {
                    'name': 'Savings Rate',
                    'value': f"{summary.get('savings_rate', 0):.1f}%",
                    'icon': '🎯'
                }
            ],
            'charts': [self._fig_to_html(fig) for fig in charts],
            'insights': self._generate_cash_flow_insights(analytics_data)
        }
        
        return self._render_report(report_data)
    
    def generate_category_report(
        self,
        analytics_data: Dict[str, Any],
        charts: List[go.Figure],
        user_name: Optional[str] = None
    ) -> str:
        """
        Generate category analysis report.
        
        Args:
            analytics_data: Category analytics results
            charts: List of Plotly figures
            user_name: Optional user name for personalization
        
        Returns:
            HTML report string
        """
        summary = analytics_data.get('summary', {})
        period = analytics_data.get('period', {})
        top_categories = analytics_data.get('top_categories', [])
        
        report_data = {
            'title': 'Category Analysis Report',
            'user_name': user_name or 'User',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period_start': period.get('start', 'N/A'),
            'period_end': period.get('end', 'N/A'),
            'metrics': [
                {
                    'name': 'Total Spending',
                    'value': f"${summary.get('total_amount', 0):,.2f}",
                    'icon': '💳'
                },
                {
                    'name': 'Unique Categories',
                    'value': str(summary.get('unique_categories', 0)),
                    'icon': '🏷️'
                },
                {
                    'name': 'Top Category',
                    'value': top_categories[0]['name'] if top_categories else 'N/A',
                    'icon': '🥇'
                },
                {
                    'name': 'Transactions',
                    'value': str(summary.get('transaction_count', 0)),
                    'icon': '📝'
                }
            ],
            'charts': [self._fig_to_html(fig) for fig in charts],
            'top_categories_table': self._create_table_html(
                headers=['Rank', 'Category', 'Amount', 'Percentage'],
                rows=[
                    [
                        cat['rank'],
                        cat['name'],
                        f"${cat['amount']:,.2f}",
                        f"{cat['percentage']:.1f}%"
                    ]
                    for cat in top_categories[:10]
                ]
            ),
            'insights': self._generate_category_insights(analytics_data)
        }
        
        return self._render_report(report_data)
    
    def generate_goal_report(
        self,
        analytics_data: Dict[str, Any],
        charts: List[go.Figure],
        user_name: Optional[str] = None,
        goal_labels: Optional[List[str]] = None
    ) -> str:
        """
        Generate goal progress report.
        
        Args:
            analytics_data: Goal analytics results
            charts: List of Plotly figures
            user_name: Optional user name for personalization
        
        Returns:
            HTML report string
        """
        summary = analytics_data.get('summary', {})
        goals = analytics_data.get('goals', [])
        
        report_data = {
            'title': 'Goal Progress Report',
            'user_name': user_name or 'User',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period_start': 'N/A',
            'period_end': 'N/A',
            'metrics': [
                {
                    'name': 'Total Goals',
                    'value': str(summary.get('total_goals', 0)),
                    'icon': '🎯'
                },
                {
                    'name': 'Active Goals',
                    'value': str(summary.get('active_goals', 0)),
                    'icon': '✅'
                },
                {
                    'name': 'At Risk Goals',
                    'value': str(summary.get('at_risk_count', 0)),
                    'icon': '⚠️'
                },
                {
                    'name': 'Avg Progress',
                    'value': f"{summary.get('average_progress', 0):.1f}%",
                    'icon': '📈'
                }
            ],
            'charts': [self._fig_to_html(fig) for fig in charts],
            'goals_table': self._create_table_html(
                headers=['Goal', 'Progress', 'Current', 'Target', 'Status'],
                rows=[
                    [
                        (goal_labels[i] if goal_labels and i < len(goal_labels) else goal['name']),
                        f"{goal.get('progress_percent', 0):.1f}%",
                        f"${goal.get('current_amount', 0):,.2f}",
                        f"${goal['target_amount']:,.2f}",
                        '✅' if (goal.get('is_completed') or not goal.get('is_active', True)) else '⚠️'
                    ]
                    for i, goal in enumerate(goals)
                ]
            ),
            'insights': self._generate_goal_insights(analytics_data)
        }
        
        return self._render_report(report_data)
    
    def generate_network_report(
        self,
        analytics_data: Dict[str, Any],
        charts: List[go.Figure],
        user_name: Optional[str] = None
    ) -> str:
        """
        Generate network analysis report.
        
        Args:
            analytics_data: Network analytics results
            charts: List of Plotly figures
            user_name: Optional user name for personalization
        
        Returns:
            HTML report string
        """
        graph_stats = analytics_data.get('graph_stats', {})
        communities = analytics_data.get('communities', {})
        
        report_data = {
            'title': 'Network Analysis Report',
            'user_name': user_name or 'User',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period_start': analytics_data.get('period', {}).get('start', 'N/A'),
            'period_end': analytics_data.get('period', {}).get('end', 'N/A'),
            'metrics': [
                {
                    'name': 'Total Nodes',
                    'value': str(graph_stats.get('nodes', 0)),
                    'icon': '🔵'
                },
                {
                    'name': 'Total Edges',
                    'value': str(graph_stats.get('edges', 0)),
                    'icon': '↔️'
                },
                {
                    'name': 'Communities',
                    'value': str(communities.get('num_communities', 0)),
                    'icon': '👥'
                },
                {
                    'name': 'Network Density',
                    'value': f"{graph_stats.get('density', 0):.3f}",
                    'icon': '🕸️'
                }
            ],
            'charts': [self._fig_to_html(fig) for fig in charts],
            'insights': self._generate_network_insights(analytics_data)
        }
        
        return self._render_report(report_data)
    
    def _create_base_template(self) -> str:
        """Create base HTML template for reports."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .meta {
            opacity: 0.9;
            font-size: 0.95em;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .metric-card .icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .metric-card .label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .metric-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-top: 5px;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .insights-section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .insights-section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .insight-item {
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9ff;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }
        
        .table-container {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        tr:hover {
            background: #f8f9ff;
        }
        
        .footer {
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="meta">
                Generated for: {{ user_name }} | Date: {{ generated_at }}<br>
                Period: {{ period_start }} to {{ period_end }}
            </div>
        </div>
        
        <div class="metrics-grid">
            {% for metric in metrics %}
            <div class="metric-card">
                <div class="icon">{{ metric.icon }}</div>
                <div class="label">{{ metric.name }}</div>
                <div class="value">{{ metric.value }}</div>
            </div>
            {% endfor %}
        </div>
        
        {% for chart in charts %}
        <div class="chart-container">
            {{ chart|safe }}
        </div>
        {% endfor %}
        
        {% if top_categories_table %}
        <div class="table-container">
            <h2>Top Categories Breakdown</h2>
            {{ top_categories_table|safe }}
        </div>
        {% endif %}
        
        {% if goals_table %}
        <div class="table-container">
            <h2>Goals Progress</h2>
            {{ goals_table|safe }}
        </div>
        {% endif %}
        
        {% if additional_sections %}
        {{ additional_sections|safe }}
        {% endif %}
        
        <div class="insights-section">
            <h2>💡 Key Insights</h2>
            {% for insight in insights %}
            <div class="insight-item">{{ insight }}</div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>CPSC Financial Analytics | Generated on {{ generated_at }}</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _render_report(self, data: Dict[str, Any]) -> str:
        """Render report template with data."""
        template = Template(self.report_template)
        return template.render(**data)
    
    def _fig_to_html(self, fig: go.Figure) -> str:
        """Convert Plotly figure to HTML div."""
        return fig.to_html(include_plotlyjs=False, div_id=f"chart-{id(fig)}")
    
    def _create_table_html(self, headers: List[str], rows: List[List[Any]]) -> str:
        """Create HTML table from headers and rows."""
        html = '<table><thead><tr>'
        for header in headers:
            html += f'<th>{header}</th>'
        html += '</tr></thead><tbody>'
        
        for row in rows:
            html += '<tr>'
            for cell in row:
                html += f'<td>{cell}</td>'
            html += '</tr>'
        
        html += '</tbody></table>'
        return html
    
    def _generate_cash_flow_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights for cash flow report."""
        insights = []
        summary = data.get('summary', {})
        
        net_flow = summary.get('net_cash_flow', 0)
        if net_flow > 0:
            insights.append(f"✅ Positive net cash flow of ${net_flow:,.2f} indicates healthy financial management.")
        elif net_flow < 0:
            insights.append(f"⚠️ Negative net cash flow of ${abs(net_flow):,.2f} suggests spending exceeds income.")
        
        savings_rate = summary.get('savings_rate', 0)
        if savings_rate > 20:
            insights.append(f"🎯 Excellent savings rate of {savings_rate:.1f}% - you're building wealth effectively!")
        elif savings_rate > 10:
            insights.append(f"👍 Good savings rate of {savings_rate:.1f}% - consider increasing to 20% if possible.")
        else:
            insights.append(f"📊 Current savings rate is {savings_rate:.1f}% - aim for at least 10-20% for financial security.")
        
        return insights
    
    def _generate_category_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights for category report."""
        insights = []
        top_categories = data.get('top_categories', [])
        diversity = data.get('diversity', {})
        
        if top_categories:
            top_cat = top_categories[0]
            insights.append(f"🥇 Top spending category is '{top_cat['name']}' at ${top_cat['amount']:,.2f} ({top_cat['percentage']:.1f}% of total).")
        
        gini = diversity.get('gini_coefficient', 0)
        if gini > 0.5:
            insights.append("📊 Spending is concentrated in few categories - consider diversifying expenses.")
        else:
            insights.append("✅ Well-diversified spending across multiple categories.")
        
        return insights
    
    def _generate_goal_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights for goal report."""
        insights = []
        summary = data.get('summary', {})
        
        at_risk = summary.get('at_risk_count', 0)
        if at_risk > 0:
            insights.append(f"⚠️ {at_risk} goal(s) are at risk - review allocation and timeline.")
        else:
            insights.append("✅ All goals are on track - great progress!")
        
        avg_progress = summary.get('average_progress', 0)
        insights.append(f"📈 Average progress across all goals: {avg_progress:.1f}%")
        
        return insights
    
    def _generate_network_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate insights for network report."""
        insights = []
        graph_stats = data.get('graph_stats', {})
        communities = data.get('communities', {})
        
        density = graph_stats.get('density', 0)
        if density > 0.5:
            insights.append("🕸️ High network density indicates strong interconnections between financial entities.")
        else:
            insights.append("📊 Network shows moderate connectivity - some entities are isolated.")
        
        num_communities = communities.get('num_communities', 0)
        if num_communities > 1:
            insights.append(f"👥 {num_communities} distinct communities detected, suggesting natural groupings in your financial activities.")
        
        return insights
    
    def generate_health_score_report(
        self,
        analytics_data: Dict[str, Any],
        charts: List[go.Figure],
        user_name: Optional[str] = None
    ) -> str:
        """
        Generate financial health score report.
        
        Args:
            analytics_data: Health score analytics results
            charts: List of Plotly figures (gauge, radar, etc.)
            user_name: Optional user name for personalization
        
        Returns:
            HTML report string
        """
        overall_score = analytics_data.get('overall_score', 0)
        rating = analytics_data.get('rating', 'N/A')
        components = analytics_data.get('components', {})
        
        report_data = {
            'title': 'Financial Health Score Report',
            'user_name': user_name or 'User',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'computed_at': analytics_data.get('computed_at', 'N/A'),
            'metrics': [
                {
                    'name': 'Overall Score',
                    'value': f"{overall_score:.1f}/100",
                    'icon': '⭐'
                },
                {
                    'name': 'Health Rating',
                    'value': rating,
                    'icon': '🏆'
                },
                {
                    'name': 'Analysis Period',
                    'value': f"{analytics_data.get('period_days', 30)} days",
                    'icon': '📅'
                }
            ],
            'charts': [self._fig_to_html(fig) for fig in charts],
            'insights': analytics_data.get('recommendations', [])
        }
        
        # Add component breakdown table
        component_table = []
        for comp_name, comp_data in components.items():
            component_table.append({
                'component': comp_name.replace('_', ' ').title(),
                'score': f"{comp_data.get('score', 0):.1f}",
                'weight': f"{comp_data.get('weight', 0) * 100:.0f}%",
                'contribution': f"{comp_data.get('contribution', 0):.1f}"
            })
        
        report_data['component_table'] = component_table
        
        # Create detailed HTML with component breakdown
        detailed_html = f"""
        <div class="component-breakdown">
            <h2>📊 Score Breakdown</h2>
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Component</th>
                        <th>Score</th>
                        <th>Weight</th>
                        <th>Contribution</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{comp['component']}</td>
                        <td>{comp['score']}</td>
                        <td>{comp['weight']}</td>
                        <td>{comp['contribution']}</td>
                    </tr>
                    ''' for comp in component_table])}
                </tbody>
            </table>
        </div>
        """
        
        report_data['additional_sections'] = detailed_html
        
        html_report = self._render_report(report_data)
        return html_report
    
    def save_report(self, html_content: str, filename: str) -> str:
        """
        Save report to HTML file.
        
        Args:
            html_content: HTML report content
            filename: Output filename
        
        Returns:
            Filename of saved file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filename
