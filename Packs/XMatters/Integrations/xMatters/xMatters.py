import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *
import requests
import json
import dateparser
import traceback
from typing import Any, Dict, Tuple, List, Optional, cast

''' CONSTANTS '''
DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()

''' CLIENT CLASS '''


class Client(BaseClient):
    """Client class to interact with the service API

    This Client implements API calls, and does not contain any Demisto logic.
    Should only do requests and return data.
    It inherits from BaseClient defined in CommonServer Python.
    Most calls use _http_request() that handles proxy, SSL verification, etc.
    """

    def xm_trigger_workflow(self, recipients: Optional[str] = None,
                            subject: Optional[str] = None, body: Optional[str] = None,
                            incident_id: Optional[str] = None,
                            close_task_id: Optional[str] = None) -> Dict[str, Any]:
        """Triggers a workflow in xMatters.

        :type recipients: ``Optional[str]``
        :param recipients: recipients for the xMatters alert.

        :type subject: ``Optional[str]``
        :param subject: Subject for the message in xMatters.

        :type body: ``Optional[str]``
        :param body: Body for the message in xMatters.

        :type incident_id: ``Optional[str]``
        :param incident_id: ID of incident that the message is related to.

        :type close_task_id: ``Optional[str]``
        :param close_task_id: Task ID from playbook to close.

        :return: result of the http request
        :rtype: ``Dict[str, Any]``
        """

        request_params: Dict[str, Any] = {
        }

        if (recipients):
            request_params['recipients'] = recipients

        if (subject):
            request_params['subject'] = subject

        if (body):
            request_params['body'] = body

        if (incident_id):
            request_params['incident_id'] = incident_id

        if (close_task_id):
            request_params['close_task_id'] = close_task_id

        res = self._http_request(
            method='POST',
            url_suffix='',
            params=request_params,
        )

        return res

    def search_alerts(self, alert_status: Optional[str] = None, priority: Optional[str] = None,
                      start_time: Optional[int] = None, property_name: Optional[str] = None,
                      property_value: Optional[str] = None, request_id: Optional[str] = None,
                      from_time: Optional[str] = None, to_time: Optional[str] = None,
                      workflow: Optional[str] = None, form: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches for xMatters alerts using the '/events' API endpoint

        All the parameters are passed directly to the API as HTTP POST parameters in the request

        :type alert_status: ``Optional[str]``
        :param alert_status: status of the alert to search for. Options are: 'ACTIVE' or 'SUSPENDED'

        :type priority: ``Optional[str]``
        :param priority:
            severity of the alert to search for. Comma-separated values.
            Options are: "LOW", "MEDIUM", "HIGH"

        :type start_time: ``Optional[int]``
        :param start_time: start timestamp (epoch in seconds) for the alert search

        :type property_name: ``Optional[str]``
        :param property_name: Name of property to match when searching for alerts.

        :type property_value: ``Optional[str]``
        :param property_value: Value of property to match when searching for alerts.

        :type request_id: ``Optional[str]``
        :param request_id: Matches requestId in xMatters.

        :type from_time: ``Optional[str]``
        :param from_time: UTC time of the beginning time to search for events.

        :type to_time: ``Optional[str]``
        :param to_time: UTC time of the end time to search for events.

        :type workflow: ``Optional[str]``
        :param workflow: Workflow that events are from in xMatters.

        :type form: ``Optional[str]``
        :param form: Form that events are from in xMatters.

        :return: list containing the found xMatters events as dicts
        :rtype: ``List[Dict[str, Any]]``
        """

        request_params: Dict[str, Any] = {}

        if alert_status:
            request_params['status'] = alert_status

        if priority:
            request_params['priority'] = priority

        if from_time:
            request_params['from'] = from_time
        elif start_time:
            request_params['from'] = start_time

        if to_time:
            request_params['to'] = to_time

        if property_value and property_name:
            request_params['propertyName'] = property_name
            request_params['propertyValue'] = property_value

        if request_id:
            request_params['requestId'] = request_id

        if workflow:
            request_params['plan'] = workflow

        if form:
            request_params['form'] = form

        res = self._http_request(
            method='GET',
            url_suffix='/api/xm/1/events',
            params=request_params
        )

        data = res['data']

        has_next = True

        while has_next:
            if 'links' in res and 'next' in res['links']:
                res = self._http_request(
                    method='GET',
                    url_suffix=res['links']['next']
                )

                for val in res['data']:
                    data.append(val)
            else:
                has_next = False

        return data

    def search_alert(self, event_id: str):
        res = self._http_request(
            method='GET',
            url_suffix='/api/xm/1/events/' + event_id
        )

        return res


''' HELPER FUNCTIONS '''


def convert_to_demisto_severity(severity: str) -> int:
    """Maps xMatters severity to Cortex XSOAR severity

    Converts the xMatters alert severity level ('Low', 'Medium',
    'High') to Cortex XSOAR incident severity (1 to 4)
    for mapping.

    :type severity: ``str``
    :param severity: severity as returned from the HelloWorld API (str)

    :return: Cortex XSOAR Severity (1 to 4)
    :rtype: ``int``
    """

    # In this case the mapping is straightforward, but more complex mappings
    # might be required in your integration, so a dedicated function is
    # recommended. This mapping should also be documented.
    return {
        'low': 1,  # low severity
        'medium': 2,  # medium severity
        'high': 3,  # high severity
    }[severity.lower()]


def arg_to_timestamp(arg: Any, arg_name: str, required: bool = False) -> Optional[int]:
    """Converts an XSOAR argument to a timestamp (seconds from epoch)

    This function is used to quickly validate an argument provided to XSOAR
    via ``demisto.args()`` into an ``int`` containing a timestamp (seconds
    since epoch). It will throw a ValueError if the input is invalid.
    If the input is None, it will throw a ValueError if required is ``True``,
    or ``None`` if required is ``False.

    :type arg: ``Any``
    :param arg: argument to convert

    :type arg_name: ``str``
    :param arg_name: argument name

    :type required: ``bool``
    :param required:
        throws exception if ``True`` and argument provided is None

    :return:
        returns an ``int`` containing a timestamp (seconds from epoch) if conversion works
        returns ``None`` if arg is ``None`` and required is set to ``False``
        otherwise throws an Exception
    :rtype: ``Optional[int]``
    """

    if arg is None:
        if required is True:
            raise ValueError(f'Missing "{arg_name}"')
        return None

    if isinstance(arg, str) and arg.isdigit():
        # timestamp is a str containing digits - we just convert it to int
        return int(arg)
    if isinstance(arg, str):
        # we use dateparser to handle strings either in ISO8601 format, or
        # relative time stamps.
        # For example: format 2019-10-23T00:00:00 or "3 days", etc
        date = dateparser.parse(arg, settings={'TIMEZONE': 'UTC'})
        if date is None:
            # if d is None it means dateparser failed to parse it
            raise ValueError(f'Invalid date: {arg_name}')

        return int(date.timestamp())
    if isinstance(arg, (int, float)):
        # Convert to int if the input is a float
        return int(arg)
    raise ValueError(f'Invalid date: "{arg_name}"')


''' COMMAND FUNCTIONS '''


def fetch_incidents(client: Client, last_run: Dict[str, int],
                    first_fetch_time: Optional[int], alert_status: Optional[str],
                    priority: Optional[str], property_name: Optional[str], property_value: Optional[str]
                    ) -> Tuple[Dict[str, int], List[dict]]:
    """This function retrieves new alerts every interval (default is 1 minute).

    This function has to implement the logic of making sure that incidents are
    fetched only onces and no incidents are missed. By default it's invoked by
    XSOAR every minute. It will use last_run to save the timestamp of the last
    incident it processed. If last_run is not provided, it should use the
    integration parameter first_fetch_time to determine when to start fetching
    the first time.

    :type client: ``Client``
    :param Client: xMatters client to use

    :type last_run: ``Optional[Dict[str, int]]``
    :param last_run:
        A dict with a key containing the latest incident created time we got
        from last fetch

    :type first_fetch_time: ``Optional[int]``
    :param first_fetch_time:
        If last_run is None (first time we are fetching), it contains
        the timestamp in milliseconds on when to start fetching incidents

    :type alert_status: ``Optional[str]``
    :param alert_status:
        status of the alert to search for. Options are: 'ACTIVE',
        'SUSPENDED', or 'TERMINATED'

    :type priority: ``str``
    :param priority:
        Comma-separated list of the priority to search for.
        Options are: "LOW", "MEDIUM", "HIGH"

    :type property_name: ``Optional[str]``
    :param property_name: Property name to match with events.

    :type property_value: ``Optional[str]``
    :param property_value: Property value to match with events.

    :return:
        A tuple containing two elements:
            next_run (``Dict[str, int]``): Contains the timestamp that will be
                    used in ``last_run`` on the next fetch.
            incidents (``List[dict]``): List of incidents that will be created in XSOAR

    :rtype: ``Tuple[Dict[str, int], List[dict]]``
    """

    # Get the last fetch time, if exists
    # last_run is a dict with a single key, called last_fetch
    last_fetch = last_run.get('last_fetch', None)
    # Handle first fetch time
    if last_fetch is None:
        # if missing, use what provided via first_fetch_time
        last_fetch = first_fetch_time
    else:
        # otherwise use the stored last fetch
        last_fetch = int(last_fetch)

    # for type checking, making sure that latest_created_time is int
    latest_created_time = cast(int, last_fetch)

    # Initialize an empty list of incidents to return
    # Each incident is a dict with a string as a key
    incidents: List[Dict[str, Any]] = []

    if last_fetch is not None:
        start_time = timestamp_to_datestring(last_fetch * 1000)
    else:
        start_time = None

    demisto.info("This is the current timestamp: " + str(start_time))
    demisto.info("MS - last_fetch: " + str(last_fetch))

    alerts = client.search_alerts(
        alert_status=alert_status,
        start_time=start_time,
        priority=priority,
        property_name=property_name,
        property_value=property_value
    )

    for alert in alerts:
        try:
            # If no created_time set is as epoch (0). We use time in ms so we must
            # convert it from the HelloWorld API response
            incident_created_time = alert.get('created')

            # If no name is present it will throw an exception
            if ("name" in alert):
                incident_name = alert['name']
            else:
                incident_name = "No Message Subject"

            datetimeformat = '%Y-%m-%dT%H:%M:%S.000Z'

            occurred = dateparser.parse(incident_created_time).strftime(datetimeformat)

            date = dateparser.parse(occurred, settings={'TIMEZONE': 'UTC'})

            incident_created_time = int(date.timestamp())
            incident_created_time_ms = incident_created_time * 1000

            demisto.info("MS - incident_created_time: " + str(last_fetch))
            # to prevent duplicates, we are only adding incidents with creation_time > last fetched incident
            if last_fetch:
                if incident_created_time <= last_fetch:
                    continue

            details = ""

            if 'plan' in alert:
                details = details + alert['plan']['name'] + " - "

            if 'form' in alert:
                details = details + alert['form']['name']

            incident = {
                'name': incident_name,
                'details': details,
                'occurred': timestamp_to_datestring(incident_created_time_ms),
                'rawJSON': json.dumps(alert),
                'type': 'xMatters Alert',  # Map to a specific XSOAR incident Type
                'severity': convert_to_demisto_severity(alert.get('priority', 'Low')),
                # 'CustomFields': {  # Map specific XSOAR Custom Fields
                #     'helloworldid': alert.get('alert_id'),
                #     'helloworldstatus': alert.get('alert_status'),
                #     'helloworldtype': alert.get('alert_type')
                # }
            }

            incidents.append(incident)

            # Update last run and add incident if the incident is newer than last fetch
            if date.timestamp() > latest_created_time:
                latest_created_time = incident_created_time
        except Exception as e:
            demisto.info("Issue with event")
            demisto.info(str(alert))
            demisto.info(str(e))
            pass

    # Save the next_run as a dict with the last_fetch key to be stored
    next_run = {'last_fetch': latest_created_time}

    return next_run, incidents


def event_reduce(e):
    return {"Created": e.get('created'),
            "Terminated": e.get('terminated'),
            "Incident": e.get('id'),
            "Name": e.get('name'),
            "PlanName": e.get('plan').get('name'),
            "FormName": e.get('form').get('name'),
            "Status": e.get('status'),
            "Prioity": e.get('priority'),
            "Properties": e.get('properties'),
            "SubmitterName": e.get('submitter').get('targetName')}


def xm_trigger_workflow_command(client: Client, recipients: str,
                                subject: str, body: str, incident_id: str,
                                close_task_id: str) -> CommandResults:
    """
    This function runs when the xm-trigger-workflow command is run.

    :type client: ``Client``
    :param Client: xMatters client to use

    :type recipients: ``str``
    :param recipients: Recipients to alert from xMatters.

    :type subject: ``str``
    :param subject: Subject of the alert in xMatters.

    :type body: ``str``
    :param body: Body of the alert in xMatters.

    :type incident_id: ``str``
    :param incident_id: Incident ID of the event in XSOAR.

    :type close_task_id: ``str``
    :param close_task_id: ID of task to close in a playbook.

    :return: Output of xm-trigger-workflow command being run.

    :rtype: ``CommandResults``
    """
    out = client.xm_trigger_workflow(
        recipients=recipients,
        subject=subject,
        body=body,
        incident_id=incident_id,
        close_task_id=close_task_id
    )

    outputs = {}

    outputs['request_id'] = out['requestId']

    return CommandResults(
        readable_output="Successfully sent a message to xMatters.",
        outputs=outputs
    )


def xm_get_events_command(client: Client, request_id: Optional[str] = None, status: Optional[str] = None,
                          priority: Optional[str] = None, from_time: Optional[str] = None,
                          to_time: Optional[str] = None, workflow: Optional[str] = None,
                          form: Optional[str] = None, property_name: Optional[str] = None,
                          property_value: Optional[str] = None) -> CommandResults:
    """
    This function runs when the xm-get-events command is run.

    :type client: ``Client``
    :param Client: xMatters client to use

    :type status: ``Optional[str]``
    :param status:
        status of the alert to search for. Options are: 'ACTIVE',
        'SUSPENDED', or 'TERMINATED'

    :type priority: ``Optional[str]``
    :param priority:
        Comma-separated list of the priority to search for.
        Options are: "LOW", "MEDIUM", "HIGH"

    :type from_time: ``Optional[str]``
    :param from_time: UTC time for the start of the search.

    :type to_time: ``Optional[str]``
    :param to_time: UTC time for the end of the search.

    :type workflow: ``Optional[str]``
    :param workflow: Name of workflow to match the search.

    :type form: ``Optional[str]``
    :param form: Name of form to match in the search.

    :type property_name: ``Optional[str]``
    :param property_name: Property name to match with events.

    :type property_value: ``Optional[str]``
    :param property_value: Property value to match with events.

    :return: Events from the search.

    :rtype: ``CommandResults``
    """
    out = client.search_alerts(
        request_id=request_id,
        alert_status=status,
        priority=priority,
        from_time=from_time,
        to_time=to_time,
        workflow=workflow,
        form=form,
        property_name=property_name,
        property_value=property_value
    )

    reduced_out = {"Events": [event_reduce(event) for event in out]}

    return CommandResults(
        readable_output="Retrieved Events from xMatters.",
        outputs=reduced_out
    )


def xm_get_event_command(client: Client, event_id: str) -> CommandResults:
    """
    This function is run when the xm-get-event command is run.

    :type client: ``Client``
    :param Client: xMatters client to use

    :type event_id: ``str``
    :param event_id: Event ID to search for in xMatters

    :return: Output of xm-get-event command

    :rtype: ``CommandResults``
    """
    out = client.search_alert(event_id=event_id)

    reduced_out = {"Event": event_reduce(out)}

    return CommandResults(
        readable_output="Retrieved Event from xMatters.",
        outputs=reduced_out
    )


''' MAIN FUNCTION '''


def main() -> None:
    """main function, parses params and runs command functions

    :return:
    :rtype:
    """

    instance = demisto.params().get('instance')
    username = demisto.params().get('username')
    password = demisto.params().get('password')
    property_name = demisto.params().get('property_name')
    property_value = demisto.params().get('property_value')
    base_url = demisto.params().get('url')

    # if your Client class inherits from BaseClient, SSL verification is
    # handled out of the box by it, just pass ``verify_certificate`` to
    # the Client constructor
    verify_certificate = not demisto.params().get('insecure', False)

    # How much time before the first fetch to retrieve incidents
    first_fetch_time = arg_to_timestamp(
        arg=demisto.params().get('first_fetch', '3 days'),
        arg_name='First fetch time',
        required=True
    )
    # Using assert as a type guard (since first_fetch_time is always an int when required=True)
    assert isinstance(first_fetch_time, int)

    # if your Client class inherits from BaseClient, system proxy is handled
    # out of the box by it, just pass ``proxy`` to the Client constructor
    proxy = demisto.params().get('proxy', False)

    # INTEGRATION DEVELOPER TIP
    # You can use functions such as ``demisto.debug()``, ``demisto.info()``,
    # etc. to print information in the XSOAR server log. You can set the log
    # level on the server configuration
    # See: https://xsoar.pan.dev/docs/integrations/code-conventions#logging

    demisto.debug(f'Command being called is {demisto.command()}')
    try:

        to_xm_client = Client(
            base_url=base_url,
            verify=verify_certificate,
            auth=(username, password),
            proxy=proxy)

        from_xm_client = Client(
            base_url="https://" + instance,
            verify=verify_certificate,
            auth=(username, password),
            proxy=proxy)

        if demisto.command() == 'xm-trigger-workflow':
            return_results(xm_trigger_workflow_command(
                to_xm_client,
                demisto.args().get('recipients'),
                demisto.args().get('subject'),
                demisto.args().get('body'),
                demisto.args().get('incident_id'),
                demisto.args().get('close_task_id')
            ))
        elif demisto.command() == 'fetch-incidents':
            # Set and define the fetch incidents command to run after activated via integration settings.
            alert_status = demisto.params().get('status', None)
            priority = demisto.params().get('priority', None)

            next_run, incidents = fetch_incidents(
                client=from_xm_client,
                last_run=demisto.getLastRun(),  # getLastRun() gets the last run dict
                first_fetch_time=first_fetch_time,
                alert_status=alert_status,
                priority=priority,
                property_name=property_name,
                property_value=property_value
            )

            # saves next_run for the time fetch-incidents is invoked
            demisto.setLastRun(next_run)
            # fetch-incidents calls ``demisto.incidents()`` to provide the list
            # of incidents to crate
            demisto.incidents(incidents)
        elif demisto.command() == 'xm-get-events':
            return_results(xm_get_events_command(
                client=from_xm_client,
                request_id=demisto.args().get('request_id'),
                status=demisto.args().get('status'),
                priority=demisto.args().get('priority'),
                from_time=demisto.args().get('from'),
                to_time=demisto.args().get('to'),
                workflow=demisto.args().get('workflow'),
                form=demisto.args().get('form'),
                property_name=demisto.args().get('property_name'),
                property_value=demisto.args().get('property_value')
            ))
        elif demisto.command() == 'xm-get-event':
            return_results(xm_get_event_command(
                client=from_xm_client,
                event_id=demisto.args().get('event_id')
            ))

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
