import os

from azure.cosmos import exceptions, CosmosClient, PartitionKey

# TODO - put these into try/except?

def db_init(database_name, container_name, partition_key):
    # TODO Maybe seperate these into seperate os.environ params?
    AccountEndpoint = os.environ["mattceventsink_DOCUMENTDB"]
    endpoint = AccountEndpoint.split(";")[0].split('=')[1]
    key = AccountEndpoint.split("AccountKey=")[1]
    client = CosmosClient(endpoint, key)
    database = client.get_database_client(database=database_name)
    pk = PartitionKey(partition_key, kind='Hash')
    container = database.create_container_if_not_exists(id=container_name, partition_key=pk)

    return container

def db_add(container, event):
    event['id'] = event['data']['call_id']
    container.create_item(body=event)

def db_delete(container, event):
    container.delete_item(item = event['data']['call_id'], partition_key=event['data']['service_tag'])

def db_query(container, query):
    results = list(container.query_items(query=query, enable_cross_partition_query=True))
    return results    