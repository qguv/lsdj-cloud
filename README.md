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

First, take care of some common prerequisites:

  - install `python` version 3.6 or higher
    - if your system doesn't provide that natively, look into `pyenv`
  - install `python-pipenv` using your system's package manager
    - if your system doesn't provide that natively, try `sudo pip install pipenv`
  - install and configure a **redis server** somewhere and put the credentials in `lsdj-cloud.conf`
  - install and configure a **meriadb server** somewhere and put the credentials in `lsdj-cloud.conf`
  - sign up for an **S3 service** somewhere and put the credentials in `lsdj-cloud.conf`
    - Amazon S3 is expensive; consider Scaleway or Wasabi which are far cheaper
    - alternatively, use a local minio s3-compatible server (especially useful for development)
  - make up a long random string and set it as the flask key in `lsdj-cloud.conf`

Now follow one of the sections below depending on how you'd like to run the server.

### Running in a terminal

  - run `pipenv install`
  - run `pipenv run lsdj-cloud
  - visit [http://localhost:5000](http://localhost:5000)

### Running under systemd --user (development)

  - `systemctl --user link systemd/user/lsdj.cloud.service`
  - `systemctl start lsdj-cloud`
  - `systemctl status lsdj-cloud`

### Running under systemd (production)

  - install nginx and configure it to reverse-proxy port 5000. starting/enabling it is not necessary.
  - move this repository to /usr/local/lib/lsdj-cloud
  - `systemctl link /usr/local/lib/lsdj-cloud/systemd/system/lsdj-cloud.service`
  - run `systemctl enable --now lsdj-cloud` as root
