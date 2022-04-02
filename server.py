import argparse
from aiohttp import web
from hashlib import sha256
import json
import logging
import os
import sys


# Checks that the hash of the provided blob matches the provided hash.
def verify_checksum(checksum, blob):
    new_checksum = sha256(blob).hexdigest()
    return checksum == new_checksum


# Checks that metadata contains the required fields, logging an error and
# return false if not.
def validate_upload_metadata(j):
    if 'id' not in j:
        logging.error(f'Malformed request, no id in metadata {j}')
        return False
    if 'hash' not in j:
        logging.error(f'Malformed request, no hash metadata in {j}')
        return False
    return True


# Checks that post request form data contains the required metadata and binary
# file.
def validate_post(data):
    if not 'bin_file' in data:
        logging.error(f'Malformed request, no bin_file in {data.keys()}')
        return False
    if not 'metadata' in data:
        logging.error(f'Malformed request, no metadata in {data.keys()}')
        return False
    return True


# The upload handler handles POST requests with a binary file and metadata,
# saving the recieved binary file to the configured save_dir and optionally
# checking its integrity using the provided hash as a checksum.
#
# If required metadata or file data is missing, it will return 400
#
# If handled successfully, it will return status 200 with a JSON payload
# containing a friendly message to confirm reciept.
async def upload_handler(request):
    # Parse and validate POST request.
    data = await request.post()
    if not validate_post(data):
        return web.Response(status=400)

    # Extract binary blob from POST request. We read the entire file into
    # memory since they are at most 1MB and therefore not too large to handle
    # several at a time.
    blob = data['bin_file'].file.read()

    # Extract the id and checksum from JSON body.
    metadata = json.loads(data['metadata'])
    if not validate_upload_metadata(metadata):
        return web.Response(status=400)
    content_id = metadata['id']
    content_hash = metadata['hash']

    # Ensure contents match provided checksum, not because we ever expect
    # this to be corrupted, but because it is cool and the whole point of
    # this application is to write a bunch of cool code to see what kind of
    # stuff myenik writes.
    if request.app['config']['verify_hash'] and not verify_checksum(content_hash, blob):
        logging.error('Strict hash checking enabled, but hashes dont match!')
        logging.info('Saving file will be skipped due to hash mismatch!')
        return web.Response(status=400)

    # Save the file contents to the configured location.
    filename = 'server-' + content_id + '.bin'
    path = os.path.join(request.app['config']['uploads_dir'], filename)
    with open(path, 'wb') as f:
        f.write(blob)
        logging.info(f'Wrote a {len(blob)} byte file to {path}')

    # Return friendly message with included length to verify reciept of file.
    response = {
        'message': f'Successfully received the {len(blob)} byte file',
    }
    return web.json_response(response)


# Creates aiohttp Application object with only one route, a POST handler for
# our file uploads.
def create_app(config={}):
    app = web.Application()
    app['config'] = config
    app.router.add_route('POST', '/uploads', upload_handler)
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', action='store', default='127.0.0.1',
                        help='IP address to listen on (use 0.0.0.0 for all)')
    parser.add_argument('-p', '--port', action='store', default='8000', type=int,
                        help='Port to listen on')
    parser.add_argument('-f', '--logfile', action='store',
                        help='Optional file to log to')
    parser.add_argument('-d', '--uploads_dir', action='store', default='/tmp',
                        help='Directory to store uploaded binary files')
    parser.add_argument('--disable-stdout-logging', action='store_true',
                        help='Disable logging to stdout')
    parser.add_argument('--disable-checksum-verification', action='store_true',
                        help='Disable verifying checksums when receiving files')
    args = parser.parse_args()

    # Configure the logging according to the command line args. Logging to
    # files and to stdout is optional, but at least one must be specified since
    # the Python logger requires at least one stream to be configured.
    if not args.logfile and args.disable_stdout_logging:
        print('You must log either to stdout or provide a logfile')
        exit(1)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[SERVER][%(levelname)s][%(asctime)s] - %(message)s')
    if args.logfile:
        file_handler = logging.FileHandler(args.logfile)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    if not args.disable_stdout_logging:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # Finally run the server! Passing `access_log=None` disables some noisy
    # INFO-level logging built in to aiohttp.
    config = {
        'uploads_dir': args.uploads_dir,
        'verify_hash': not args.disable_checksum_verification,
    }
    app = create_app(config)
    web.run_app(app, host=args.address, port=args.port, access_log=None)
