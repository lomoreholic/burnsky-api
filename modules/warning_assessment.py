"""Current warning impact aggregation for burnsky predictions."""

from datetime import datetime


class CurrentWarningAssessmentService:
    """Convert active warning details into a capped burnsky score impact."""

    def __init__(self, parse_warning, calculate_impact, now=datetime.now):
        self._parse_warning = parse_warning
        self._calculate_impact = calculate_impact
        self._now = now

    def assess(self, warning_data):
        if not warning_data or not warning_data.get('details'):
            return 0, [], []

        now = self._now()
        time_of_day = 'sunset' if 17 <= now.hour <= 19 else 'sunrise' if 5 <= now.hour <= 7 else 'day'
        season = self._season_for_month(now.month)
        active_warnings = []
        analysis = []
        total_impact = 0

        for warning in warning_data['details']:
            warning_text = warning if isinstance(warning, str) else str(warning)
            warning_info = self._parse_warning(warning_text)
            impact, multipliers = self._calculate_impact(warning_info, time_of_day, season)
            active_warnings.append(warning_text)
            analysis.append({
                'warning_text': warning_text,
                'category': warning_info['category'],
                'subcategory': warning_info['subcategory'],
                'severity': warning_info['severity'],
                'level': warning_info['level'],
                'impact_score': impact,
                'impact_factors': warning_info['impact_factors'],
                'adjustments': multipliers,
                'area_specific': warning_info['area_specific']
            })
            total_impact += impact

        extreme_count = sum(item['severity'] == 'extreme' for item in analysis)
        severe_count = sum(item['severity'] == 'severe' for item in analysis)
        max_impact = 45 if extreme_count >= 2 else 35 if extreme_count else 30 if severe_count >= 2 else 25 if severe_count else 20
        return min(total_impact, max_impact), active_warnings, analysis

    @staticmethod
    def _season_for_month(month):
        if month in (12, 1, 2):
            return 'winter'
        if month in (3, 4, 5):
            return 'spring'
        if month in (9, 10, 11):
            return 'autumn'
        return 'summer'