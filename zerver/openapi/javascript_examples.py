
from typing import Dict, Any, Optional, Iterable, Callable, Set, List

import json
import os
import sys
import subprocess

from functools import wraps

from zerver.lib import mdiff
from zerver.openapi.openapi import validate_against_openapi_schema

from zerver.models import get_realm, get_user

from zulip import Client

ZULIP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURE_PATH = os.path.join(ZULIP_DIR, 'templates', 'zerver', 'api', 'fixtures.json')

TEST_FUNCTIONS = dict()  # type: Dict[str, Callable[..., None]]
REGISTERED_TEST_FUNCTIONS = set()  # type: Set[str]
CALLED_TEST_FUNCTIONS = set()  # type: Set[str]

def openapi_test_function(endpoint: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """This decorator is used to register an openapi test function with
    its endpoint. Example usage:

    @openapi_test_function("/messages/render:post")
    def ...
    """
    def wrapper(test_func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(test_func)
        def _record_calls_wrapper(*args: Any, **kwargs: Any) -> Any:
            CALLED_TEST_FUNCTIONS.add(test_func.__name__)
            return test_func(*args, **kwargs)

        REGISTERED_TEST_FUNCTIONS.add(test_func.__name__)
        TEST_FUNCTIONS[endpoint] = _record_calls_wrapper

        return _record_calls_wrapper
    return wrapper

def ensure_users(ids_list: List[int], user_names: List[str]) -> None:
    # Ensure that the list of user ids (ids_list)
    # matches the users we want to refer to (user_names).
    realm = get_realm("zulip")
    user_ids = [get_user(name + '@zulip.com', realm).id for name in user_names]

    assert ids_list == user_ids

def load_api_fixtures():
    # type: () -> Dict[str, Any]
    with open(FIXTURE_PATH, 'r') as fp:
        json_dict = json.load(fp)
        return json_dict

FIXTURES = load_api_fixtures()

'''
# SETUP METHODS FOLLOW
def test_against_fixture(result, fixture, check_if_equal=[], check_if_exists=[]):
    # type: (Dict[str, Any], Dict[str, Any], Optional[Iterable[str]], Optional[Iterable[str]]) -> None
    assertLength(result, fixture)

    if not check_if_equal and not check_if_exists:
        for key, value in fixture.items():
            assertEqual(key, result, fixture)

    if check_if_equal:
        for key in check_if_equal:
            assertEqual(key, result, fixture)

    if check_if_exists:
        for key in check_if_exists:
            assertIn(key, result)

def assertEqual(key, result, fixture):
    # type: (str, Dict[str, Any], Dict[str, Any]) -> None
    if result[key] != fixture[key]:
        first = "{key} = {value}".format(key=key, value=result[key])
        second = "{key} = {value}".format(key=key, value=fixture[key])
        raise AssertionError("Actual and expected outputs do not match; showing diff:\n" +
                             mdiff.diff_strings(first, second))
    else:
        assert result[key] == fixture[key]

def assertLength(result, fixture):
    # type: (Dict[str, Any], Dict[str, Any]) -> None
    if len(result) != len(fixture):
        result_string = json.dumps(result, indent=4, sort_keys=True)
        fixture_string = json.dumps(fixture, indent=4, sort_keys=True)
        raise AssertionError("The lengths of the actual and expected outputs do not match; showing diff:\n" +
                             mdiff.diff_strings(result_string, fixture_string))
    else:
        assert len(result) == len(fixture)

def assertIn(key, result):
    # type: (str, Dict[str, Any]) -> None
    if key not in result.keys():
        raise AssertionError(
            "The actual output does not contain the the key `{key}`.".format(key=key)
        )
    else:
        assert key in result

def test_messages(client, nonadmin_client):
    # type: (Client, Client) -> None

    render_message(client)
    message_id = send_message(client)
    add_reaction(client, message_id)
    remove_reaction(client, message_id)
    update_message(client, message_id)
    get_raw_message(client, message_id)
    get_messages(client)
    get_message_history(client, message_id)
    delete_message(client, message_id)
    mark_all_as_read(client)
    mark_stream_as_read(client)
    mark_topic_as_read(client)
    update_message_flags(client)

    test_nonexistent_stream_error(client)
    test_private_message_invalid_recipient(client)
    test_update_message_edit_permission_error(client, nonadmin_client)
    test_delete_message_edit_permission_error(client, nonadmin_client)

def test_users(client):
    # type: (Client) -> None

    create_user(client)
    get_members(client)
    get_single_user(client)
    deactivate_user(client)
    update_user(client)
    get_profile(client)
    update_notification_settings(client)
    upload_file(client)
    remove_attachment(client)
    set_typing_status(client)
    get_user_presence(client)
    update_presence(client)
    create_user_group(client)
    group_id = get_user_groups(client)
    update_user_group(client, group_id)
    update_user_group_members(client, group_id)
    remove_user_group(client, group_id)
    get_alert_words(client)
    add_alert_words(client)
    remove_alert_words(client)

def test_streams(client, nonadmin_client):
    # type: (Client, Client) -> None

    add_subscriptions(client)
    test_add_subscriptions_already_subscribed(client)
    list_subscriptions(client)
    stream_id = get_stream_id(client)
    update_stream(client, stream_id)
    get_streams(client)
    get_subscribers(client)
    remove_subscriptions(client)
    toggle_mute_topic(client)
    update_subscription_settings(client)
    update_notification_settings(client)
    get_stream_topics(client, 1)
    delete_stream(client, stream_id)

    test_user_not_authorized_error(nonadmin_client)
    test_authorization_errors_fatal(client, nonadmin_client)


def test_queues(client):
    # type: (Client) -> None
    # Note that the example for api/get-events-from-queue is not tested.
    # Since, methods such as client.get_events() or client.call_on_each_message
    # are blocking calls and since the event queue backend is already
    # thoroughly tested in zerver/tests/test_event_queue.py, it is not worth
    # the effort to come up with asynchronous logic for testing those here.
    queue_id = register_queue(client)
    deregister_queue(client, queue_id)

def test_server_organizations(client):
    # type: (Client) -> None

    get_realm_filters(client)
    add_realm_filter(client)
    get_server_settings(client)
    remove_realm_filter(client)
    get_realm_emoji(client)
    upload_custom_emoji(client)

def test_errors(client):
    # type: (Client) -> None
    test_missing_request_argument(client)
    test_invalid_stream_error(client)

def test_the_api(client, nonadmin_client):
    # type: (Client, Client) -> None

    get_user_agent(client)
    test_users(client)
    test_streams(client, nonadmin_client)
    test_messages(client, nonadmin_client)
    test_queues(client)
    test_server_organizations(client)
    test_errors(client)

    sys.stdout.flush()
    if REGISTERED_TEST_FUNCTIONS != CALLED_TEST_FUNCTIONS:
        print("Error!  Some @openapi_test_function tests were never called:")
        print("  ", REGISTERED_TEST_FUNCTIONS - CALLED_TEST_FUNCTIONS)
        sys.exit(1)
'''


@openapi_test_function("/messages:post")
def send_message(key):
    print("2")
    print(key)
    js_code = """
const zulip = require('zulip-js');

// Pass the path to your zuliprc file here.
const config = {
    zuliprc: './zerver/openapi/.zuliprc',
};

// Send a stream message
zulip(config).then((client) => {
    // Send a message
    const params = {
        to: 'Denmark',
        type: 'stream',
        subject: 'Castle',
        content: 'I come not, friends, to steal away your hearts.'
    }

    client.messages.send(params).then(console.log);
});
/*
// Send a private message
zulip(config).then((client) => {
    // Send a private message
    const user_id = 9;
    const params = {
        to: [user_id],
        type: 'private',
        content: 'With mirth and laughter let old wrinkles come.',
    }

    client.messages.send(params).then(console.log);
});*/
"""
    print("3")
    #a=subprocess.check_output(["node","\nconsole.log('fdf')"],universal_newlines=True)
    
    a=subprocess.check_output(['node'],input=bytes(js_code,encoding='utf-8')).decode('utf-8')
    #a=subprocess.check_output(js_code)
    print(json.loads(a))
    """
    with subprocess.Popen('node',stdin=subprocess.PIPE,universal_newlines=True) as process:
        out, err = process.communicate(js_code)
    """

    '''

    subprocess.check_output()
    subprocess.check_output('console.log', stdout=a, stderr=subprocess.PIPE, shell=True)
    
    print(a)
    '''
    #a=subprocess.check_output("console.log('ddd')")
    #subprocess.check_output("console.log('fd')")
    # + js_code.splitlines(),shell=True).decode('utf-8')

    #print(response_json)
    '''
    for x in response_json:
        validate_against_openapi_schema(x, '/messages', 'post', '200')

'''
def test_js_bindings(client):
    # type: (Client) -> None

    zuliprc = open("./zerver/openapi/.zuliprc","w")
    zuliprc.writelines(["[api]\n",
                        "email=" + client.email + "\n",
                        "key=" + client.api_key + "\n"
                        "site=" + client.base_url[:-5],
                       ])
    print(zuliprc)
    zuliprc.close()

    print("1")
    print(client.api_key)
    send_message(client.api_key)

