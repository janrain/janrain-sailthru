"""Sync action."""
from flask import current_app as app
from flask import request
from sailthru import SailthruClient
import janrain_datalib

def sync():
    """Sync records.
    Returns status 200 to prevent webhook from retrying.
    Returns any other status if webhook should retry.
    """
    webhook_payload = request.json
    if not webhook_payload:
        app.logger.warning("aborting: no webhook payload data in request")
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
        app.logger.warning("aborting: no attributes specified in config")
        return 'no attributes'
    app.logger.debug("attributes: {}".format(app.config['JANRAIN_ATTRIBUTES']))

    # convert attributes from string to list
    attributes = [x.strip() for x in app.config['JANRAIN_ATTRIBUTES'].split(',')]
    # uuid and email will be handled separately as keys
    if 'email' in attributes:
        attributes.remove('email')
    if 'uuid' in attributes:
        attributes.remove('uuid')

    # replace dots with underscores (sailthru strips out dots)
    sailthru_fields = [x.replace('.', '_') for x in attributes]

    for item in webhook_payload:
        uuid = item['uuid']

        app.logger.info("{}: retrieving record from capture".format(uuid))
        record = capture_schema.records.get_record(uuid)
        try:
            # include email
            record = record.as_dict(attributes + ['email'])
        except janrain_datalib.exceptions.ApiError as err:
            app.logger.error("{}: capture: {}".format(uuid, str(err)))
            return 'fail (capture)'

        # get values from the capture record as a flattened list
        values = [dot_lookup(record, x) for x in attributes]
        # map sailthru attribute names to values
        sailthru_vars = dict(zip(sailthru_fields, values))

        app.logger.info("{}: retrieving record from sailthru with matching email".format(uuid))
        # lookup record in sailthru via email
        sailthru_payload = {
            'id': record['email'],
            'key': 'email',
        }
        response = sailthru_client.api_get('user', sailthru_payload)

        # matching email found in sailthru
        if response.is_ok():
            app.logger.debug("{}: email match found in sailthru".format(uuid))

            # upsert using email (also set extid)
            sailthru_payload = {
                'id': record['email'],
                'key': 'email',
                'keys': {
                    'extid': uuid
                },
                'vars': sailthru_vars,
            }

        else:
            r_err = response.get_error()

            # a problem happened with the sailthru client
            if r_err.get_error_code() != 99:
                app.logger.error("{}: sailthru: {}".format(uuid, r_err))
                return 'fail (sailthru)'

            # email not found in sailthru
            app.logger.debug("{}: no matching email found in sailthru".format(uuid))
            # upsert using extid (also set email)
            sailthru_payload = {
                'id': uuid,
                'key': 'extid',
                'keys': {
                    'email': record['email']
                },
                'vars': sailthru_vars,
            }

        app.logger.info("{}: sending record to sailthru".format(uuid))
        response = sailthru_client.api_post('user', sailthru_payload)
        if not response.is_ok():
            app.logger.error("{}: sailthru error: {}".format(uuid, response.get_error()))
            return 'fail (sailthru)'

    return 'done'

def dot_lookup(data, path):
    """Lookup a value from a multilevel dict given a dot-separated path string."""
    for key in path.split('.'):
        data = data[key]
    return data
