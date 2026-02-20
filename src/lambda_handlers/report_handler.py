"""Lambda handler for POST /api/analytics/report."""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.analytics.cash_flow import CashFlowAnalytics
from src.analytics.categories import CategoryAnalytics
from src.analytics.goals import GoalAnalytics
from src.analytics.health_score import HealthScoreAnalytics
from src.analytics.institutions import InstitutionAnalytics
from src.analytics.network import NetworkAnalytics
from src.data.dynamodb_client import DynamoDBClient
from src.utils import date_utils
from src.visualization.charts import ChartGenerator
from src.visualization.reports import ReportGenerator
from src.visualization.s3_uploader import S3Uploader

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Valid report types
REPORT_TYPES = {
    'cash_flow',
    'category',
    'goal',
    'network',
    'health_score',
    'comprehensive',
}


def _get_environment() -> str:
    """Get current deployment environment from env variable."""
    return os.environ.get('ENVIRONMENT', 'devl')


def _get_s3_bucket() -> str:
    """Get S3 bucket name from env variable."""
    return os.environ.get('ANALYTICS_S3_BUCKET', f"cpsc-analytics-{_get_environment()}")


def _get_local_reports_dir() -> Optional[str]:
    """Return local reports directory if LOCAL_REPORTS_DIR is set, else None."""
    return os.environ.get('LOCAL_REPORTS_DIR')


def _save_report_locally(
    html_content: str,
    user_id: str,
    report_type: str,
    reports_dir: str,
) -> dict:
    """
    Save an HTML report to the local filesystem instead of S3.
    Used during local development when S3 is not available.

    Returns a dict with the same keys as S3Uploader.upload_report so the
    caller does not need to branch on local vs remote.
    """
    now = datetime.now(timezone.utc)
    timestamp = int(now.timestamp())
    date_path = now.strftime('%Y/%m/%d')
    filename = f"{report_type}_report_{timestamp}.html"
    key = f"reports/{user_id}/{date_path}/{filename}"

    full_dir = os.path.join(reports_dir, os.path.dirname(key))
    os.makedirs(full_dir, exist_ok=True)
    full_path = os.path.join(reports_dir, key)

    with open(full_path, 'w', encoding='utf-8') as fh:
        fh.write(html_content)

    abs_path = os.path.abspath(full_path).replace('\\', '/')
    logger.info(f"Report saved locally: {abs_path}")

    return {
        'presigned_url': f"file:///{abs_path}",
        'key': key,
        'bucket': reports_dir,
    }


def _get_user_id_from_event(event: Dict[str, Any]) -> Optional[str]:
    """
    Extract user_id from Cognito JWT claims in the API Gateway event.

    API Gateway (with Cognito authorizer) populates:
      event['requestContext']['authorizer']['claims']['sub']
    """
    try:
        claims = (
            event.get('requestContext', {})
                 .get('authorizer', {})
                 .get('claims', {})
        )
        user_id = claims.get('sub')
        if not user_id:
            user_id = (
                event.get('requestContext', {})
                     .get('authorizer', {})
                     .get('userId')
            )
        return user_id
    except Exception as exc:
        logger.error(f"Failed to extract user_id from event: {exc}")
        return None


def _build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Build a standard API Gateway proxy response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body, default=str),
    }


def _validate_request(body: Dict[str, Any]) -> Optional[str]:
    """
    Validate request body.

    Returns an error message string if invalid, otherwise None.
    """
    report_type = body.get('reportType')
    if not report_type:
        return "Missing required field: reportType"
    if report_type not in REPORT_TYPES:
        return (
            f"Invalid reportType '{report_type}'. "
            f"Must be one of: {', '.join(sorted(REPORT_TYPES))}"
        )

    # dateRange is not required for 'goal' (snapshot — not time-windowed)
    if report_type != 'goal':
        date_range = body.get('dateRange', {})
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        if not start_date or not end_date:
            return "Missing required fields: dateRange.start and dateRange.end"

        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return "dateRange dates must be in YYYY-MM-DD format"

        if start_date >= end_date:
            return "dateRange.start must be before dateRange.end"

    return None


