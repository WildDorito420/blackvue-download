# blackvue-download
Download video files from BlackVue camera

Forked from [PhilRW/blackvue-download](https://github.com/PhilRW/blackvue-download)

## How to use
Firstly, install the pip requirements for the script:
```bash
pip install -r requirements.txt
```

Then, run the python script and pass it two arguments: the destination directory and the IP/hostname of the camera.
It will run continuously and will wait 5 minutes between trying to reach the host.

```bash
python ./blackvue-download.py /home/me/BlackVue 192.168.0.123 
```

The script will place the files in subfolders based on year, month, and day (YYYY/MM/DD).

The following flags are available:
- **--wait_time** sets the time between rescanning the dashcam file library, defaults to 5mins
- **--log_level** sets the logging level of the output, defaults to INFO
- **--skip_night** will skip the night time files, between 8pm and 6am
    - **--early_hr** will set the early hour value, defaults to 6 (24hr time)
    - **--late_hr** will set the late hour value, defaults to 20 (24hr time)


## Docker

A docker image is available via GitHub to run the script as a container. All flags can be delcared as environment variables.

`docker run -v /home/me/BlackVue:/data -e HOST=192.168.12.34 ghcr.io/wilddorito420/blackvue-download:1.0`

If you don't map the [data volume](https://docs.docker.com/storage/), it will be anonymous.