"""Countdown Timer Plugin for FiestaBoard."""

from __future__ import annotations

import logging
import datetime
import math
import hashlib
import hmac
import json

from typing import Any, Dict, List

from src.plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)

class CountdownTimerPlugin(PluginBase):
    """A local timer that counts down automatically and tracks visual blocks."""

    def __init__(self, manifest: Dict[str, Any]) -> None:
        super().__init__(manifest)
        self._payload: Dict[str, Any] = {}
        self._last_updated: str = ""
        
        self._start_time = None
        self._end_time = None
        self._target_time = None
        self._total_seconds = 0.0
        self._status_block_duration = 0.0
        self._max_status_flaps = 0
        self._status_color = ""
        self._status_color_completed = ""
        
        # Track whether a timer is currently active or completely done
        self._timer_in_flight = False 
        self._timer_finished = False

    @property
    def plugin_id(self) -> str:
        """Return the plugin ID - must match manifest.json 'id' field."""
        return "timer"

    def receive_payload(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        raw_body: bytes = b"",
    ) -> None:
        secret = self.config.get("secret", "")
        if secret:
            sig_header = headers.get("x-webhook-signature", "")
            if not sig_header:
                raise PermissionError("Missing X-Webhook-Signature header")
            body_bytes = raw_body if raw_body else json.dumps(payload, separators=(",", ":")).encode()
            expected = "sha256=" + hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig_header, expected):
                raise PermissionError("Invalid webhook signature")
        
        self._payload = payload
        self._last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self._start_time = datetime.datetime.now()
        
        # A new payload arrived, so reset the flight status to False 
        # so fetch_data will parse the new duration on its next run.
        self._timer_in_flight = False
        self._timer_finished = False

    def fetch_data(self) -> PluginResult:
        logger.info("Timer Plugin: fetch_data")
        try:
            now = datetime.datetime.now()

            # 1. SETUP: Only calculate if we aren't flying AND haven't already finished this payload
            if not self._timer_in_flight and not self._timer_finished:
                logger.info("Timer Plugin: #1 SETUP")
                default_measure = self.config.get("default_measure") or "minutes"
                
                # Fetch config variables
                self._max_status_flaps = int(self.config.get("max_status_flaps", 0))
                self._status_color = str(self.config.get("status_color", ""))
                self._status_color_completed = str(self.config.get("status_color_completed", ""))
                
                self._current_duration = float(self._payload.get("duration", 0))
                self._current_measure = str(self._payload.get("measure", default_measure)).strip().lower()

                if self._current_measure == "minutes":
                    self._total_seconds = self._current_duration * 60
                else:
                    self._total_seconds = self._current_duration
                    
                # Calculate status block duration
                if self._max_status_flaps > 0:
                    self._status_block_duration = self._total_seconds / self._max_status_flaps
                else:
                    self._status_block_duration = 0.0
                    
                if self._start_time:
                    self._end_time = self._start_time + datetime.timedelta(seconds=self._total_seconds)
                
                # Setup complete, mark as in flight
                self._timer_in_flight = True

            # 2. TICK: Calculate remaining time and flaps
            minutes_remaining = 0.0
            seconds_remaining = 0
            current_status_flaps = 0
            
            # If we already finished this timer, skip the math entirely
            if self._timer_finished:
                seconds_remaining = 0
                minutes_remaining = 0.0
                current_status_flaps = 0
                
            elif self._end_time:
                logger.info("Timer Plugin: Calculate Time")
                time_left = self._end_time - now
                raw_seconds_left = time_left.total_seconds()
                
                if raw_seconds_left > 0:
                    seconds_remaining = int(raw_seconds_left)
                    minutes_remaining = round(seconds_remaining / 60.0, 2)
                    
                    if self._status_block_duration > 0:
                        elapsed_seconds = self._total_seconds - raw_seconds_left
                        flaps_removed = int(elapsed_seconds // self._status_block_duration)
                        current_status_flaps = max(0, self._max_status_flaps - flaps_removed)
                    else:
                        current_status_flaps = self._max_status_flaps
                else:
                    # The timer has just finished! 
                    seconds_remaining = 0
                    minutes_remaining = 0.0
                    current_status_flaps = 0
                    
                    # Turn off flight status AND mark it as permanently finished
                    self._timer_in_flight = False 
                    self._timer_finished = True 

            # 3. OUTPUT: Format strings for the frontend
            last_updated = self._last_updated or "Never"
            start_time_str = self._start_time.strftime("%Y-%m-%d %H:%M:%S") if self._start_time else "None"
            end_time_str = self._end_time.strftime("%Y-%m-%d %H:%M:%S") if self._end_time else "None"
            
            # Generate the repeated status color string (e.g., "{red}{red}{red}")
            status_display = ("{" + self._status_color + "}") * current_status_flaps if self._status_color else ""
            
            # Generate the padded version by calculating how many flaps have been removed
            completed_flaps = self._max_status_flaps - current_status_flaps
            completed_display = ("{" + self._status_color_completed + "}") * completed_flaps if self._status_color_completed else ""
            status_display_padded = status_display + completed_display

            return PluginResult(
                available=True,
                data={
                    "start_time": start_time_str,
                    "end_time": end_time_str, 
                    "duration": getattr(self, '_current_duration', 0),
                    "measure": getattr(self, '_current_measure', "minutes"),
                    "minutes_remaining": minutes_remaining,
                    "seconds_remaining": seconds_remaining,
                    "status_block_duration": self._status_block_duration,
                    "status_current_length": current_status_flaps,
                    "status_max_length": self._max_status_flaps,
                    "status_display": status_display,
                    "status_display_padded": status_display_padded,
                    "last_updated": last_updated,
                    "timer_in_flight": self._timer_in_flight
                },
            )
        except Exception as e:
            logger.exception("Error reading timer payload")
            return PluginResult(available=False, error=str(e))

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []

    def cleanup(self) -> None:
        pass
