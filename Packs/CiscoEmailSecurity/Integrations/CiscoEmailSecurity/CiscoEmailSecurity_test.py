import json
import pytest
from CiscoEmailSecurity import Client


def get_fetch_data():
    with open('./test_data.json', 'r') as f:
        return json.loads(f.read())


test_data = get_fetch_data()


def test_date_to_cisco_date():
    from CiscoEmailSecurity import date_to_cisco_date
    res = date_to_cisco_date('2019-11-20 09:36:09')
    assert res == '2019-11-20T09:36:09.000Z'


@pytest.mark.parametrize(
    "limit, expected",
    [
        ('', 50),
        ('100', 50),
        ('20', 20)
    ]
)
def test_set_limit(limit, expected):
    from CiscoEmailSecurity import set_limit
    res = set_limit(limit)
    assert res == expected


def test_build_url_params_for_list_report():
    from CiscoEmailSecurity import build_url_params_for_list_report
    res = build_url_params_for_list_report(test_data['args_for_list_report'])
    assert res == test_data['url_params_for_list_reports']


def test_build_url_params_for_list_messages():
    from CiscoEmailSecurity import build_url_params_for_list_messages
    res = build_url_params_for_list_messages(test_data['args_for_list_messages'])
    assert res == test_data['url_params_for_list_messages']


def test_build_url_params_for_get_details():
    from CiscoEmailSecurity import build_url_params_for_get_details
    res = build_url_params_for_get_details(test_data['args_for_get_details'], '/sma/api/v2.0/quarantine/messages')
    assert res == test_data['url_params_for_get_details']


def test_build_url_params_for_spam_quarantine():
    from CiscoEmailSecurity import build_url_params_for_spam_quarantine
    res = build_url_params_for_spam_quarantine(test_data['args_for_spam_quarantine'])
    assert res == test_data['url_params_for_spam_quarantine']


def test_list_search_messages_command(requests_mock):
    from CiscoEmailSecurity import list_search_messages_command
    requests_mock.get("https://ciscoemailsecurity/sma/api/v2.0/message-tracking/messages?"
                      "startDate=2017-02-14T09:51:46.000-0600.000Z&endDate=2017-02-14T09:51:46.000-0600.000Z"
                      "&searchOption=messages&offset=0&limit=50",
                      json=test_data['search_messages_response_data'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_search_messages_command(client, {"start_date": "2017-02-14T09:51:46.000-0600",
                                                "end_date": "2017-02-14T09:51:46.000-0600"})
    assert res.outputs == test_data['search_messages_context']
    assert res.outputs_prefix == 'CiscoEmailSecurity.Messages'
    assert res.outputs_key_field == 'attributes.mid'


def test_messages_to_human_readable():
    from CiscoEmailSecurity import messages_to_human_readable
    res = messages_to_human_readable(test_data['search_messages_context'])
    assert res == test_data['messages_human_readable']


def test_list_get_message_details_command(requests_mock):
    from CiscoEmailSecurity import list_get_message_details_command
    requests_mock.get("https://ciscoemailsecurity/sma/api/v2.0/message-tracking/details?"
                      "startDate=2017-02-14T09:51:46.000-0600.000Z&endDate=2017-02-14T09:51:46.000-0600.000Z&"
                      "mid=None&icid=None",
                      json=test_data['get_message_details_response_data'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_get_message_details_command(client, {"start_date": "2017-02-14T09:51:46.000-0600",
                                                    "end_date": "2017-02-14T09:51:46.000-0600"})
    assert res.outputs == test_data['get_message_details_context']
    assert res.outputs_prefix == 'CiscoEmailSecurity.Message'
    assert res.outputs_key_field == 'messages.mid'


def test_message_to_human_readable():
    from CiscoEmailSecurity import details_get_to_human_readable
    res = details_get_to_human_readable(test_data['get_message_details_context'])
    assert res == test_data['message_human_readable']


def test_list_search_spam_quarantine_command(requests_mock):
    from CiscoEmailSecurity import list_search_spam_quarantine_command
    requests_mock.get("https://ciscoemailsecurity/sma/api/v2.0/quarantine/messages"
                      "?startDate=2017-02-14T09:51:46.000-0600.000Z&endDate=2017-02-14T09:51:46.000-0600.000Z"
                      "&quarantineType=spam&offset=0&limit=50", json=test_data['search_spam_quarantine_response_data'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_search_spam_quarantine_command(client, {"start_date": "2017-02-14T09:51:46.000-0600",
                                                       "end_date": "2017-02-14T09:51:46.000-0600"})
    assert res.outputs == test_data['search_spam_quarantine_context']
    assert res.outputs_prefix == 'CiscoEmailSecurity.SpamQuarantine'
    assert res.outputs_key_field == 'mid'


def test_spam_quarantine_to_human_readable():
    from CiscoEmailSecurity import spam_quarantine_to_human_readable
    res = spam_quarantine_to_human_readable(test_data['search_spam_quarantine_context'])
    assert res == test_data['spam_quarantine_human_readable']


def test_list_get_quarantine_message_details_command(requests_mock):
    from CiscoEmailSecurity import list_get_quarantine_message_details_command
    requests_mock.get("https://ciscoemailsecurity/sma/api/v2.0/quarantine/messages?mid=None&quarantineType=spam",
                      json=test_data['quarantine_message_details_response_data'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_get_quarantine_message_details_command(client, {"start_date": "2017-02-14T09:51:46.000-0600",
                                                               "end_date": "2017-02-14T09:51:46.000-0600"})
    assert res.outputs == test_data['quarantine_message_details_context']
    assert res.outputs_prefix == 'CiscoEmailSecurity.QuarantineMessageDetails'
    assert res.outputs_key_field == 'mid'


def test_quarantine_message_details_data_to_human_readable():
    from CiscoEmailSecurity import quarantine_message_details_data_to_human_readable
    res = quarantine_message_details_data_to_human_readable(test_data['quarantine_message_details_context'])
    assert res == test_data['quarantine_message_details_human_readable']


def test_list_delete_quarantine_messages_command(requests_mock):
    from CiscoEmailSecurity import list_delete_quarantine_messages_command
    requests_mock.post("https://ciscoemailsecurity/sma/api/v2.0/quarantine/messages",
                       json=test_data['quarantine_delete_message_response_data'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_delete_quarantine_messages_command(client, {"messages_ids": "1234"})
    assert res.readable_output == test_data['quarantine_delete_message_response_data']
    assert res.outputs_prefix == 'CiscoEmailSecurity.QuarantineDeleteMessages'


def test_list_release_quarantine_messages_command(requests_mock):
    from CiscoEmailSecurity import list_release_quarantine_messages_command
    requests_mock.post("https://ciscoemailsecurity/sma/api/v2.0/quarantine/messages",
                       json=test_data['quarantine_release_message_response_data'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_release_quarantine_messages_command(client, {"messages_ids": "1234"})
    assert res.readable_output == test_data['quarantine_release_message_response_data']
    assert res.outputs_prefix == 'CiscoEmailSecurity.QuarantineDeleteMessages'


def test_build_url_filter_for_get_list_entries():
    from CiscoEmailSecurity import build_url_filter_for_get_list_entries
    res = build_url_filter_for_get_list_entries({"list_type": "safelist", "view_by": "bla"})
    assert res == "/sma/api/v2.0/quarantine/safelist?action=view&limit=50&offset=0&quarantineType=spam&viewBy=bla"


def test_list_entries_get_command(requests_mock):
    from CiscoEmailSecurity import list_entries_get_command
    requests_mock.get("https://ciscoemailsecurity/sma/api/v2.0/quarantine/safelist",
                      json=test_data['get_list_entries_response'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_entries_get_command(client, {"list_type": "safelist", "limit": "25", "order_by": "recipient",
                                            "view_by": "recipient"})
    assert res.outputs == test_data['get_list_entries_context']
    assert res.outputs_prefix == 'CiscoEmailSecurity.ListEntriesGet'


def test_build_url_and_request_body_for_add_list_entries():
    from CiscoEmailSecurity import build_url_and_request_body_for_add_list_entries
    res_url, res_request_body = build_url_and_request_body_for_add_list_entries({"list_type": "safelist",
                                                                                 "action": "add", "recipient_addresses":
                                                                                ["user1@acme.com", "user2@acme.com"],
                                                                                "sender_list": ["acme.com"],
                                                                                 "view_by": "recipient"})
    assert res_url == "/sma/api/v2.0/quarantine/safelist"
    assert res_request_body == {"action": "add", "quarantineType": "spam", "viewBy": "recipient",
                                "recipientAddresses": ["user1@acme.com", "user2@acme.com"], "senderList": ["acme.com"]}


def test_list_entries_add_command(requests_mock):
    from CiscoEmailSecurity import list_entries_add_command
    requests_mock.post("https://ciscoemailsecurity/sma/api/v2.0/quarantine/safelist",
                       json=test_data['add_list_entries_response'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_entries_add_command(client, {"list_type": "safelist", "action": "add", "limit": "25",
                                            "recipient_addresses": ["user1@acme.com", "user2@acme.com"],
                                            "sender_list": ["acme.com"], "view_by": "recipient"})
    assert res.outputs == test_data['add_list_entries_context']
    assert res.outputs_prefix == 'CiscoEmailSecurity.listEntriesAdd'


def test_build_url_and_request_body_for_delete_list_entries():
    from CiscoEmailSecurity import build_url_and_request_body_for_delete_list_entries
    res_url, res_request_body = build_url_and_request_body_for_delete_list_entries({"list_type": "safelist",
                                                                                    "sender_list": ["acme.com"],
                                                                                    "view_by": "recipient"})
    assert res_url == "/sma/api/v2.0/quarantine/safelist"
    assert res_request_body == {"quarantineType": "spam", "viewBy": "recipient", "senderList": ["acme.com"]}


def test_list_entries_delete_command(requests_mock):
    from CiscoEmailSecurity import list_entries_delete_command
    requests_mock.post("https://ciscoemailsecurity/sma/api/v2.0/quarantine/safelist",
                       json=test_data['delete_list_entries_response'])

    client = Client({"client_id": "a", "client_secret": "b", "base_url": "https://ciscoemailsecurity/",
                     "insecure": False, "proxy": False})
    res = list_entries_delete_command(client, {"list_type": "safelist", "sender_list": ["acme.com"],
                                               "view_by": "recipient"})
    assert res.outputs == test_data['delete_list_entries_context']
    assert res.outputs_prefix == 'CiscoEmailSecurity.listEntriesDelete'
