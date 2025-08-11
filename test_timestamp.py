from datetime import datetime
import pytz

def format_timestamp_ist(timestamp_str):
    """Convert ISO timestamp to IST format: Date : Time (HH:MM AM/PM)"""
    try:
        # Parse the ISO timestamp
        if isinstance(timestamp_str, str):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = timestamp_str
        
        # Convert to IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            utc = pytz.timezone('UTC')
            dt = utc.localize(dt)
        
        ist_time = dt.astimezone(ist)
        
        # Format as: Date : Time (HH:MM AM/PM)
        formatted_date = ist_time.strftime('%Y-%m-%d')
        formatted_time = ist_time.strftime('%I:%M %p')
        
        return f"{formatted_date} : {formatted_time}"
    except Exception as e:
        print(f"Error formatting timestamp {timestamp_str}: {e}")
        return str(timestamp_str)

# Test with the current timestamp
test_timestamp = "2025-08-10T19:26:08.319736"
formatted = format_timestamp_ist(test_timestamp)
print(f"Original: {test_timestamp}")
print(f"Formatted: {formatted}")
