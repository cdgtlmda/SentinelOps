"""
SentinelOps Threat Simulation Scheduler - Cloud Function
Automatically generates threat scenarios and publishes to Pub/Sub for processing
"""

import json
import logging
import os
import random
from datetime import datetime
from typing import Dict, Any, List

from google.cloud import pubsub_v1
from google.cloud import firestore
import functions_framework

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'your-gcp-project-id')
PUBSUB_TOPIC = os.getenv('THREAT_EVENTS_TOPIC', 'threat-events')
FIRESTORE_COLLECTION = os.getenv('FIRESTORE_COLLECTION', 'simulated_threats')

# Initialize clients
publisher = pubsub_v1.PublisherClient()
firestore_client = firestore.Client()
topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)

# Simplified threat scenarios for Cloud Function deployment
THREAT_SCENARIOS = [
    {
        "id": "LOW_BUCKET_PUBLIC",
        "severity": "LOW", 
        "template": {
            "event_type": "BUCKET_PUBLIC_READ",
            "resource": "gs://demo-{bucket_id}",
            "finding": "Public ACL detected on bucket",
            "severity": "LOW",
            "mitre_tactic": "TA0009",
            "remediation_priority": "P3"
        }
    },
    {
        "id": "MED_SUSPICIOUS_LOGIN",
        "severity": "MEDIUM",
        "template": {
            "event_type": "SUSPICIOUS_LOGIN", 
            "actor_ip": "{attacker_ip}",
            "target_user": "{user}",
            "country": "{country}",
            "finding": "Login from unusual geolocation",
            "severity": "MEDIUM",
            "mitre_tactic": "TA0001",
            "mitre_technique": "T1078",
            "remediation_priority": "P2"
        }
    },
    {
        "id": "CRIT_SSH_BRUTE",
        "severity": "CRITICAL",
        "template": {
            "event_type": "SSH_BRUTE_FORCE",
            "actor_ip": "{attacker_ip}",
            "target_vm": "{vm}",
            "match_count": "{attack_count}",
            "finding": "Active SSH brute force attack detected",
            "severity": "CRITICAL",
            "mitre_tactic": "TA0006",
            "mitre_technique": "T1110.001",
            "remediation_priority": "P1"
        }
    },
    {
        "id": "CRIT_RANSOMWARE",
        "severity": "CRITICAL",
        "template": {
            "event_type": "RANSOMWARE_FILE_WRITE",
            "target_vm": "{vm}",
            "extension": ".crypted",
            "file_count": "{file_count}",
            "finding": "Mass file encryption detected - ransomware active",
            "severity": "CRITICAL",
            "mitre_tactic": "TA0040",
            "mitre_technique": "T1486",
            "remediation_priority": "P1"
        }
    },
    {
        "id": "MED_DNS_TUNNEL",
        "severity": "MEDIUM",
        "template": {
            "event_type": "DNS_TUNNELING",
            "actor_ip": "{attacker_ip}",
            "domain": "{domain}",
            "qps": "{qps}",
            "finding": "High-entropy DNS queries suggest tunneling",
            "severity": "MEDIUM",
            "mitre_tactic": "TA0011",
            "mitre_technique": "T1071.004",
            "remediation_priority": "P2"
        }
    }
]

def generate_random_values() -> Dict[str, str]:
    """Generate random values for template substitution"""
    return {
        "bucket_id": f"{random.randint(1000, 9999)}",
        "attacker_ip": f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "user": random.choice(["alice@corp.com", "bob@corp.com", "svc-ci@corp.com"]),
        "country": random.choice(["RU", "CN", "BR", "IR", "NG"]),
        "vm": random.choice(["web-1", "web-2", "db-1", "api-1"]),
        "attack_count": str(random.randint(20, 150)),
        "file_count": str(random.randint(500, 5000)),
        "domain": f"{random.randint(10000000, 99999999)}.bad.tld",
        "qps": str(random.randint(200, 1000))
    }

def substitute_template(template: Dict[str, Any], values: Dict[str, str]) -> Dict[str, Any]:
    """Substitute random values in template"""
    result = {}
    for key, value in template.items():
        if isinstance(value, str):
            # Replace all placeholders in the string
            substituted = value
            for placeholder, replacement in values.items():
                substituted = substituted.replace(f"{{{placeholder}}}", replacement)
            result[key] = substituted
        else:
            result[key] = value
    return result

