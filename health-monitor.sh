#!/bin/bash
# Health monitoring script for freaziepeazie.app
# Run this via crontab every 5 minutes: */5 * * * * /opt/freezer-app/health-monitor.sh

SITE_URL="https://freaziepeazie.app"
LOG_FILE="/opt/freezer-app/logs/health-monitor.log"
ALERT_EMAIL="admin@freaziepeazie.app"  # Change this to your email

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to send alert
send_alert() {
    local subject="$1"
    local message="$2"
    
    # Log the alert
    log_message "ALERT: $subject - $message"
    
    # Send email if mail is configured
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null
    fi
    
    # Could also integrate with Slack, Discord, etc.
    # curl -X POST -H 'Content-type: application/json' \
    #   --data '{"text":"'"$subject: $message"'"}' \
    #   YOUR_SLACK_WEBHOOK_URL
}

# Check main site
check_site() {
    local url="$1"
    local name="$2"
    
    if curl -f -s --max-time 10 "$url" > /dev/null 2>&1; then
        log_message "✅ $name is healthy"
        return 0
    else
        log_message "❌ $name is down"
        return 1
    fi
}

# Check database health
check_database() {
    if docker-compose exec -T api python3 -c "
import sys
sys.path.append('.')
try:
    from database import SessionLocal
    db = SessionLocal()
    db.execute('SELECT 1')
    db.close()
    print('Database OK')
except Exception as e:
    print(f'Database Error: {e}')
    exit(1)
" >/dev/null 2>&1; then
        log_message "✅ Database is healthy"
        return 0
    else
        log_message "❌ Database is unhealthy"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 90 ]; then
        log_message "❌ Disk space critical: ${usage}%"
        send_alert "Disk Space Critical" "Disk usage is at ${usage}%. Immediate action required."
        return 1
    elif [ "$usage" -gt 80 ]; then
        log_message "⚠️  Disk space warning: ${usage}%"
        send_alert "Disk Space Warning" "Disk usage is at ${usage}%. Consider cleanup."
        return 1
    else
        log_message "✅ Disk space healthy: ${usage}%"
        return 0
    fi
}

# Check container health
check_containers() {
    local unhealthy_containers=$(docker-compose ps | grep -v "Up" | grep -v "State" | wc -l)
    
    if [ "$unhealthy_containers" -gt 0 ]; then
        log_message "❌ $unhealthy_containers container(s) are not running"
        send_alert "Container Health Issue" "$unhealthy_containers containers are not in 'Up' state"
        return 1
    else
        log_message "✅ All containers are healthy"
        return 0
    fi
}

# Main health check
main() {
    log_message "Starting health check..."
    
    local issues=0
    
    # Check main endpoints
    if ! check_site "$SITE_URL/health" "Main Health Endpoint"; then
        issues=$((issues + 1))
    fi
    
    if ! check_site "$SITE_URL/api/health" "API Health Endpoint"; then
        issues=$((issues + 1))
    fi
    
    if ! check_site "$SITE_URL/" "Frontend"; then
        issues=$((issues + 1))
    fi
    
    # Check system health
    if ! check_database; then
        issues=$((issues + 1))
    fi
    
    if ! check_disk_space; then
        issues=$((issues + 1))
    fi
    
    if ! check_containers; then
        issues=$((issues + 1))
    fi
    
    # Overall status
    if [ "$issues" -eq 0 ]; then
        log_message "🎉 All systems healthy"
    else
        log_message "⚠️  Found $issues issue(s)"
        
        # If site is completely down, try auto-recovery
        if ! curl -f -s --max-time 5 "$SITE_URL/health" > /dev/null 2>&1; then
            log_message "🔄 Attempting auto-recovery..."
            
            # Restart containers
            cd /opt/freezer-app
            docker-compose restart
            
            # Wait and recheck
            sleep 30
            if curl -f -s --max-time 10 "$SITE_URL/health" > /dev/null 2>&1; then
                log_message "✅ Auto-recovery successful"
                send_alert "Site Auto-Recovery Success" "Site was down but has been automatically recovered."
            else
                log_message "❌ Auto-recovery failed"
                send_alert "Site Down - Manual Intervention Required" "Site is down and auto-recovery failed. Manual intervention required."
            fi
        fi
    fi
    
    log_message "Health check completed"
    echo "" >> "$LOG_FILE"  # Add blank line for readability
}

# Change to app directory
cd /opt/freezer-app || exit 1

# Run main function
main

# Rotate logs if they get too large (keep last 1000 lines)
if [ -f "$LOG_FILE" ] && [ $(wc -l < "$LOG_FILE") -gt 1000 ]; then
    tail -n 500 "$LOG_FILE" > "${LOG_FILE}.tmp"
    mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi