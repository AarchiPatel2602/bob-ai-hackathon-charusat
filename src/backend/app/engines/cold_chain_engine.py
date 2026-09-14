import datetime
from typing import List, Dict, Any, Optional
from backend.app.models.sensor import SensorReading
from backend.app.models.shipment import Shipment
from backend.app.models.compliance import ComplianceProfile

def evaluate_temperature_severity(
    temperature: float,
    min_temp: float,
    max_temp: float,
    profile: Optional[ComplianceProfile] = None
) -> Dict[str, Any]:
    """
    Evaluates a temperature value against permissible bounds and compliance profile rules.
    """
    critical_delta = profile.critical_temp_delta if profile else 2.0
    
    if min_temp <= temperature <= max_temp:
        # Check warning buffer (within 0.5 degrees of bound)
        if (max_temp - temperature <= 0.5) or (temperature - min_temp <= 0.5):
            return {
                "is_excursion": False,
                "severity": "WARNING",
                "reason": f"Temperature {temperature:.1f}°C is within limits but nearing threshold [{min_temp}°C - {max_temp}°C]"
            }
        return {
            "is_excursion": False,
            "severity": "NORMAL",
            "reason": f"Temperature {temperature:.1f}°C is within standard range [{min_temp}°C - {max_temp}°C]"
        }

    # Out of range excursion
    is_above = temperature > max_temp
    delta = round(temperature - max_temp if is_above else min_temp - temperature, 2)
    direction = "above maximum" if is_above else "below minimum"

    if delta >= critical_delta:
        severity = "CRITICAL"
    elif delta >= 1.0:
        severity = "MAJOR"
    else:
        severity = "WARNING"

    return {
        "is_excursion": True,
        "severity": severity,
        "delta": delta,
        "reason": f"Excursion of {delta}°C {direction} (Current: {temperature:.1f}°C, Permissible: {min_temp}°C - {max_temp}°C)"
    }

def analyze_excursion_run(readings: List[SensorReading], min_temp: float, max_temp: float) -> Dict[str, Any]:
    """
    Computes duration, peak excursion temperature, and active excursion span from chronological readings.
    """
    if not readings:
        return {
            "has_active_excursion": False,
            "duration_minutes": 0.0,
            "peak_temperature": None,
            "severity": "NORMAL",
            "excursion_points_count": 0
        }

    # Chronological sort (oldest to newest)
    sorted_readings = sorted(readings, key=lambda r: r.timestamp)
    latest_reading = sorted_readings[-1]

    if not latest_reading.is_excursion:
        return {
            "has_active_excursion": False,
            "duration_minutes": 0.0,
            "peak_temperature": latest_reading.temperature,
            "severity": latest_reading.severity or "NORMAL",
            "excursion_points_count": 0
        }

    # Find where the latest continuous excursion streak began
    excursion_streak = []
    for r in reversed(sorted_readings):
        if r.is_excursion:
            excursion_streak.append(r)
        else:
            break

    excursion_streak.reverse()
    start_time = excursion_streak[0].timestamp
    end_time = excursion_streak[-1].timestamp
    
    # Calculate duration
    duration_minutes = round((end_time - start_time).total_seconds() / 60.0, 1)
    if duration_minutes < 1.0 and len(excursion_streak) > 1:
        duration_minutes = float(len(excursion_streak) * 4) # estimated ~4 min per sensor ping in simulation
    elif duration_minutes < 1.0:
        duration_minutes = 3.5

    peak_temp = max(r.temperature for r in excursion_streak)
    highest_severity = "WARNING"
    for r in excursion_streak:
        if r.severity == "CRITICAL":
            highest_severity = "CRITICAL"
            break
        elif r.severity == "MAJOR":
            highest_severity = "MAJOR"

    return {
        "has_active_excursion": True,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_minutes": duration_minutes,
        "peak_temperature": round(peak_temp, 2),
        "severity": highest_severity,
        "excursion_points_count": len(excursion_streak)
    }

def calculate_predictive_breach(readings: List[SensorReading], min_temp: float, max_temp: float) -> Dict[str, Any]:
    """
    Computes temperature trend rate (deg C / minute) from recent readings
    and projects time until upper/lower threshold breach.
    """
    if len(readings) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "trend_per_5min": 0.0,
            "estimated_minutes_to_breach": None,
            "message": "Insufficient sensor history for prediction."
        }

    # Take the last 3-5 readings
    sorted_readings = sorted(readings, key=lambda r: r.timestamp)
    sample = sorted_readings[-5:]
    
    t1 = sample[0].timestamp
    t2 = sample[-1].timestamp
    delta_seconds = (t2 - t1).total_seconds()
    
    # In live/stepped simulation, if timestamps are within 1 second, simulate time step of 300s (5 mins) per step
    if delta_seconds < 10:
        delta_minutes = (len(sample) - 1) * 5.0
    else:
        delta_minutes = delta_seconds / 60.0

    delta_temp = sample[-1].temperature - sample[0].temperature
    rate_per_minute = delta_temp / delta_minutes if delta_minutes > 0 else 0.0
    trend_5min = round(rate_per_minute * 5.0, 2)

    latest_temp = sample[-1].temperature

    # If temperature is rising towards max_temp
    if rate_per_minute > 0.01:
        if latest_temp > max_temp:
            return {
                "status": "BREACHED",
                "trend_per_5min": trend_5min,
                "estimated_minutes_to_breach": 0.0,
                "message": f"Threshold already breached! Trend: +{trend_5min:.2f}°C per 5 min."
            }
        
        remaining_headroom = max_temp - latest_temp
        minutes_to_breach = round(remaining_headroom / rate_per_minute, 1)
        
        if minutes_to_breach <= 35.0:
            return {
                "status": "BREACH_LIKELY",
                "trend_per_5min": trend_5min,
                "estimated_minutes_to_breach": minutes_to_breach,
                "message": f"TEMPERATURE BREACH LIKELY: Upper limit ({max_temp}°C) crossing in ~{minutes_to_breach:.0f} mins (Trend: +{trend_5min:.2f}°C/5min)"
            }

    # If temperature is dropping towards min_temp
    elif rate_per_minute < -0.01:
        if latest_temp < min_temp:
            return {
                "status": "BREACHED",
                "trend_per_5min": trend_5min,
                "estimated_minutes_to_breach": 0.0,
                "message": f"Lower threshold breached! Trend: {trend_5min:.2f}°C per 5 min."
            }
        remaining_headroom = latest_temp - min_temp
        minutes_to_breach = round(remaining_headroom / abs(rate_per_minute), 1)
        if minutes_to_breach <= 35.0:
            return {
                "status": "BREACH_LIKELY",
                "trend_per_5min": trend_5min,
                "estimated_minutes_to_breach": minutes_to_breach,
                "message": f"FREEZE BREACH LIKELY: Lower limit ({min_temp}°C) crossing in ~{minutes_to_breach:.0f} mins (Trend: {trend_5min:.2f}°C/5min)"
            }

    return {
        "status": "STABLE",
        "trend_per_5min": trend_5min,
        "estimated_minutes_to_breach": None,
        "message": f"Temperature trajectory is stable ({trend_5min:+.2f}°C per 5 min)."
    }
