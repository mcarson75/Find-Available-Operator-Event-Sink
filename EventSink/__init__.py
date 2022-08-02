from ast import operator
import logging
import os
import requests

import cosmosdb_helpers as db_help
import azure.functions as func

db_active_calls = None
db_events = None

def main(req: func.HttpRequest) -> func.HttpResponse:
    global db_active_calls
    global db_events

    def find_operator():
        operators = {}
        query = 'SELECT * FROM activeCalls c WHERE c.data.service_tag = "' + os.environ["OperatorServiceTag"] + '"'
        operator_participants = db_help.db_query(db_active_calls, query)
        for p in operator_participants:
            if not p['data']['conference'] in operators:
                operators[p['data']['conference']] = 1
            else:
                operators[p['data']['conference']] += 1
        
        min_part = 1000
        operator = os.environ["OperatorConferenceBase"] + '1'
        for o in operators.keys():
            if operators[o] < min_part:
                min_part = operators[o]
                operator = o
                
        return operator
            

    if db_active_calls is None:
        db_active_calls = db_help.db_init('eventDatabase', 'activeCalls', '/data/service_tag')

    if db_events is None:
        db_events = db_help.db_init('eventDatabase', 'events', '/event')

    request_body = req.get_body()

    # Get request body
    body = func.Document.from_json(request_body)
    event = dict(body)

    # Send all event to events container to store for reporting TODO send to a queue for furthur processing & reduce lag
    #outEvents.set(func.Document.from_json(request_body))
    db_help.db_add(db_events, event)

    # Check event type and add or remove to active calls db
    if 'event' in event:    
        event_type = event['event']
        logging.info(f'Event type is: {event_type}')
        
        if event_type == 'participant_connected':
            logging.info(f'Event is type {event_type}, sending to active calls db')
            db_help.db_add(db_active_calls, event)
            
            if event['data']['service_tag'] == os.environ["CallerServiceTag"] and event['data']['call_direction'] == 'in':
                operator = find_operator()
                
                fqdn = os.environ["ManagementNodeFQDN"]
                uname = os.environ["ManagementNodeUsername"]
                pwd = os.environ["ManagementNodePassword"]
                dom = os.environ["SIPDialingDomain"]
                dial_location = os.environ["SIPDialLocation"]
                api_dial = "/api/admin/command/v1/participant/dial/"
                
                data = {
                    'conference_alias': event['data']['destination_alias'],
                    'destination': operator + '@' + dom,
                    'routing': 'manual',
                    'role': 'guest',
                    'remote_display_name': os.environ["OperatorDisplayName"],
                    'system_location': dial_location
                }
                
                requests.post(fqdn + api_dial, auth=(uname, pwd), json=data)

        elif event_type == 'participant_disconnected':
            logging.info(f'Event type is {event_type}, deleting from active calls db ')
            db_help.db_delete(db_active_calls, event)
        
        elif event_type == 'eventsink_started' and os.environ["ClearDatabaseOnRestart"] == 'true':
            db_help.db_clean('eventDatabase', db_active_calls)
            db_help.db_clean('eventDatabase', db_events)
            
        else:
            logging.info(f'Event type is {event_type}, no action')
    
    
        
    return 'OK'