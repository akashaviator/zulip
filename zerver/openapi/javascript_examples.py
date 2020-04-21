
from typing import Dict, Any, Callable, Set, List

import json
import os
import sys
import subprocess

from functools import wraps

from zerver.openapi.openapi import validate_against_openapi_schema

from zulip import Client

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

def run_js_code(js_code: str) -> List[Dict[str, Any]]:

    def get_json_data(response_list: List[str]) -> List[Dict[str, Any]]:

        js_code = """
var json_data = {response_list};
json_data.forEach(
    (data) => console.log(JSON.stringify(eval("(" + data + ")")))
);
""".format(response_list=response_list)
        output = subprocess.check_output(['node'],
                                         input=js_code,
                                         universal_newlines=True)

        responses = [json.loads(response) for response in output.splitlines()]

        return responses

    output = subprocess.check_output(['node'], input=js_code, universal_newlines=True)
    responses = get_json_data(output.splitlines())

    return responses

@openapi_test_function("/messages:post")
def send_message(key) -> None:

    js_code = """
const zulip = require('zulip-js');

// Pass the path to your zuliprc file here.
const config = {
    zuliprc: './zerver/openapi/.zuliprc',
};
// {code_example|start}
/* Send a stream message */
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
// {code_example|end}

// {code_example|start}
/* Send a private message*/
zulip(config).then((client) => {
    // Send a private message
    const user_id = 9;
    const params = {
        to: [user_id],
        type: 'private',
        content: 'With mirth and laughter let old wrinkles come.',
    }

    client.messages.send(params).then(console.log);
});
// {code_example|end}
"""
    result_list = run_js_code(js_code)

    for result in result_list:
        validate_against_openapi_schema(result, '/messages', 'post', '200')


def test_messages(client: Client) -> None:
    send_message(client)

def test_js_bindings(client: Client) -> None:

    zuliprc = open("./zerver/openapi/.zuliprc", "w")
    zuliprc.writelines(
        ["[api]\n",
         "email=" + client.email + "\n",
         "key=" + client.api_key + "\n",
         "site=" + client.base_url[:-5]]
    )

    zuliprc.close()

    try:
        test_messages(client)
    finally:
        os.remove("./zerver/openapi/.zuliprc")

    sys.stdout.flush()
    if REGISTERED_TEST_FUNCTIONS != CALLED_TEST_FUNCTIONS:
        print("Error!  Some @openapi_test_function tests were never called:")
        print("  ", REGISTERED_TEST_FUNCTIONS - CALLED_TEST_FUNCTIONS)
        sys.exit(1)
