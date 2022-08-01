from ast import operator
import logging
import os
import requests

import cosmosdb_helpers as db_help
import azure.functions as func

db_cont = None

def main(req: func.HttpRequest, outEvents: func.Out[func.Document]) -> func.HttpResponse:
    global db_cont

    def find_operator():
        operators = {}
        #operator_participants = db_help.db_query(db_cont,'SELECT * FROM activeCalls c WHERE c.data.conference LIKE "stsOperator%"')
        operator_participants = db_help.db_query(db_cont,'SELECT * FROM activeCalls c WHERE c.data.service_tag = "sts-operator"')
        for p in operator_participants:
            if not p['data']['conference'] in operators:
                operators[p['data']['conference']] = 1
            else:
                operators[p['data']['conference']] += 1
        
        min_part = 1000
        operator = 'stsOperator1'
        for o in operators.keys():
            if operators[o] < min_part:
                min_part = operators[o]
                operator = o
                
        return operator
            

    if db_cont is None:
        db_cont = db_help.db_init('eventDatabase', 'activeCalls', '/data/service_tag')

    request_body = req.get_body()

    # Get request body
    body = func.Document.from_json(request_body)
    event = dict(body)

    # Send all event to events container to store for reporting TODO send to a queue for furthur processing & reduce lag
    outEvents.set(func.Document.from_json(request_body))

    # Check event type and add or remove to active calls db
    if 'event' in event:    
        event_type = event['event']
        logging.info(f'Event type is: {event_type}')
        
        if event_type == 'participant_connected':
            logging.info(f'Event is type {event_type}, sending to active calls db')
            db_help.db_add(db_cont, event)
            
            if event['data']['service_tag'] == 'sts-emt' and event['data']['call_direction'] == 'in':
                operator = find_operator()
                
                fqdn = os.environ["mgt_node_fqdn"]
                uname = os.environ["mgt_node_user"]
                pwd = os.environ["mgt_node_pwd"]
                dom = os.environ["conf_domain"]
                dial_location = os.environ["dial_location"]
                api_dial = "/api/admin/command/v1/participant/dial/"
                
                data = {
                    'conference_alias': event['data']['destination_alias'],
                    'destination': operator + '@' + dom,
                    'routing': 'manual',
                    'role': 'guest',
                    'remote_display_name': 'STS Operator',
                    'system_location': dial_location
                }
                
                requests.post(fqdn + api_dial, auth=(uname, pwd), json=data)

        elif event_type == 'participant_disconnected':
            logging.info(f'Event type is {event_type}, deleting from active calls db ')
            db_help.db_delete(db_cont, event)
            
        else:
            logging.info(f'Event type is {event_type}, no action')
    
    
        
    return 'OK'