def generate_threat_scenario(scenario_id: str = None, severity: str = None) -> Dict[str, Any]:
    """Generate a single threat scenario"""
    # Filter scenarios
    available_scenarios = THREAT_SCENARIOS
    
    if scenario_id:
        available_scenarios = [s for s in THREAT_SCENARIOS if s["id"] == scenario_id]
        if not available_scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")
    elif severity:
        available_scenarios = [s for s in THREAT_SCENARIOS if s["severity"] == severity.upper()]
        if not available_scenarios:
            raise ValueError(f"No scenarios found for severity {severity}")
    
    # Select random scenario
    scenario = random.choice(available_scenarios)
    
    # Generate random values
    values = generate_random_values()
    
    # Substitute template
    event_data = substitute_template(scenario["template"], values)
    
    # Add metadata
    event_data.update({
        "scenario_id": scenario["id"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source": "threat_simulator_cloud_function",
        "simulation_id": f"SIM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"
    })
    
    return event_data

def publish_to_pubsub(event_data: Dict[str, Any]) -> None:
    """Publish threat event to Pub/Sub"""
    try:
        message_data = json.dumps(event_data).encode('utf-8')
        
        # Add message attributes
        attributes = {
            'event_type': event_data.get('event_type', 'unknown'),
            'severity': event_data.get('severity', 'MEDIUM'),
            'source': 'threat_simulator',
            'timestamp': event_data.get('timestamp', '')
        }
        
        # Publish message
        future = publisher.publish(topic_path, message_data, **attributes)
        message_id = future.result()
        
        logger.info(f"Published threat event {event_data.get('simulation_id')} with message ID: {message_id}")
        
    except Exception as e:
        logger.error(f"Failed to publish to Pub/Sub: {e}")
        raise

def store_in_firestore(event_data: Dict[str, Any]) -> None:
    """Store threat simulation in Firestore for tracking"""
    try:
        doc_ref = firestore_client.collection(FIRESTORE_COLLECTION).document(event_data.get('simulation_id'))
        doc_ref.set({
            **event_data,
            'created_at': firestore.SERVER_TIMESTAMP,
            'processed': False
        })
        
        logger.info(f"Stored simulation {event_data.get('simulation_id')} in Firestore")
        
    except Exception as e:
        logger.error(f"Failed to store in Firestore: {e}")
        # Don't re-raise - storage failure shouldn't break the simulation

@functions_framework.http
def simulate_threats(request):
    """
    HTTP Cloud Function to simulate threat events
    
    Query parameters:
    - count: Number of scenarios to generate (default: 1, max: 20)
    - severity: Filter by severity (LOW, MEDIUM, CRITICAL)
    - scenario_id: Generate specific scenario
    - intensity: Simulation intensity (low, medium, high)
    """
    try:
        # Parse request parameters
        count = min(int(request.args.get('count', 1)), 20)
        severity = request.args.get('severity')
        scenario_id = request.args.get('scenario_id')
        intensity = request.args.get('intensity', 'medium')
        
        # Adjust count based on intensity
        intensity_multipliers = {'low': 1, 'medium': 2, 'high': 3}
        count = count * intensity_multipliers.get(intensity, 1)
        count = min(count, 50)  # Cap at 50 events
        
        logger.info(f"Generating {count} threat scenarios (intensity: {intensity})")
        
        generated_events = []
        
        for i in range(count):
            try:
                # Generate scenario
                event_data = generate_threat_scenario(scenario_id, severity)
                
                # Publish to Pub/Sub for processing
                publish_to_pubsub(event_data)
                
                # Store in Firestore for tracking
                store_in_firestore(event_data)
                
                generated_events.append({
                    'simulation_id': event_data.get('simulation_id'),
                    'event_type': event_data.get('event_type'),
                    'severity': event_data.get('severity'),
                    'timestamp': event_data.get('timestamp')
                })
                
            except Exception as e:
                logger.error(f"Failed to generate scenario {i+1}: {e}")
                continue
        
        # Return response
        response = {
            'status': 'success',
            'message': f'Generated {len(generated_events)} threat scenarios',
            'events': generated_events,
            'parameters': {
                'count': count,
                'severity': severity,
                'scenario_id': scenario_id,
                'intensity': intensity
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return json.dumps(response), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        logger.error(f"Function execution failed: {e}")
        
        error_response = {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return json.dumps(error_response), 500, {'Content-Type': 'application/json'}

@functions_framework.cloud_event
def scheduled_threat_simulation(cloud_event):
    """
    Cloud Scheduler triggered function for automated threat simulation
    
    This function is triggered by Cloud Scheduler to generate realistic
    threat scenarios at regular intervals for testing and demonstration.
    """
    try:
        logger.info("Starting scheduled threat simulation")
        
        # Determine simulation parameters based on time of day
        current_hour = datetime.utcnow().hour
        
        if 9 <= current_hour <= 17:  # Business hours - more activity
            count = random.randint(3, 8)
            severity_weights = {"LOW": 0.5, "MEDIUM": 0.35, "CRITICAL": 0.15}
        elif 18 <= current_hour <= 23:  # Evening - moderate activity
            count = random.randint(2, 5)
            severity_weights = {"LOW": 0.4, "MEDIUM": 0.4, "CRITICAL": 0.2}
        else:  # Night/early morning - low activity but higher severity
            count = random.randint(1, 3)
            severity_weights = {"LOW": 0.2, "MEDIUM": 0.3, "CRITICAL": 0.5}
        
        logger.info(f"Generating {count} scenarios for hour {current_hour}")
        
        generated_scenarios = []
        
        for i in range(count):
            # Choose severity based on weights
            rand = random.random()
            cumulative = 0
            chosen_severity = "MEDIUM"
            
            for severity, weight in severity_weights.items():
                cumulative += weight
                if rand <= cumulative:
                    chosen_severity = severity
                    break
            
            try:
                # Generate and publish scenario
                event_data = generate_threat_scenario(severity=chosen_severity)
                publish_to_pubsub(event_data)
                store_in_firestore(event_data)
                
                generated_scenarios.append(event_data.get('simulation_id'))
                
            except Exception as e:
                logger.error(f"Failed to generate scheduled scenario {i+1}: {e}")
                continue
        
        logger.info(f"Scheduled simulation complete: generated {len(generated_scenarios)} scenarios")
        
        # Update schedule statistics in Firestore
        try:
            stats_ref = firestore_client.collection('simulation_stats').document('scheduled_runs')
            stats_ref.set({
                'last_run': firestore.SERVER_TIMESTAMP,
                'scenarios_generated': len(generated_scenarios),
                'run_hour': current_hour,
                'total_runs': firestore.Increment(1)
            }, merge=True)
        except Exception as e:
            logger.warning(f"Failed to update statistics: {e}")
        
    except Exception as e:
        logger.error(f"Scheduled simulation failed: {e}")
        raise

def get_simulation_stats():
    """Get statistics about threat simulations"""
    try:
        # Query recent simulations
        recent_sims = firestore_client.collection(FIRESTORE_COLLECTION)\
            .order_by('created_at', direction='DESCENDING')\
            .limit(100)\
            .stream()
        
        severity_counts = {}
        event_type_counts = {}
        total_sims = 0
        
        for doc in recent_sims:
            data = doc.to_dict()
            severity = data.get('severity', 'UNKNOWN')
            event_type = data.get('event_type', 'UNKNOWN')
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            total_sims += 1
        
        return {
            'total_simulations': total_sims,
            'severity_breakdown': severity_counts,
            'event_type_breakdown': event_type_counts,
            'available_scenarios': len(THREAT_SCENARIOS)
        }
        
    except Exception as e:
        logger.error(f"Failed to get simulation stats: {e}")
        return {'error': str(e)}

@functions_framework.http
def simulation_stats(request):
    """HTTP endpoint to get simulation statistics"""
    try:
        stats = get_simulation_stats()
        
        response = {
            'status': 'success',
            'data': stats,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return json.dumps(response), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        logger.error(f"Stats endpoint failed: {e}")
        
        error_response = {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return json.dumps(error_response), 500, {'Content-Type': 'application/json'}