"""Sync action."""
from flask import current_app as app
from flask import request
from sailthru.sailthru_client import SailthruClient
import janrain_datalib

def sync():
    """Sync records.
    Returns status 200 to prevent webhook from retrying.
    Returns any other status if webhook should retry.
    """
    webhook_payload = request.json
    if not webhook_payload:
        app.logger.warning("no webhook payload data detected in request: aborting")
        return 'no webhook payload'
    app.logger.debug("webhook payload: {}".format(webhook_payload))

    capture_app = janrain_datalib.get_app(
        app.config['JANRAIN_URI'],
        app.config['JANRAIN_CLIENT_ID'],
        app.config['JANRAIN_CLIENT_SECRET'])
    capture_schema = capture_app.get_schema(app.config['JANRAIN_SCHEMA_NAME'])

    sailthru_client = SailthruClient(
        app.config['SAILTHRU_API_KEY'],
        app.config['SAILTHRU_API_SECRET'])

    if not app.config['JANRAIN_ATTRIBUTES']:
        app.logger.warning("no attributes specified in config: aborting")
        return 'no attributes'

    attributes = [x.strip() for x in app.config['JANRAIN_ATTRIBUTES'].split(',')]
    # these attributes will be handled separately
    if 'email' in attributes:
        attributes.remove('email')
    if 'uuid' in attributes:
        attributes.remove('uuid')

    # replace dots with underscores (sailthru will strip dots from field names)
    sailthru_attributes = [x.replace('.', '_') for x in attributes]
    if not app.config['SAILTHRU_LISTS']:
        sailthru_lists = {}
    else:
        sailthru_lists = [x.strip() for x in app.config['SAILTHRU_LISTS'].split(',')]
    # map list name to 1 for add or 0 for remove
    lists_dict = dict(zip(sailthru_lists, [1 for _ in range(len(sailthru_lists))]))

    for item in webhook_payload:
        uuid = item['uuid']
        # always include uuid and email in capture record
        record = capture_schema.records.get_record(uuid)
        record_attributes = attributes + ['uuid', 'email']

        app.logger.info("retrieving record from capture: {}".format(uuid))
        try:
            record = record.as_dict(record_attributes)
        except janrain_datalib.exceptions.ApiError as err:
            app.logger.debug("capture error: {}".format(str(err)))
            app.logger.error("capture error: failed to fetch record")
            return 'fail (capture)'

        # get values from the capture record
        values = [dot_lookup(record, x) for x in attributes]
        # map new attribute names to values
        attributes_dict = dict(zip(sailthru_attributes, values))

        sailthru_payload = {
            'id': record['uuid'],
            'key': 'extid',
            'keys': {
                'email': record['email'],
            },
            'keysconflict': 'merge',
            'vars': attributes_dict,
            'lists': lists_dict,
        }

        app.logger.info("sending record to sailthru: {}".format(record['uuid']))
        # creates or updates a user (upsert)
        response = sailthru_client.api_post('user', sailthru_payload)
        if response.is_ok():
            app.logger.debug("sailthru success: {}".format(response.get_body()))
        else:
            app.logger.debug("sailthru error: {}".format(response.get_error()))
            app.logger.error("sailthru error: unable to sync record")
            return 'fail (sailthru)'

    return 'done'

def dot_lookup(data, path):
    """Lookup a value from a multilevel dict given a dot-separated path string."""
    for key in path.split('.'):
        data = data[key]
    return data
