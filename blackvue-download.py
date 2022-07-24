import argparse
import logging
import os
import pathlib
import shutil
import signal
import sys
import time
import urllib3
import requests

logging.basicConfig(
    format='%(asctime)s - %(levelname)-10s - %(message)s',
)

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_WAIT_TIME = 300
HTTP_TIMEOUT = 13
EARLY_HOUR = 6
LATE_HOUR = 20

logger = logging.getLogger(__name__)

timeformat = "%Y-%m-%d %H:%M"


def sig_handler(signalnum, frame):
    logging.debug(f"Caught signal {signalnum}: {frame}")
    logging.info("Exiting program.")
    exit()


if __name__ == '__main__':

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    parser = argparse.ArgumentParser(description="Download files from BlackVue camera")
    parser.add_argument("destination", help="The target download directory")
    parser.add_argument("host", help="The IP / Hostname of the dashcam")
    parser.add_argument("--wait_time", default=os.environ.get("WAIT_TIME", DEFAULT_WAIT_TIME), help="Sets the wait time between rescanning the dashcam file library, defaults to 5mins")
    parser.add_argument("--log_level", default=os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL), help="Set the log level, defaults to INFO")
    parser.add_argument("--skip_night", action='store_true', help="Declare this flag if you want to skip night time recordings")
    parser.add_argument("--early_hr", default=EARLY_HOUR, help="ONLY USE WITH --skip_night to set the early hour value, defaults to 6am")
    parser.add_argument("--late_hr", default=LATE_HOUR, help="ONLY USE WITH --skip_night to set the late hour value, defaults to 8pm")

    args = parser.parse_args()

    logger.setLevel(args.log_level)

    logger.info("Running program.")

    base = "http://" + args.host
    url = f"{base}/blackvue_vod.cgi"

    if not os.path.isdir(args.destination):
        logger.error(f"Destination directory {args.destination} does not exist.")
        sys.exit(1)

    while True:

        logger.debug("Starting run.")

        skipped = 0
        downloaded = 0
        errored = 0

        try:
            logger.info(f"Getting {url}")
            result = requests.get(url, timeout=5)

            if result.status_code > 299:
                raise ValueError(f"{result.status_code} {result.reason}")

            content = result.content.splitlines()
            cam_files = []
            for f in content:
                if "Record" in f.decode():
                    video = f.decode().split(",")[0].split(":")[1]
                    cam_files.append(video)
                    if video.endswith("_NF.mp4"):
                        basename = video[:-5]
                        cam_files.append(basename + ".3gf")
                        cam_files.append(basename + ".gps")

            for f in sorted(cam_files):
                fn = f.split("/")[-1]
                file_time = fn.split("_")[1]
                y, m, d = fn[0:4], fn[4:6], fn[6:8]
                dest_dir = os.path.join(args.destination, y, m, d)
                if os.path.isfile(os.path.join(dest_dir, fn)):
                    logger.info(f"File {fn} already downloaded, skipping.")
                    skipped += 1
                elif args.skip_night and (int(file_time[0:2]) >= 20 or int(file_time[0:2]) <= 6):
                    logger.info(f"File {fn} is during the night, skipping.")
                    skipped += 1
                else:
                    dest = os.path.join(args.destination, fn)
                    logger.info(f"Downloading {f} to {dest} ...")
                    try:
                        r = requests.get(base + f, stream=True, timeout=HTTP_TIMEOUT)
                        with open(dest + ".tmp", 'wb') as f:
                            shutil.copyfileobj(r.raw, f)
                        pathlib.Path(dest_dir).mkdir(parents=True, exist_ok=True)
                        os.rename(dest + ".tmp", os.path.join(dest_dir, fn))

                        downloaded += 1
                    except TimeoutError as rt:
                        logger.error(f"Connection timed out while downloading: {rt}")
                        errored += 1

            logger.info(f"{len(cam_files)} total, {skipped} skipped, {downloaded} downloaded, {errored} errored.")

        except requests.exceptions.ReadTimeout as rt:
            logger.warning(f"Connection timeout to {args.host}: {rt}")
        except requests.exceptions.ConnectionError as ce:
            logger.warning(f"Cannot connect to {args.host}: {ce}")
        except ValueError as ve:
            logger.error(ve)
        except urllib3.exceptions.ReadTimeoutError as te:
            logger.error(te)

        logger.debug(f"Ending run, waiting {args.wait_time} seconds.")
        time.sleep(int(args.wait_time))