def _generate_single_report(
    report_type: str,
    user_id: str,
    start_date: str,
    end_date: str,
    options: Dict[str, Any],
    db_client: DynamoDBClient,
    chart_gen: ChartGenerator,
    report_gen: ReportGenerator,
) -> str:
    """
    Generate HTML for a single report type.

    Returns:
        HTML string of the generated report
    """
    user_name = options.get('userName')

    if report_type == 'cash_flow':
        analytics = CashFlowAnalytics(db_client)
        data = analytics.analyze(user_id, start_date, end_date)
        charts: List = []
        periods = data.get('periods', [])
        if periods:
            labels = [p.get('period') for p in periods]
            deposits = [p.get('total_deposits', 0) for p in periods]
            withdrawals = [p.get('total_withdrawals', 0) for p in periods]
            charts.append(
                chart_gen.create_stacked_bar_chart(
                    categories=labels,
                    series={'Deposits': deposits, 'Withdrawals': withdrawals},
                    title='Cash Flow Over Time',
                )
            )
        return report_gen.generate_cash_flow_report(data, charts, user_name=user_name)

    elif report_type == 'category':
        analytics = CategoryAnalytics(db_client)
        data = analytics.analyze(user_id, start_date, end_date)
        charts = []
        top_cats = data.get('top_categories', [])
        if top_cats:
            labels = [c.get('name') for c in top_cats[:10]]
            values = [c.get('amount', 0) for c in top_cats[:10]]
            charts.append(chart_gen.create_pie_chart(labels=labels, values=values, title='Spending by Category'))
        return report_gen.generate_category_report(data, charts, user_name=user_name)

    elif report_type == 'goal':
        analytics = GoalAnalytics(db_client)
        data = analytics.analyze(user_id)
        charts = []
        goals = data.get('goals', [])
        if goals:
            # Use unique labels: append index when goal names collide so Plotly
            # does not merge duplicate category names and stack their values.
            name_counts: dict = {}
            unique_labels = []
            for g in goals:
                name = g.get('name', 'Unknown')
                if name in name_counts:
                    name_counts[name] += 1
                    unique_labels.append(f"{name} ({name_counts[name]})")
                else:
                    name_counts[name] = 1
                    unique_labels.append(name)
            values = [g.get('progress_percent', 0) for g in goals]
            # Green for complete/inactive goals, red for in-progress ones
            bar_colors = [
                '#28a745' if (g.get('is_completed') or not g.get('is_active', True)) else '#dc3545'
                for g in goals
            ]
            charts.append(chart_gen.create_bar_chart(
                categories=unique_labels,
                values=values,
                title='Goal Progress (%)',
                x_label='Goals',
                y_label='% Complete',
                orientation='h',
                bar_colors=bar_colors,
            ))
        return report_gen.generate_goal_report(data, charts, user_name=user_name, goal_labels=unique_labels)

    elif report_type == 'network':
        analytics = NetworkAnalytics(db_client)
        data = analytics.analyze(user_id, start_date, end_date)
        charts = []
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        if nodes:
            charts.append(
                chart_gen.create_network_graph(
                    nodes=nodes,
                    edges=edges,
                    title='Financial Network Graph',
                )
            )
        # Sankey diagram — flows with a positive weight (spending / allocation)
        sankey_edges = [e for e in edges if e.get('attributes', {}).get('weight', 0) > 0]
        logger.info(f"Network: {len(nodes)} nodes, {len(edges)} edges, {len(sankey_edges)} weighted edges for Sankey")
        if sankey_edges:
            # Build id → display name lookup from node attributes (normalise keys to str)
            # Append node type in parentheses so same-named nodes (e.g. institution + goal
            # both called "asdf") resolve to distinct Sankey labels.
            def _node_label(n):
                attrs = n.get('attributes', {})
                name = attrs.get('name') or str(n['id'])
                node_type = attrs.get('type', '')
                if node_type in ('institution', 'goal', 'category'):
                    return f"{name} ({node_type})"
                return name

            id_to_name = {str(n['id']): _node_label(n) for n in nodes}
            logger.debug(f"Sankey id_to_name: {id_to_name}")
            logger.debug(f"Sankey edges sample: {sankey_edges[:3]}")
            sources = [id_to_name.get(str(e['source']), str(e['source'])) for e in sankey_edges]
            targets = [id_to_name.get(str(e['target']), str(e['target'])) for e in sankey_edges]
            values = [float(e['attributes']['weight']) for e in sankey_edges]
            logger.info(f"Sankey resolved — sources: {sources}, targets: {targets}, values: {values}")
            charts.append(
                chart_gen.create_sankey_diagram(
                    sources=sources,
                    targets=targets,
                    values=values,
                    title='Financial Flow (Institution → Goal / Category)',
                )
            )
        else:
            logger.warning("No weighted edges found — Sankey diagram skipped. Edge attributes sample: %s",
                           [e.get('attributes') for e in edges[:3]])
        return report_gen.generate_network_report(data, charts, user_name=user_name)

    elif report_type == 'health_score':
        start_ts, end_ts = date_utils.get_date_range(start_date, end_date)
        transactions = db_client.get_all_user_transactions(
            user_id=user_id, start_date=start_ts, end_date=end_ts
        )
        institutions = db_client.get_institutions(user_id)
        goals = db_client.get_goals(user_id)
        period_days = (
            datetime.strptime(end_date, '%Y-%m-%d')
            - datetime.strptime(start_date, '%Y-%m-%d')
        ).days
        analytics = HealthScoreAnalytics()
        data = analytics.analyze(
            transactions=transactions,
            institutions=institutions,
            goals=goals,
            period_days=period_days,
            include_recommendations=True,
        )
        charts = []
        # Gauge chart for overall score
        overall_score = data.get('overall_score', 0)
        charts.append(
            chart_gen.create_gauge_chart(
                value=overall_score,
                title='Financial Health Score',
                max_value=100,
            )
        )
        # Radar chart for component breakdown
        components = data.get('components', {})
        if components:
            radar_cats = [k.replace('_', ' ').title() for k in components.keys()]
            radar_vals = [v.get('score', 0) for v in components.values()]
            charts.append(
                chart_gen.create_radar_chart(
                    categories=radar_cats,
                    values=radar_vals,
                    title='Score Dimensions',
                )
            )
        return report_gen.generate_health_score_report(data, charts, user_name=user_name)

    raise ValueError(f"Unsupported report type: {report_type}")


