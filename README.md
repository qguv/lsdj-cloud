# LSDj Cloud

_currently under heavy development_

LSDj Cloud is a webapp to help you store and organize your LSDj tracks. After uploading an SRAM dump from your Game Boy flash cartridge, each LSDj track is extracted and stored in version control.

  - Version control for your tracks
  - Revert songs back to old versions
  - Serverless
  - JS not required
  - ~~Assemble playlists for quick SRAM download of the latest versions of the tracks in an album or performance set.~~ (soon)
  - ~~Handle LSDj compatibility~~ (later)
  - ~~Create audio previews~~ (later)
  - Forever free and [open source](https://github.com/qguv/lsdj-cloud)

There's a flagship instance running at [https://lsdj.cloud](https://lsdj.cloud).

## Running

  - install `python` version 3.6 or higher (might be `python3` on older systems)
  - install `flask` and `boto3` using `pip` (might be `pip3` on older systems)
  - set up an S3 bucket in Wasabi, AWS, or similar. DO NOT EXPOSE TO THE PUBLIC
  - set up S3 credentials and flask keys in `config.py`
  - run `./lsdj-cloud` and visit [http://localhost:5000](http://localhost:5000)
  - set up your webserver (`nginx` is good) to proxy requsets to the flask port, or better yet, have it hit an actual WSGI server

## Serving (serverless)

  - depends per provider, but the app is fully stateless; all state is stored in S3 for now

```
TODO more specific serverless instructions, maybe a serverless.yml config?
```
