# Find-Available-Operator-Event-Sink

This function connects a caller with the best available operator in Pexip Infinity deployments.  This function is deployed as a function app in Azure, and configured as an event sink in Pexip Infinity.

The function stores all events from the event sink in one database, and stores currently active participants in another database.  When a caller (in this case an EMT) calls into connect to the operator, the function looks for operators among the currently active participants and then dials from the EMT's conference to the operator's conference via the Pexip Infinity management API.
