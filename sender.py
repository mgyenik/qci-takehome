import aiohttp
import argparse
import asyncio
from dataclasses import dataclass
import json
from hashlib import sha256
import logging
import os
import random
import sys
import uuid

# `SenderConfig` holds the many parameters that control the behavior of the
# sender application.
@dataclass
class SenderConfig:
    num_files: int
    num_workers: int
    url: str
    save_dir: str
    inject_bad_checksums: bool


# `RandomBlobProvider` is an iterable object that will provide a fixed number
# of randomly generated binary blobs with random sizes.
class RandomBlobProvider:
    # Constructor which configures the quantity and size of random blobs
    # generated. It will generate `N` blobs in the range [`min_size`,
    # `max_size`].
    def __init__(self, min_size, max_size, N):
        self.count = 0
        self.N = N
        self.min_size = min_size
        self.max_size = max_size

    # Iteration start method, we reset the count so that it can be reused in
    # multiple loops.
    def __iter__(self):
        self.count = 0
        return self

    # Next item method, actually generates the blob and returns it, stopping
    # after `N` times.
    def __next__(self):
        self.count += 1
        if self.count > self.N:
            raise StopIteration
        size = random.randrange(self.min_size, self.max_size)
        blob = os.urandom(size)
        return blob


# Process and send one blob. The blob will be saved to a file, and then sent to
# the server along with some metadata.
async def send_blob(name, blob, config):
    # Generate a unique ID for it to pass to the server and ensure unique
    # filenames, as well as compute the checksum.
    new_id = str(uuid.uuid4())
    checksum = sha256(blob).hexdigest()

    # Optionally corrupt the file with a 10% chance to demonstrate server
    # checksum verification. Converting to bytearray unfortunately makes a copy
    # of the blob, but they are only 1MB max, so not a problem for now.
    if config.inject_bad_checksums and random.random() < 0.1:
        logging.info(f'{name} intentionally corrupting blob')
        blob = bytearray(blob)
        blob[0] += 1

    # Write the blob to a file synchronously, blocking the coroutine until
    # done.
    filename = 'sender-' + new_id + '.bin'
    path = os.path.join(config.save_dir, filename)
    with open(path, 'wb') as f:
        f.write(blob)
        logging.info(f'{name} wrote binary file to {path}')

    # Send file and metadata to the server as multipart/form-data in a POST
    blob_file = open(path, 'rb')
    blob_metadata = {'id': new_id, 'hash': checksum}
    form_data = aiohttp.FormData()
    form_data.add_field('metadata', json.dumps(blob_metadata))
    form_data.add_field('bin_file', blob_file)
    async with aiohttp.ClientSession() as session:
        async with session.post(config.url, data=form_data) as response:
            if response.status == 200:
                j = await response.json()
                msg = j['message']
                logging.info(f'{name} successfully sent blob and received response {msg}')
            else:
                logging.info(f'{name} encountered status {response.status} sending blob')

# The send worker task runs indefinitely until cancelled, processing one blob
# from the queue at a time.
async def send_worker(name, queue, config):
    try:
        while True:
            blob = await queue.get()
            await asyncio.shield(send_blob(name, blob, config))
            queue.task_done()
    except asyncio.CancelledError:
        logging.info(f'{name} done!')

# The generate worker will generate the blobs and put them in the queue, with a
# random sleep between them.
async def generate_worker(num_files, queue):
    blob_provider = RandomBlobProvider(min_size=1024, max_size=1024*1024, N=num_files)
    for blob in blob_provider:
        logging.info(f'Generated new blob of length {len(blob)}')
        await queue.put(blob)
        sleep_time = random.uniform(0.001, 1.0)
        await asyncio.sleep(sleep_time)
    logging.info(f'Generator task done!')

# The application handles generating and sending random files using a single
# data generator task and a multiple worker tasks that communicate via a queue.
#
# The data generator task generates randomly sized blobs at random time
# intervals and enqueues them. Once the generator task has completed, the
# application will begin the shutdown process, described below.
#
# The worker tasks handle saving the blobs to files, and sending them to the
# server via HTTP. The worker tasks run forever, handling new blobs in the
# queue, until the shutdown process begins.
#
# Shutdown is handled by waiting for the queue to be empty after the generation
# task is done. Once the send workers have taken all blobs from the queue and
# marked them as done, we raise a cancelled exception in each send worker task,
# which they will catch and take a hint to exit gracefully.
async def main(config):
    # Create a queue to send the random blobs to the workers, and an event to
    # coordinate cancellation.
    queue = asyncio.Queue(maxsize=config.num_files)

    # Create the worker tasks, keeping track of the task objects for later when
    # we need to wait on them during shudown
    loop = asyncio.get_running_loop()
    send_tasks = []
    for i in range(config.num_workers):
        t = loop.create_task(send_worker(f'W{i}', queue, config))
        send_tasks.append(t)

    # Now create the data generator task and run the loop until it is
    # completed. Once it is done, every blob that we're going to make has been
    # put in the queue. Once they've been emplaced in the queue, we can wait
    # for the queue to be empty with a `join()` to guarantee that they have all
    # been processed.
    await generate_worker(config.num_files, queue)
    await queue.join()

    # Gracefully terminate all the send workers.
    for t in send_tasks:
        t.cancel()
        await t
    logging.info('Done!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', action='store', default='127.0.0.1',
                        help='IP Address to send to')
    parser.add_argument('-p', '--port', action='store', default='8000', type=int,
                        help='Port to send to')
    parser.add_argument('-n', '--num_files', action='store', default='100', type=int,
                        help='Number of random binary files to generate')
    parser.add_argument('-w', '--num_workers', action='store', default='10', type=int,
                        help='Number of concurrent send workers')
    parser.add_argument('-f', '--logfile', action='store',
                        help='Optional file to log to')
    parser.add_argument('-d', '--binfile_dir', action='store', default='/tmp',
                        help='Directory to store generated binary files')
    parser.add_argument('--disable-stdout-logging', action='store_true',
                        help='Disable logging to stdout')
    parser.add_argument('--inject-bad-checksums', action='store_true',
                        help='Purposefully send bad checksums 10% of the time for testing')
    args = parser.parse_args()

    # Configure the logging according to the command line args. Logging to
    # files and to stdout is optional, but at least one must be specified since
    # the Python logger requires at least one stream to be configured.
    if not args.logfile and args.disable_stdout_logging:
        print('You must log either to stdout or provide a logfile')
        exit(1)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[SENDER][%(levelname)s][%(asctime)s] - %(message)s')
    if args.logfile:
        file_handler = logging.FileHandler(args.logfile)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    if not args.disable_stdout_logging:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # To keep the parameter lists from getting out of hand, bundle all options
    # into a config object and then pass it to the main send logic.
    url = f'http://{args.address}:{args.port}/uploads'
    config = SenderConfig(
        num_files = args.num_files,
        num_workers = args.num_workers,
        url = url,
        save_dir = args.binfile_dir,
        inject_bad_checksums = args.inject_bad_checksums,
    )
    asyncio.run(main(config))
