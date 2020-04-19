
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

def test_messages(client):
    # type: (Client) -> None

    send_message(client)

def test_js_bindings(client):
    # type: (Client) -> None

    zuliprc = open("./zerver/openapi/.zuliprc","w")
    zuliprc.writelines(["[api]\n",
                        "email=" + client.email + "\n",
                        "key=" + client.api_key + "\n"
                        "site=" + client.base_url[:-5],
                       ])

    zuliprc.close()

    test_messages(client)
    os.remove("./zerver/openapi/.zuliprc")

    sys.stdout.flush()
    if REGISTERED_TEST_FUNCTIONS != CALLED_TEST_FUNCTIONS:
        print("Error!  Some @openapi_test_function tests were never called:")
        print("  ", REGISTERED_TEST_FUNCTIONS - CALLED_TEST_FUNCTIONS)
        sys.exit(1)


@openapi_test_function("/messages:post")
def send_message(key):

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

    client.messages.send(params).then((res)=>{res=JSON.stringify(res);console.log(res)});
});

// Send a private message
zulip(config).then((client) => {
    // Send a private message
    const user_id = 9;
    const params = {
        to: [user_id],
        type: 'private',
        content: 'With mirth and laughter let old wrinkles come.',
    }

    client.messages.send(params).then((res)=>{res=JSON.stringify(res);console.log(res)});
});
"""
   
    e=subprocess.check_output(['node'],input=js_code,universal_newlines=True)
    e=e.split('\n')
    z=[]
    for i in range(len(e)-1):
        z.append(json.loads(e[i]))
    print(z)
    for a in z:
        validate_against_openapi_schema(a, '/messages', 'post', '200')



