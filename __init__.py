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
        # Default state if no occasion matches today
        data = {
            "special_day_type": "",
            "special_day_date": "",
            "special_day_name": "",
            "special_day_description": "",
            "is_today_special": False
        }

        occasions = config.get("occasions", [])
        today = datetime.date.today()

        # Lists to hold data in case there are multiple events today
        matched_names = []
        matched_descriptions = []
        matched_types = []

        for occasion in occasions:
            try:
                month = int(occasion.get("month", 0))
                day = int(occasion.get("day", 0))
            except (ValueError, TypeError):
                logger.error(f"Invalid date format in occasion: {occasion.get('name')}")
                continue

            # If the date matches today, collect the data instead of breaking
            if month == today.month and day == today.day:
                data["is_today_special"] = True
                data["special_day_date"] = today.isoformat()
                
                name = occasion.get("name")
                if name:
                    matched_names.append(name)
                    
                description = occasion.get("description")
                if description:
                    matched_descriptions.append(description)
                    
                occasion_type = occasion.get("type", "Holiday")
                if occasion_type:
                    matched_types.append(occasion_type)

        # If we found any matches, join them together for the variables
        if data["is_today_special"]:
            data["special_day_name"] = " & ".join(matched_names)
            
            # Filter out empty descriptions before joining
            valid_descriptions = [desc for desc in matched_descriptions if desc.strip()]
            data["special_day_description"] = " | ".join(valid_descriptions)
            
            # Deduplicate types
            unique_types = list(dict.fromkeys(matched_types))
            data["special_day_type"] = " / ".join(unique_types)

        return PluginResult(available=True, data=data)
        
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors = []
        return errors

    def cleanup(self) -> None:
        pass
