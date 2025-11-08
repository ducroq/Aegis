"""
Email Sender Module

Sends formatted email alerts when risk thresholds are exceeded.

Email format:
1. Subject: Attention-grabbing for alerts
2. Risk summary: Overall score + tier + change
3. Dimension breakdown: Individual scores with trends
4. Key evidence: Specific data points that triggered alert
5. Suggested actions: What to consider
6. Track record: Historical alert accuracy (placeholder for now)
"""

import logging
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class EmailSender:
    """
    Send formatted email alerts for portfolio risk warnings.
    """

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize email sender.

        Args:
            config: ConfigManager instance. If None, creates new one.
        """
        if config is None:
            config = ConfigManager()
        self.config = config

        # Get email configuration
        self.smtp_server = config.get_secret('smtp_server') or 'smtp.gmail.com'
        smtp_port_str = config.get_secret('smtp_port') or '587'
        self.smtp_port = int(smtp_port_str)
        self.smtp_user = config.get_secret('smtp_user')
        self.smtp_password = config.get_secret('smtp_password')
        self.from_email = config.get_secret('from_email') or self.smtp_user
        self.to_email = config.get_secret('to_email')

        logger.info(
            f"Email sender initialized: {self.from_email} -> {self.to_email}"
        )

    def send_alert(
        self,
        alert_summary: Dict[str, Any],
        dry_run: bool = False
    ) -> bool:
        """
        Send alert email.

        Args:
            alert_summary: Alert summary from AlertLogic.get_alert_summary()
            dry_run: If True, don't actually send email (just log)

        Returns:
            True if email sent successfully, False otherwise
        """
        # Generate email content
        subject = self._generate_subject(alert_summary)
        html_body = self._generate_html_body(alert_summary)
        text_body = self._generate_text_body(alert_summary)

        if dry_run:
            # For dry run, use placeholder if no email configured
            to_email = self.to_email or "user@example.com"
            logger.info("[DRY RUN] Would send email:")
            logger.info(f"  To: {to_email}")
            logger.info(f"  Subject: {subject}")
            logger.info(f"  Body length: {len(text_body)} chars")
            print("\n" + "=" * 60)
            print("EMAIL PREVIEW (DRY RUN)")
            print("=" * 60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print("-" * 60)
            print(text_body)
            print("=" * 60)
            return True

        # Send actual email
        if not self.to_email:
            logger.error("No recipient email configured")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Alert email sent successfully to {self.to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False

    def _generate_subject(self, alert_summary: Dict[str, Any]) -> str:
        """Generate email subject line."""
        tier = alert_summary['tier']
        score = alert_summary['current_score']

        if tier == 'RED':
            emoji = 'ALERT'
            prefix = 'SEVERE'
        elif tier == 'YELLOW':
            emoji = 'WARNING'
            prefix = 'ELEVATED'
        else:
            emoji = 'NOTICE'
            prefix = 'WATCH'

        return f"[{emoji}] Portfolio Risk: {prefix} - Score {score:.1f}/10"

    def _generate_text_body(self, alert_summary: Dict[str, Any]) -> str:
        """Generate plain text email body."""
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("AEGIS PORTFOLIO RISK ALERT")
        lines.append("=" * 60)
        lines.append("")

        # Overall risk summary
        tier = alert_summary['tier']
        score = alert_summary['current_score']
        reason = alert_summary['reason']

        lines.append(f"RISK LEVEL: {tier}")
        lines.append(f"OVERALL SCORE: {score:.1f}/10")
        lines.append("")
        lines.append(f"REASON: {reason}")
        lines.append("")

        # Trends
        if 'trends' in alert_summary and alert_summary['trends']:
            lines.append("-" * 60)
            lines.append("TREND ANALYSIS")
            lines.append("-" * 60)
            trends = alert_summary['trends']

            if '1w_change' in trends:
                direction = trends.get('1w_direction', '')
                lines.append(f"1-Week Change: {trends['1w_change']:+.1f} ({direction})")

            if '4w_change' in trends:
                direction = trends.get('4w_direction', '')
                lines.append(f"4-Week Change: {trends['4w_change']:+.1f} ({direction})")

            if '12w_change' in trends:
                direction = trends.get('12w_direction', '')
                lines.append(f"12-Week Change: {trends['12w_change']:+.1f} ({direction})")

            lines.append("")

        # Dimension breakdown
        lines.append("-" * 60)
        lines.append("RISK DIMENSION BREAKDOWN")
        lines.append("-" * 60)

        dimension_scores = alert_summary['dimension_scores']
        dimension_trends = alert_summary.get('trends', {}).get('dimension_trends', {})

        for dim, score in sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True):
            trend = dimension_trends.get(dim, {}).get('direction', '')
            trend_str = f" ({trend})" if trend else ""
            lines.append(f"{dim.capitalize():15s}: {score:.1f}/10{trend_str}")

        lines.append("")

        # Key evidence
        if alert_summary.get('key_evidence'):
            lines.append("-" * 60)
            lines.append("KEY EVIDENCE")
            lines.append("-" * 60)
            for evidence in alert_summary['key_evidence']:
                lines.append(f"  - {evidence}")
            lines.append("")

        # Suggested actions
        lines.append("-" * 60)
        lines.append("SUGGESTED ACTIONS")
        lines.append("-" * 60)

        if tier == 'RED':
            lines.append("  * SEVERE RISK: Consider major defensive positioning")
            lines.append("  * Review portfolio allocation immediately")
            lines.append("  * Consider raising cash position (20-40%)")
            lines.append("  * Review stop-loss levels on risky positions")
            lines.append("  * Consider hedging strategies")
        elif tier == 'YELLOW':
            lines.append("  * ELEVATED RISK: Monitor portfolio closely")
            lines.append("  * Review and rebalance if needed")
            lines.append("  * Consider building cash position (10-20%)")
            lines.append("  * Trim positions that have run up significantly")
            lines.append("  * Avoid adding new risk")
        else:
            lines.append("  * WATCH: Stay informed but no immediate action needed")
            lines.append("  * Continue regular monitoring")
            lines.append("  * Review specific risk dimensions flagged above")

        lines.append("")

        # Footer
        lines.append("-" * 60)
        lines.append("IMPORTANT DISCLAIMER")
        lines.append("-" * 60)
        lines.append("This is an automated risk assessment based on quantitative")
        lines.append("indicators. It is NOT investment advice. Make your own")
        lines.append("decisions based on your personal risk tolerance and goals.")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("System: Aegis Portfolio Risk Monitor")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_html_body(self, alert_summary: Dict[str, Any]) -> str:
        """Generate HTML email body."""
        tier = alert_summary['tier']
        score = alert_summary['current_score']
        reason = alert_summary['reason']

        # Color scheme based on tier
        if tier == 'RED':
            header_color = '#dc3545'  # Red
            tier_badge = '<span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">RED ALERT</span>'
        elif tier == 'YELLOW':
            header_color = '#ffc107'  # Yellow
            tier_badge = '<span style="background: #ffc107; color: black; padding: 4px 12px; border-radius: 4px; font-weight: bold;">YELLOW WARNING</span>'
        else:
            header_color = '#28a745'  # Green
            tier_badge = '<span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">WATCH</span>'

        # Build HTML with string concatenation to avoid nested f-string issues
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {header_color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; }}
                .score {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; border-bottom: 2px solid #dee2e6; padding-bottom: 5px; }}
                .dimension {{ padding: 8px; margin: 5px 0; background: white; border-radius: 4px; }}
                .dimension-name {{ display: inline-block; width: 150px; font-weight: bold; }}
                .dimension-score {{ float: right; font-weight: bold; }}
                .evidence {{ padding: 8px; margin: 5px 0; background: white; border-left: 3px solid {header_color}; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
                .action {{ padding: 8px; margin: 5px 0; background: #fff3cd; border-left: 3px solid #ffc107; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AEGIS RISK ALERT</h1>
                    <div class="score">{score:.1f}/10</div>
                    {tier_badge}
                </div>
                <div class="content">
                    <div class="section">
                        <p><strong>Reason:</strong> {reason}</p>
                    </div>
        """

        # Trends
        if 'trends' in alert_summary and alert_summary['trends']:
            trends = alert_summary['trends']
            html += '<div class="section"><div class="section-title">Trend Analysis</div>'
            if '1w_change' in trends:
                w1_change = trends["1w_change"]
                w1_dir = trends.get("1w_direction", "")
                html += f'<p>1-Week Change: <strong>{w1_change:+.1f}</strong> ({w1_dir})</p>'
            if '4w_change' in trends:
                w4_change = trends["4w_change"]
                w4_dir = trends.get("4w_direction", "")
                html += f'<p>4-Week Change: <strong>{w4_change:+.1f}</strong> ({w4_dir})</p>'
            html += '</div>'

        # Dimension breakdown
        html += '<div class="section"><div class="section-title">Risk Dimensions</div>'
        dimension_scores = alert_summary['dimension_scores']
        for dim, dim_score in sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True):
            score_color = '#dc3545' if dim_score >= 8 else ('#ffc107' if dim_score >= 6 else '#28a745')
            html += f'''
            <div class="dimension">
                <span class="dimension-name">{dim.capitalize()}</span>
                <span class="dimension-score" style="color: {score_color};">{dim_score:.1f}/10</span>
            </div>
            '''
        html += '</div>'

        # Key evidence
        if alert_summary.get('key_evidence'):
            html += '<div class="section"><div class="section-title">Key Evidence</div>'
            for evidence in alert_summary['key_evidence']:
                html += f'<div class="evidence">{evidence}</div>'
            html += '</div>'

        # Suggested actions
        html += '<div class="section"><div class="section-title">Suggested Actions</div>'
        if tier == 'RED':
            actions = [
                'SEVERE RISK: Consider major defensive positioning',
                'Review portfolio allocation immediately',
                'Consider raising cash position (20-40%)',
                'Review stop-loss levels on risky positions'
            ]
        elif tier == 'YELLOW':
            actions = [
                'ELEVATED RISK: Monitor portfolio closely',
                'Review and rebalance if needed',
                'Consider building cash position (10-20%)',
                'Avoid adding new risk'
            ]
        else:
            actions = [
                'WATCH: Stay informed but no immediate action needed',
                'Continue regular monitoring'
            ]

        for action in actions:
            html += f'<div class="action">{action}</div>'
        html += '</div>'

        # Footer
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html += f'''
                    <div class="footer">
                        <p><strong>DISCLAIMER:</strong> This is an automated risk assessment based on quantitative indicators. It is NOT investment advice. Make your own decisions based on your personal risk tolerance and goals.</p>
                        <p>Generated: {timestamp}<br>
                        System: Aegis Portfolio Risk Monitor</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

        return html


def main():
    """Test email sender."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing Email Sender...\n")
    print("=" * 60)

    email_sender = EmailSender()

    # Test alert summary
    test_summary = {
        'should_alert': True,
        'tier': 'YELLOW',
        'reason': 'Risk score 7.2/10 at YELLOW level and rising rapidly (+1.5 points in 4 weeks)',
        'current_score': 7.2,
        'dimension_scores': {
            'recession': 8.0,
            'credit': 7.5,
            'valuation': 6.0,
            'liquidity': 5.5,
            'positioning': 4.0
        },
        'trends': {
            '1w_change': 0.3,
            '1w_direction': 'UP',
            '4w_change': 1.5,
            '4w_direction': 'UP_SHARP',
            'dimension_trends': {
                'recession': {'change': 0.5, 'direction': 'UP'},
                'credit': {'change': 0.2, 'direction': 'UP'}
            }
        },
        'key_evidence': [
            '[RECESSION] CRITICAL: Unemployment claims spiking +12.5% YoY',
            '[CREDIT] WARNING: HY spreads widening rapidly (8.5 bps/day)',
            '[RECESSION] WARNING: Yield curve inverted (-0.6pp)',
            'Recession risk: 8.0/10',
            'Credit risk: 7.5/10'
        ],
        'all_signals': {}
    }

    # Dry run (preview only)
    print("TEST: Dry Run Email Preview")
    print("-" * 60)
    success = email_sender.send_alert(test_summary, dry_run=True)

    if success:
        print("\n" + "=" * 60)
        print("Email Sender test PASSED")
        print("=" * 60)
        print("\nNOTE: This was a dry run. To send actual emails:")
        print("1. Configure SMTP settings in config/credentials/secrets.ini")
        print("2. Set smtp_server, smtp_port, smtp_user, smtp_password")
        print("3. Set from_email and to_email")
        print("4. Call send_alert() with dry_run=False")
    else:
        print("\nEmail Sender test FAILED")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
