# Remove an attachment

Remove an attachment uploaded by the requesting user.

`GET {{ api_url }}/v1/attachements/{attachment_id}`

## Usage examples

{start_tabs}
{tab|python}

{generate_code_example(python)|/attachements/{attachment_id}:delete|example}

{tab|curl}

{generate_code_example(curl)|/attachements/{attachment_id}:delete|example}

{end_tabs}

## Arguments

{generate_api_arguments_table|zulip.yaml|/attachements/{attachment_id}:delete}

## Response

#### Example response

A typical successful JSON response may look like:

{generate_code_example|/attachements/{attachment_id}:delete|fixture(200)}
