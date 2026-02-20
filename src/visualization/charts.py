"""Chart generation utilities for financial analytics visualizations."""

from typing import Dict, List, Any, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from datetime import datetime
import base64
from io import BytesIO


class ChartGenerator:
    """Generate various chart types for financial analytics."""
    
    def __init__(self, theme: str = 'plotly_white'):
        """
        Initialize chart generator.
        
        Args:
            theme: Plotly template theme (plotly, plotly_white, plotly_dark, etc.)
        """
        self.theme = theme
        self.default_colors = px.colors.qualitative.Set2
    
    def create_line_chart(
        self,
        data: Dict[str, List[float]],
        x_axis: List[str],
        title: str,
        x_label: str = "Date",
        y_label: str = "Amount",
        height: int = 500
    ) -> go.Figure:
        """
        Create a line chart for time series data.
        
        Args:
            data: Dictionary mapping series names to value lists
            x_axis: List of x-axis labels (dates/periods)
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        for i, (name, values) in enumerate(data.items()):
            fig.add_trace(go.Scatter(
                x=x_axis,
                y=values,
                mode='lines+markers',
                name=name,
                line=dict(width=3, color=self.default_colors[i % len(self.default_colors)]),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            xaxis=dict(title=x_label, gridcolor='#e0e0e0'),
            yaxis=dict(title=y_label, gridcolor='#e0e0e0'),
            template=self.theme,
            hovermode='x unified',
            height=height,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)"
            )
        )
        
        return fig
    
    def create_bar_chart(
        self,
        categories: List[str],
        values: List[float],
        title: str,
        x_label: str = "Category",
        y_label: str = "Amount",
        orientation: str = 'v',
        height: int = 500,
        bar_colors: Optional[List[str]] = None
    ) -> go.Figure:
        """
        Create a bar chart for categorical comparisons.
        
        Args:
            categories: List of category names
            values: List of values for each category
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            orientation: 'v' for vertical, 'h' for horizontal
            height: Chart height in pixels
            bar_colors: Optional list of per-bar color strings. When provided,
                        overrides the default colorscale.
        
        Returns:
            Plotly Figure object
        """
        color_kwargs = (
            dict(color=bar_colors)
            if bar_colors is not None
            else dict(color=values, colorscale='Blues', showscale=False)
        )
        if orientation == 'h':
            fig = go.Figure(data=[go.Bar(
                y=categories,
                x=values,
                orientation='h',
                marker=dict(**color_kwargs),
                text=[f"{v:.1f}%" if y_label == '% Complete' else f"${v:,.2f}" for v in values],
                textposition='auto'
            )])
            fig.update_layout(
                xaxis=dict(title=y_label),
                yaxis=dict(title=x_label)
            )
        else:
            fig = go.Figure(data=[go.Bar(
                x=categories,
                y=values,
                marker=dict(**color_kwargs),
                text=[f"{v:.1f}%" if y_label == '% Complete' else f"${v:,.2f}" for v in values],
                textposition='auto'
            )])
            fig.update_layout(
                xaxis=dict(title=x_label),
                yaxis=dict(title=y_label)
            )
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            template=self.theme,
            height=height,
            showlegend=False
        )
        
        return fig
    
    def create_pie_chart(
        self,
        labels: List[str],
        values: List[float],
        title: str,
        donut: bool = False,
        height: int = 500
    ) -> go.Figure:
        """
        Create a pie or donut chart for proportional data.
        
        Args:
            labels: List of slice labels
            values: List of values for each slice
            title: Chart title
            donut: If True, creates a donut chart
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        """
        hole_size = 0.4 if donut else 0.0
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=hole_size,
            marker=dict(colors=self.default_colors),
            textposition='auto',
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            template=self.theme,
            height=height,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )
        
        return fig
    
    def create_stacked_bar_chart(
        self,
        categories: List[str],
        data_series: Dict[str, List[float]],
        title: str,
        x_label: str = "Category",
        y_label: str = "Amount",
        height: int = 500
    ) -> go.Figure:
        """
        Create a stacked bar chart for multi-series categorical data.
        
        Args:
            categories: List of category names (x-axis)
            data_series: Dictionary mapping series names to value lists
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        for i, (name, values) in enumerate(data_series.items()):
            fig.add_trace(go.Bar(
                name=name,
                x=categories,
                y=values,
                marker=dict(color=self.default_colors[i % len(self.default_colors)])
            ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            xaxis=dict(title=x_label),
            yaxis=dict(title=y_label),
            barmode='stack',
            template=self.theme,
            height=height,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255,255,255,0.8)"
            )
        )
        
        return fig
    
    def create_area_chart(
        self,
        data: Dict[str, List[float]],
        x_axis: List[str],
        title: str,
        x_label: str = "Date",
        y_label: str = "Amount",
        stacked: bool = False,
        height: int = 500
    ) -> go.Figure:
        """
        Create an area chart for time series data.
        
        Args:
            data: Dictionary mapping series names to value lists
            x_axis: List of x-axis labels
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            stacked: If True, creates a stacked area chart
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        for i, (name, values) in enumerate(data.items()):
            fig.add_trace(go.Scatter(
                x=x_axis,
                y=values,
                mode='lines',
                name=name,
                fill='tonexty' if i > 0 and stacked else 'tozeroy',
                line=dict(width=2, color=self.default_colors[i % len(self.default_colors)]),
                stackgroup='one' if stacked else None
            ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            xaxis=dict(title=x_label, gridcolor='#e0e0e0'),
            yaxis=dict(title=y_label, gridcolor='#e0e0e0'),
            template=self.theme,
            hovermode='x unified',
            height=height,
            showlegend=True
        )
        
        return fig
    
    def create_scatter_plot(
        self,
        x_data: List[float],
        y_data: List[float],
        labels: Optional[List[str]] = None,
        title: str = "Scatter Plot",
        x_label: str = "X Axis",
        y_label: str = "Y Axis",
        height: int = 500
    ) -> go.Figure:
        """
        Create a scatter plot for correlation analysis.
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            labels: Optional labels for each point
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        """
        fig = go.Figure(data=go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            text=labels,
            marker=dict(
                size=12,
                color=list(range(len(x_data))),
                colorscale='Viridis',
                showscale=False
            ),
            hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            xaxis=dict(title=x_label),
            yaxis=dict(title=y_label),
            template=self.theme,
            height=height
        )
        
        return fig
    
    def create_heatmap(
        self,
        z_data: List[List[float]],
        x_labels: List[str],
        y_labels: List[str],
        title: str = "Heatmap",
        colorscale: str = 'Blues',
        height: int = 500
    ) -> go.Figure:
        """
        Create a heatmap for matrix data.
        
        Args:
            z_data: 2D list of values
            x_labels: X-axis labels
            y_labels: Y-axis labels
            title: Chart title
            colorscale: Plotly colorscale name
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        """
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=x_labels,
            y=y_labels,
            colorscale=colorscale,
            text=[[f"${val:,.2f}" for val in row] for row in z_data],
            texttemplate='%{text}',
            textfont={"size": 10},
            hovertemplate='%{y} - %{x}<br>Value: $%{z:,.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            template=self.theme,
            height=height
        )
        
        return fig
    
    def create_network_graph(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        title: str = "Network Graph",
        height: int = 600
    ) -> go.Figure:
        """
        Create a network graph visualization.
        
        Args:
            nodes: List of node dictionaries with 'id' and 'attributes'
            edges: List of edge dictionaries with 'source', 'target', 'attributes'
            title: Chart title
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        """
        # Build NetworkX graph for layout calculation
        G = nx.Graph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node['id'], **node.get('attributes', {}))
        
        # Add edges
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], **edge.get('attributes', {}))
        
        # Calculate layout
        if G.number_of_nodes() == 0:
            pos = {}
        elif G.number_of_nodes() == 1:
            pos = {list(G.nodes())[0]: (0, 0)}
        else:
            pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Create edge traces
        edge_trace = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color='#888'),
                hoverinfo='none',
                showlegend=False
            ))
        
        # Create node traces by type
        node_types = {}
        for node in G.nodes():
            node_data = G.nodes[node]
            node_type = node_data.get('type', 'default')
            if node_type not in node_types:
                node_types[node_type] = {'x': [], 'y': [], 'text': [], 'ids': []}
            
            x, y = pos[node]
            node_types[node_type]['x'].append(x)
            node_types[node_type]['y'].append(y)
            node_types[node_type]['text'].append(node_data.get('name', node))
            node_types[node_type]['ids'].append(node)
        
        # Color mapping for node types
        type_colors = {
            'institution': '#1f77b4',
            'goal': '#ff7f0e',
            'category': '#2ca02c',
            'tag': '#d62728',
            'default': '#9467bd'
        }
        
        # Create node traces
        node_traces = []
        for node_type, data in node_types.items():
            node_traces.append(go.Scatter(
                x=data['x'],
                y=data['y'],
                mode='markers+text',
                name=node_type.title(),
                marker=dict(
                    size=20,
                    color=type_colors.get(node_type, type_colors['default']),
                    line=dict(width=2, color='white')
                ),
                text=data['text'],
                textposition='top center',
                textfont=dict(size=10),
                hovertemplate='<b>%{text}</b><br>Type: ' + node_type + '<extra></extra>'
            ))
        
        # Create figure
        fig = go.Figure(data=edge_trace + node_traces)
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            template=self.theme,
            showlegend=True,
            hovermode='closest',
            height=height,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def create_gauge_chart(
        self,
        value: float,
        title: str,
        max_value: float = 100.0,
        threshold_colors: Optional[List[Tuple[float, str]]] = None,
        height: int = 400
    ) -> go.Figure:
        """
        Create a gauge chart for single metric visualization.
        
        Args:
            value: Current value
            title: Chart title
            max_value: Maximum value for the gauge
            threshold_colors: List of (threshold, color) tuples
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        """
        if threshold_colors is None:
            threshold_colors = [
                (0.33 * max_value, 'red'),
                (0.67 * max_value, 'yellow'),
                (max_value, 'green')
            ]
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 20}},
            delta={'reference': max_value * 0.75},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, threshold_colors[0][0]], 'color': threshold_colors[0][1]},
                    {'range': [threshold_colors[0][0], threshold_colors[1][0]], 'color': threshold_colors[1][1]},
                    {'range': [threshold_colors[1][0], threshold_colors[2][0]], 'color': threshold_colors[2][1]}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.90
                }
            }
        ))
        
        fig.update_layout(
            template=self.theme,
            height=height
        )
        
        return fig
    
    def create_sankey_diagram(
        self,
        sources: List[str],
        targets: List[str],
        values: List[float],
        title: str,
        node_labels: Optional[List[str]] = None,
        height: int = 600
    ) -> go.Figure:
        """
        Create a Sankey diagram for flow visualization.
        
        Args:
            sources: List of source node names
            targets: List of target node names
            values: List of flow values
            title: Chart title
            node_labels: Optional custom node labels (defaults to unique sources+targets)
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        
        Example:
            sources = ['Income', 'Income', 'Savings']
            targets = ['Groceries', 'Utilities', 'Emergency Fund']
            values = [500, 200, 300]
        """
        # Create unique node list from sources and targets (for index mapping)
        unique_nodes = list(dict.fromkeys(sources + targets))
        
        # Use custom labels if provided, otherwise use node names
        display_labels = node_labels if node_labels is not None else unique_nodes
        
        # Map source/target names to indices
        label_to_idx = {label: idx for idx, label in enumerate(unique_nodes)}
        
        # Convert source/target names to indices
        source_indices = [label_to_idx[s] for s in sources]
        target_indices = [label_to_idx[t] for t in targets]
        
        # Create color palette
        node_colors = px.colors.qualitative.Set3[:len(display_labels)]
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=display_labels,
                color=node_colors
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color='rgba(0,0,0,0.2)'
            )
        )])
        
        fig.update_layout(
            title=title,
            template=self.theme,
            height=height,
            font=dict(size=12)
        )
        
        return fig
    
    def create_radar_chart(
        self,
        categories: List[str],
        values: List[float],
        title: str,
        max_value: float = 100.0,
        series_name: str = "Score",
        comparison_values: Optional[List[float]] = None,
        comparison_name: str = "Previous",
        height: int = 500
    ) -> go.Figure:
        """
        Create a radar (spider) chart for multi-dimensional data.
        
        Args:
            categories: List of dimension names
            values: List of values for each dimension
            title: Chart title
            max_value: Maximum value for the radar scale
            series_name: Name of the primary data series
            comparison_values: Optional second series for comparison
            comparison_name: Name of the comparison series
            height: Chart height in pixels
        
        Returns:
            Plotly Figure object
        
        Example:
            categories = ['Savings', 'Goals', 'Diversity', 'Utilization', 'Regularity']
            values = [85, 75, 60, 90, 70]
        """
        fig = go.Figure()
        
        # Add main data series
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=series_name,
            line=dict(color='rgb(0, 123, 255)'),
            marker=dict(size=8)
        ))
        
        # Add comparison series if provided
        if comparison_values is not None:
            fig.add_trace(go.Scatterpolar(
                r=comparison_values,
                theta=categories,
                fill='toself',
                name=comparison_name,
                line=dict(color='rgba(255, 123, 0, 0.6)'),
                marker=dict(size=6),
                opacity=0.7
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max_value],
                    showticklabels=True,
                    tickfont=dict(size=10)
                ),
                angularaxis=dict(
                    tickfont=dict(size=12)
                )
            ),
            title=title,
            template=self.theme,
            height=height,
            showlegend=True
        )
        
        return fig
    
    def save_chart_html(self, fig: go.Figure, filename: str) -> str:
        """
        Save chart as HTML file.
        
        Args:
            fig: Plotly Figure object
            filename: Output filename
        
        Returns:
            Filename of saved file
        """
        fig.write_html(filename)
        return filename
    
    def save_chart_image(
        self,
        fig: go.Figure,
        filename: str,
        format: str = 'png',
        width: int = 1200,
        height: int = 800
    ) -> str:
        """
        Save chart as static image (requires kaleido).
        
        Args:
            fig: Plotly Figure object
            filename: Output filename
            format: Image format ('png', 'jpeg', 'svg', 'pdf')
            width: Image width in pixels
            height: Image height in pixels
        
        Returns:
            Filename of saved file
        """
        fig.write_image(filename, format=format, width=width, height=height)
        return filename
    
    def chart_to_base64(
        self,
        fig: go.Figure,
        format: str = 'png',
        width: int = 1200,
        height: int = 800
    ) -> str:
        """
        Convert chart to base64 encoded string for embedding.
        
        Args:
            fig: Plotly Figure object
            format: Image format ('png', 'jpeg')
            width: Image width in pixels
            height: Image height in pixels
        
        Returns:
            Base64 encoded image string
        """
        img_bytes = fig.to_image(format=format, width=width, height=height)
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return f"data:image/{format};base64,{img_base64}"
