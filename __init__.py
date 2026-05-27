"""Special Occasion Plugin for FiestaBoard."""

import datetime
import logging
from src.plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)

class SpecialOccasionsPlugin(PluginBase):

    """A special occasion plugin to automate special day pages"""
    
    @property
    def plugin_id(self) -> str:
        """Return the plugin ID - must match manifest.json 'id' field."""
        return "special_occasions"

    def fetch_data(self) -> PluginResult:
        config = self.config
        if not config:
            return None
        
        # Default state if no occasion matches today
        data = {
            "special_day_type": "N/A",
            "special_day_date": "",
            "special_day_name": "N/A",
            "special_day_description": "N/A",
            "is_today_special": False
        }

        occasions = config.get("occasions", [])
        today = datetime.date.today()

        for occasion in occasions:
            try:
                logger.debug("looping occasions")
                month = int(occasion.get("month", 0))
                logger.debug(month)
                day = int(occasion.get("day", 0))
                logger.debug(day)
            except (ValueError, TypeError):
                logger.error(f"Invalid date format in occasion: {occasion.get('name')}")
                continue

            # If the date matches today, collect the data instead of breaking
            if month == today.month and day == today.day:
                logger.debug("Match on Date")
                data["is_today_special"] = True
                data["special_day_type"] = occasion.get("type")
                data["special_day_date"] = today.isoformat()
                data["special_day_name"] = occasion.get("name")
                data["special_day_description"] = occasion.get("description")

                return PluginResult(available=True, data=data)

        return PluginResult(available=True, data=data)
        
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        return errors

    def cleanup(self) -> None:
        pass
