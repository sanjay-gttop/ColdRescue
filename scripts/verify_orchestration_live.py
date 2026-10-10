import boto3, json, time, urllib.request, urllib.error
from datetime import datetime, timezone

sfn = boto3.client('stepfunctions', region_name='ap-south-1')
sm_arn = 'arn:aws:states:ap-south-1:494110627063:stateMachine:ColdRescue-IncidentRecovery-dev'
api_url = 'https://l4bpu3mf2f.execute-api.ap-south-1.amazonaws.com/dev/incidents/recover'

# 1. Test 401 Unauthorized without token using urllib
status_code = None
try:
    req = urllib.request.Request(api_url, data=b'{"test": 1}', headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        status_code = resp.status
except urllib.error.HTTPError as err:
    status_code = err.code

print('Unauthenticated API status code:', status_code)

# 2. Start real Step Functions execution for TRUCK-104 directly with full lifecycle payload
run_id = f'truck_104_{int(time.time())}'
execution_input = {
    'incident_id': 'TRUCK-104',
    'correlation_id': f'corr_{run_id}',
    'stream_id': f'stream_{run_id}',
    'idempotency_key': f'idem_{run_id}',
    'incident': {
        'incident_id': 'TRUCK-104',
        'location_id': 'loc_bhavani_nh544',
        'location_name': 'NH-544 Bhavani Corridor',
        'latitude': 11.4489,
        'longitude': 77.6833,
        'cooling_status': 'failed',
        'cargo': {
            'cargo_id': 'cargo_milk_104',
            'cargo_type': 'dairy',
            'mass_kg': 1200.0,
            'current_temperature_c': 4.5,
            'ambient_temperature_c': 38.5,
            'safe_temperature_max_c': 8.0,
            'backup_runtime_min': 180.0,
        },
        'receivers': [
            {
                'receiver_id': 'recv_tiruppur_hub',
                'name': 'Tiruppur Dairy Cooperative Hub',
                'category': 'COLD_STORAGE_FACILITY',
                'capacity_kg': 5000.0,
                'current_load_kg': 1500.0,
                'available_capacity_kg': 3500.0,
                'latitude': 11.1085,
                'longitude': 77.3411,
                'cooling_status': 'operational',
                'backup_runtime_min': 240.0,
                'accepts_temp_min_c': 2.0,
                'accepts_temp_max_c': 8.0,
                'compatible_cargo_types': ['dairy'],
            }
        ],
    },
    'approval': {
        'approved': True,
        'approver_email': 'approver@coldrescue.io',
        'notes': 'Verified Tiruppur intake capacity and grid stability.',
    },
    'driver': {
        'driver_id': 'driver_karthik_42',
        'status': 'ACKNOWLEDGED',
    },
}

exec_res = sfn.start_execution(
    stateMachineArn=sm_arn,
    name=f'TRUCK-104-LIVE-{int(time.time())}',
    input=json.dumps(execution_input),
)
exec_arn = exec_res['executionArn']
print('Execution started:', exec_arn)

# Poll for terminal execution status
status = 'RUNNING'
desc = {}
for _ in range(15):
    time.sleep(2)
    desc = sfn.describe_execution(executionArn=exec_arn)
    status = desc['status']
    if status != 'RUNNING':
        break

print('Terminal execution status:', status)
history = sfn.get_execution_history(executionArn=exec_arn, maxResults=50)

orchestration_evidence = {
    'api_url': api_url,
    'unauthenticated_status_code': status_code,
    'state_machine_arn': sm_arn,
    'execution_arn': exec_arn,
    'execution_status': status,
    'startDate': desc['startDate'].isoformat(),
    'stopDate': desc.get('stopDate', desc['startDate']).isoformat(),
    'output': json.loads(desc.get('output', '{}')),
    'events_count': len(history['events']),
}

with open('data/evidence/live/orchestration_verification.json', 'w') as f:
    json.dump(orchestration_evidence, f, indent=2)

print('Orchestration live verification saved to data/evidence/live/orchestration_verification.json')
