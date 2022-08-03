# Find-Available-Operator-Event-Sink

This function connects a caller with the best available operator in Pexip Infinity deployments.  This function is deployed as a function app in Azure, and configured as an event sink in Pexip Infinity.

The function stores all events from the event sink in one database, and stores currently active participants in another database.  When a caller (in this case an EMT) calls into connect to the operator, the function looks for operators among the currently active participants and then dials from the EMT's conference to the operator's conference via the Pexip Infinity management API.

Necessary environment variables:

```
DatabaseEndpoint        - endpoint for Azure database for storing all events and active calls
QueueStorageAccount     - endpoint for storage account for queues
ClearDatabaseOnRestart  - string true/false, clears database on eventsink_restart (not yet implemented)
ManagementNodeFQDN      - management node FQDN for management API access
ManagementNodeUsername  - management node username for management API access
ManagementNodePassword  - management node password for management API access
ConferenceNodeFQDN      - conference node FQDN for client API access
SIPDialingDomain        - SIP dialing domain for call to operator
SIPDialLocation         - outgoing location for SIP dial to operator
OperatorServiceTag      - service tag configured for operator conferences (set in policy)
OperatorConferenceBase  - base name for operator conferences (in dial string, will have number appended)
OperatorDisplayName     - name displayed by operator to caller
CallerServiceTag        - service tag configured for caller conferences which will connect to operator (set in policy)
CallerConferenceBase    - base name for caller conferences (displayed to operator upon connection, appended with caller's unique ID)
```