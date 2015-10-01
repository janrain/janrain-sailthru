Janrain to Sailthru Connector
=============================

A webhook app to send records from Janrain Capture to Sailthru.

Overview
--------

This app works in conjunction with Janrain's webhook system to propagate changes
from Capture to Sailthru. The webhook must be configured to point to the /sync
endpoint of this app. Upon receiving a POST from the webhook, the app looks up
the user record and then creates or updates a corresponding record in Sailthru.

If the email address of the record matches between Janrain and Sailthru, the
Sailthru record is updated. If a match is not found, the Sailthru record with
extid matching the Janrain UUID is updated (or created if it did not exist yet).

The Sailthru account must have the external id (extid) feature enabled. All
specified attributes from Janrain will be written as custom vars in Sailthru.


Configuration
-------------

The app reads all of its configuration from environment variables.

* `DEBUG`: If this is set to anything other than empty string or the word
FALSE, then the app runs in debug mode. Additional info is written to the log.

* `APP_LOG_FILE`: The path to the file where the app will write the log.

* `APP_LOG_FILESIZE`: The maximum size in bytes of the app log before it gets
rotated. (default: `10000000`)

* `APP_LOG_NUM_BACKUPS`: The number of rotated backups of the app log that will
be kept. (default: `20`)

* `JANRAIN_URI`: The URI of the Janrain Capture app.

* `JANRAIN_CLIENT_ID`: The client to use for connecting to the Capture app.

* `JANRAIN_CLIENT_SECRET`: The secret for the client.

* `JANRAIN_SCHEMA_NAME`: The name of the Capture schema containing the user
records. (default: `user`)

* `JANRAIN_ATTRIBUTES`: Additional attributes that will be copied from Capture
to Sailthru (uuid and email are always included). This should be a
comma-separated list using dot-notation to refer to non-top-level attributes.

* `SAILTHRU_API_KEY`: The api key for the Sailthru account.

* `SAILTHRU_API_SECRET`: The secret for the api key.
