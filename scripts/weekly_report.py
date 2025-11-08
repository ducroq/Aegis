"""
Weekly Report Script - Generate Report and Send Alerts

This script is intended to be run weekly (e.g., every Sunday via cron/Task Scheduler).
It:
1. Loads the latest risk scores from history
2. Checks if alert conditions are met using AlertLogic
3. Generates a formatted report
4. Sends email alert if thresholds are crossed
5. Records alert in history

Usage:
    python scripts/weekly_report.py [--force] [--dry-run]

Options:
    --force      Force send alert even if conditions not met (for testing)
    --dry-run    Generate report but don't send email
"""

import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.alerts.alert_logic import AlertLogic
from src.alerts.email_sender import EmailSender
from src.alerts.history_manager import HistoryManager


def setup_logging(verbose: bool = False):
    """Configure logging for the script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / 'data' / 'logs' / 'weekly_report.log')
        ]
    )


def load_latest_scores() -> dict:
    """
    Load the latest risk scores from history.

    Returns:
        Dict with latest risk assessment
    """
    logger = logging.getLogger(__name__)

    history_file = project_root / 'data' / 'history' / 'risk_scores.csv'

    if not history_file.exists():
        logger.error(f"History file not found: {history_file}")
        logger.error("Run daily_update.py first to create history")
        return None

    # Read last line of CSV
    import csv
    with open(history_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        logger.error("No data in history file")
        return None

    latest = rows[-1]

    # Convert to expected format
    result = {
        'date': latest['date'],
        'overall_score': float(latest['overall_risk']),
        'tier': latest['tier'],
        'dimension_scores': {
            'recession': float(latest['recession']),
            'credit': float(latest['credit']),
            'valuation': float(latest['valuation']),
            'liquidity': float(latest['liquidity']),
            'positioning': float(latest['positioning'])
        }
    }

    # Get historical scores for trend analysis
    if len(rows) >= 4:
        history = [float(row['overall_risk']) for row in rows[-5:]]  # Last 5 weeks
        result['history'] = history
    else:
        result['history'] = [float(row['overall_risk']) for row in rows]

    logger.info(f"Loaded latest scores from {latest['date']}")
    logger.info(f"  Overall Risk: {result['overall_score']:.2f}/10 ({result['tier']})")

    return result


def check_alert_conditions(risk_data: dict, alert_logic: AlertLogic) -> dict:
    """
    Check if alert conditions are met.

    Args:
        risk_data: Latest risk assessment with history
        alert_logic: AlertLogic instance

    Returns:
        Dict with alert decision
    """
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("CHECKING ALERT CONDITIONS")
    logger.info("="*60)

    # Format current result for AlertLogic
    current_result = {
        'overall_score': risk_data['overall_score'],
        'tier': risk_data['tier'],
        'dimension_scores': risk_data['dimension_scores']
    }

    # Format history (most recent first, for last few weeks)
    history = []
    if 'history' in risk_data and len(risk_data['history']) > 1:
        # Create simple history entries with just scores
        for score in reversed(risk_data['history'][:-1]):  # Exclude current (last)
            history.append({
                'overall_score': score,
                'dimension_scores': risk_data['dimension_scores']  # Simplified
            })

    # Check if alert should be triggered
    triggered, tier, reason, details = alert_logic.should_alert(current_result, history)

    result = {
        'triggered': triggered,
        'tier': tier,
        'reason': reason,
        'details': details,
        'signals': details.get('signals', [])
    }

    if triggered:
        logger.warning(f"ALERT TRIGGERED: {reason}")
        logger.warning(f"  Tier: {tier}")
    else:
        logger.info(f"No alert: {reason}")

    return result


def generate_report(risk_data: dict, alert_decision: dict, alert_logic: AlertLogic) -> str:
    """
    Generate formatted report text.

    Args:
        risk_data: Latest risk assessment
        alert_decision: Alert decision from AlertLogic
        alert_logic: AlertLogic instance for formatting

    Returns:
        Formatted report string
    """
    logger = logging.getLogger(__name__)
    logger.info("Generating report...")

    report = []
    report.append("="*60)
    report.append("AEGIS RISK REPORT")
    report.append(f"Date: {risk_data['date']}")
    report.append("="*60)
    report.append("")

    # Overall risk
    report.append(f"Overall Risk Score: {risk_data['overall_score']:.2f}/10")
    report.append(f"Risk Tier: {risk_data['tier']}")
    report.append("")

    # Alert status
    if alert_decision['triggered']:
        report.append(f"*** ALERT ***: {alert_decision['reason']}")
        report.append("")

    # Dimension scores
    report.append("Dimension Scores:")
    for dim, score in risk_data['dimension_scores'].items():
        # Simple visual indicator (ASCII-safe)
        if score >= 8.0:
            indicator = "[RED]"
        elif score >= 6.5:
            indicator = "[YELLOW]"
        else:
            indicator = "[GREEN]"
        report.append(f"  {dim.capitalize():12s}: {score:5.2f}/10 {indicator}")
    report.append("")

    # Trend
    if len(risk_data.get('history', [])) > 1:
        recent_trend = risk_data['history'][-1] - risk_data['history'][-2]
        trend_arrow = "UP" if recent_trend > 0 else "DOWN" if recent_trend < 0 else "FLAT"
        report.append(f"Recent Trend: {trend_arrow} {recent_trend:+.2f} points")
        report.append("")

    # Recommendations
    if risk_data['tier'] == 'RED':
        report.append("Recommendation:")
        report.append("  [!] SEVERE RISK - Consider major defensive positioning")
        report.append("  - Review portfolio allocation")
        report.append("  - Build significant cash position (30-50%)")
        report.append("  - Consider hedging strategies")
    elif risk_data['tier'] == 'YELLOW':
        report.append("Recommendation:")
        report.append("  [!] ELEVATED RISK - Monitor closely")
        report.append("  - Review portfolio for vulnerabilities")
        report.append("  - Consider building cash position (10-30%)")
        report.append("  - Reduce leverage")
    else:
        report.append("Recommendation:")
        report.append("  [OK] NORMAL CONDITIONS - Stay the course")
        report.append("  - Maintain current allocation")
        report.append("  - Continue regular monitoring")

    report.append("")
    report.append("="*60)
    report.append("This is an automated report from Aegis Risk System")
    report.append("="*60)

    return "\n".join(report)


def send_alert_email(
    risk_data: dict,
    alert_decision: dict,
    report: str,
    email_sender: EmailSender,
    dry_run: bool = False
):
    """
    Send alert email if conditions are met.

    Args:
        risk_data: Latest risk assessment
        alert_decision: Alert decision
        report: Formatted report text
        email_sender: EmailSender instance
        dry_run: If True, don't actually send
    """
    logger = logging.getLogger(__name__)

    if dry_run:
        logger.info("="*60)
        logger.info("DRY RUN - NOT SENDING EMAIL")
        logger.info("="*60)
        logger.info("Would send email with report:")
        logger.info("\n" + report)
        return

    if not alert_decision['triggered']:
        logger.info("No alert triggered, not sending email")
        return

    logger.info("="*60)
    logger.info("SENDING ALERT EMAIL")
    logger.info("="*60)

    try:
        # Create email content
        subject = f"⚠️ Aegis Alert: Risk {risk_data['overall_score']:.1f}/10 ({risk_data['tier']})"

        result = email_sender.send_alert_email(
            subject=subject,
            risk_score=risk_data['overall_score'],
            tier=risk_data['tier'],
            dimension_scores=risk_data['dimension_scores'],
            signals=alert_decision.get('signals', []),
            report_text=report
        )

        if result['success']:
            logger.info(f"✓ Email sent successfully to {result['recipient']}")
        else:
            logger.error(f"✗ Failed to send email: {result['error']}")

    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Weekly risk report and alerts')
    parser.add_argument('--force', action='store_true',
                        help='Force send alert even if conditions not met')
    parser.add_argument('--dry-run', action='store_true',
                        help='Generate report but don\'t send email')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    # Setup
    (project_root / 'data' / 'logs').mkdir(parents=True, exist_ok=True)
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        logger.info("="*60)
        logger.info(f"WEEKLY REPORT STARTING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)

        # Initialize components
        config = ConfigManager()
        alert_logic = AlertLogic(config)
        email_sender = EmailSender(config)
        history_manager = HistoryManager()

        # Load latest scores
        risk_data = load_latest_scores()
        if risk_data is None:
            logger.error("Failed to load risk data")
            return 1

        # Check alert conditions
        alert_decision = check_alert_conditions(risk_data, alert_logic)

        # Force alert if requested
        if args.force and not alert_decision['triggered']:
            logger.warning("Forcing alert due to --force flag")
            alert_decision['triggered'] = True
            alert_decision['reason'] = "Forced alert (testing)"

        # Generate report
        report = generate_report(risk_data, alert_decision, alert_logic)

        # Send email if alert triggered
        send_alert_email(risk_data, alert_decision, report, email_sender, dry_run=args.dry_run)

        # Record alert in history (if sent)
        if alert_decision['triggered'] and not args.dry_run:
            history_manager.record_alert(
                date=risk_data['date'],
                risk_score=risk_data['overall_score'],
                tier=alert_decision['tier'],
                reason=alert_decision['reason']
            )
            logger.info("Recorded alert in history")

        # Summary
        logger.info("="*60)
        logger.info("WEEKLY REPORT COMPLETED")
        logger.info("="*60)
        logger.info(f"Risk: {risk_data['overall_score']:.2f}/10 ({risk_data['tier']})")
        if alert_decision['triggered']:
            logger.info(f"Alert sent: {alert_decision['reason']}")

        return 0

    except Exception as e:
        logger.error(f"WEEKLY REPORT FAILED: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
