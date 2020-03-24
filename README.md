# LSDj Cloud

_currently under heavy development_

LSDj Cloud is a webapp to help you store and organize your LSDj tracks. After uploading an SRAM dump from your Game Boy flash cartridge, each LSDj track is extracted and stored in version control.

  - Version control for your tracks
  - Revert songs back to old versions
  - JS not required
  - ~~Assemble playlists for quick SRAM download of the latest versions of the tracks in an album or performance set.~~ (soon)
  - ~~Handle LSDj compatibility~~ (later)
  - ~~Create audio previews~~ (later)
  - ~~Serverless~~ (later)
  - Forever free and [open source](https://github.com/qguv/lsdj-cloud)

There's a flagship instance running at [https://lsdj.cloud](https://lsdj.cloud).

## Running

### Running in a terminal

  - install `python` version 3.6 or higher
  - install `python-pipenv` using your system's package manager. alternatively you can use `sudo pip install pipenv`
  - run `pipenv install`
  - set up an S3 bucket in Wasabi, AWS, or similar. DO NOT EXPOSE TO THE PUBLIC
  - set up S3 credentials and flask keys in `config.py`
  - run `./lsdj-cloud` and visit [http://localhost:5000](http://localhost:5000)
  - set up your webserver (`nginx` is good) to reverse-proxy port 5000; or better yet, have it hit an actual WSGI server
  - (optional) systemd can run the lsdj.cloud service so that it starts automatically on boot, see section **systemd** below

### Running under systemd

  - install nginx and configure it to reverse-proxy port 5000. starting/enabling it is not necessary.
  - move this repository to /usr/local/lib/lsdj.cloud
  - copy contrib/lsdj.cloud.service into `/etc/systemd/system/`
  - run `systemctl daemon-reload` as root
  - run `systemctl enable --now lsdj.cloud` as root