def _generate_comprehensive_report(
    user_id: str,
    start_date: str,
    end_date: str,
    options: Dict[str, Any],
    db_client: DynamoDBClient,
    chart_gen: ChartGenerator,
    report_gen: ReportGenerator,
) -> str:
    """
    Generate a comprehensive multi-section HTML report.

    Combines cash_flow, category, goal, and health_score sections.
    """
    user_name = options.get('userName', 'User')
    sections_html = []

    for rtype in ['cash_flow', 'category', 'goal', 'health_score']:
        try:
            section_html = _generate_single_report(
                report_type=rtype,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                options=options,
                db_client=db_client,
                chart_gen=chart_gen,
                report_gen=report_gen,
            )
            sections_html.append(section_html)
        except Exception as exc:
            logger.warning(f"Skipping {rtype} section in comprehensive report: {exc}")

    if not sections_html:
        raise RuntimeError("No report sections could be generated")

    # Wrap all sections in a single HTML page
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    combined = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Comprehensive Financial Report - {user_name}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }}
.section-divider {{ border: none; border-top: 3px solid #667eea; margin: 40px 0; }}
.section-label {{ text-align: center; color: #667eea; font-size: 1.5em; margin: 20px 0; font-weight: bold; }}
</style>
</head>
<body>
<div style="text-align:center; padding: 30px; background: linear-gradient(135deg,#667eea,#764ba2); color:white; margin-bottom:30px;">
<h1 style="font-size:2.5em;">Comprehensive Financial Report</h1>
<p>Generated for: {user_name} | {now_str} | Period: {start_date} to {end_date}</p>
</div>
{'<hr class="section-divider">'.join(
    f'<div class="report-section">{html}</div>' for html in sections_html
)}
</body>
</html>"""
    return combined


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entry point for POST /api/analytics/report.

    Expected event structure (API Gateway proxy integration):
    {
        "body": "{\"reportType\": \"cash_flow\", \"dateRange\": {\"start\": \"2025-01-01\", \"end\": \"2025-12-31\"}, \"options\": {\"userName\": \"John\"}}",
        "requestContext": {
            "authorizer": {
                "claims": {"sub": "<cognito-user-id>"}
            }
        }
    }

    Response body:
    {
        "reportType": "cash_flow",
        "userId": "<user-id>",
        "generatedAt": "2026-...",
        "reportUrl": "https://s3.../presigned-url",
        "s3Key": "reports/<user>/<date>/cash_flow_report_<time>.html"
    }
    """
    logger.info("report_handler invoked")

    # --- Extract user identity ---
    user_id = _get_user_id_from_event(event)
    if not user_id:
        return _build_response(401, {'error': 'Unauthorized: missing user identity'})

    # --- Parse request body ---
    try:
        raw_body = event.get('body') or '{}'
        body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        return _build_response(400, {'error': f'Invalid JSON body: {exc}'})

    # --- Validate ---
    validation_error = _validate_request(body)
    if validation_error:
        return _build_response(400, {'error': validation_error})

    report_type = body['reportType']
    date_range = body.get('dateRange', {})
    start_date = date_range.get('start')
    end_date = date_range.get('end')
    options = body.get('options', {})

    logger.info(
        f"Generating {report_type} report for user {user_id}"
        + (f" ({start_date} → {end_date})" if start_date and end_date else " (snapshot)")
    )

    # --- Initialize clients ---
    environment = _get_environment()
    bucket_name = _get_s3_bucket()

    try:
        db_client = DynamoDBClient(environment=environment)
    except Exception as exc:
        logger.error(f"Failed to initialize DynamoDB client: {exc}")
        return _build_response(500, {'error': 'Failed to connect to database'})

    chart_gen = ChartGenerator()
    report_gen = ReportGenerator()

    local_reports_dir = _get_local_reports_dir()
    if local_reports_dir:
        s3_uploader = None
    else:
        try:
            s3_uploader = S3Uploader(bucket_name=bucket_name)
        except Exception as exc:
            logger.error(f"Failed to initialize S3 uploader: {exc}")
            return _build_response(500, {'error': 'Failed to initialize storage client'})

    # --- Generate report HTML ---
    try:
        if report_type == 'comprehensive':
            html_content = _generate_comprehensive_report(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                options=options,
                db_client=db_client,
                chart_gen=chart_gen,
                report_gen=report_gen,
            )
        else:
            html_content = _generate_single_report(
                report_type=report_type,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                options=options,
                db_client=db_client,
                chart_gen=chart_gen,
                report_gen=report_gen,
            )
    except ValueError as exc:
        return _build_response(400, {'error': str(exc)})
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}", exc_info=True)
        return _build_response(500, {'error': 'Report generation failed'})

    # --- Upload to S3 (or save locally) ---
    if local_reports_dir:
        logger.info(f"LOCAL_REPORTS_DIR is set — saving report locally to '{local_reports_dir}'")
        try:
            upload_result = _save_report_locally(
                html_content=html_content,
                user_id=user_id,
                report_type=report_type,
                reports_dir=local_reports_dir,
            )
        except Exception as exc:
            logger.error(f"Local report save failed: {exc}", exc_info=True)
            return _build_response(500, {'error': 'Failed to save report locally'})
    else:
        try:
            upload_result = s3_uploader.upload_report(
                html_content=html_content,
                user_id=user_id,
                report_type=report_type,
            )
        except Exception as exc:
            logger.error(f"S3 upload failed: {exc}", exc_info=True)
            return _build_response(500, {'error': 'Failed to store report'})

    # --- Build response ---
    response_body = {
        'reportType': report_type,
        'userId': user_id,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'reportUrl': upload_result.get('presigned_url'),
        's3Key': upload_result.get('key'),
        'bucket': upload_result.get('bucket'),
    }
    if start_date and end_date:
        response_body['dateRange'] = {'start': start_date, 'end': end_date}

    return _build_response(200, response_body)
