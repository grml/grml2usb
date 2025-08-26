# grml2usb

[![Sponsor](https://img.shields.io/badge/Sponsor-GitHub-purple?logo=github)](https://github.com/sponsors/grml)
[![GitHub release](https://img.shields.io/github/v/release/grml/grml2usb)](https://github.com/grml/grml2usb/releases)
[![Debian package](https://img.shields.io/debian/v/grml2usb/trixie?label=debian)](https://packages.debian.org/trixie/grml2usb)
[![Ubuntu package](https://img.shields.io/ubuntu/v/grml2usb)](https://packages.ubuntu.com/search?keywords=grml2usb)

Install [Grml](https://grml.org/) Live Linux to a USB key drive.

## Purpose

This tool installs a Grml ISO image (or a running Grml) to USB drives, making them bootable.
You can install multiple Grml flavours on the same USB drive, for example both `amd64` and `arm64` versions.

## Installation

### From Debian repositories

```bash
sudo apt install grml2usb
```

### From GitHub releases

Download the latest release from [GitHub Releases](https://github.com/grml/grml2usb/releases), and then:

```bash
# Download and install .deb package
sudo apt install ./grml2usb_*.deb
```

## Quick Start

1. Install `grml2usb` package
2. [Download a Grml ISO image](https://grml.org/download/)
3. Install it to USB device:
   ```bash
   sudo grml2usb grml.iso /dev/sdX1
   ```

**Warning:** Replace `/dev/sdX1` with the FAT partition on your USB device.
This will destroy all data on the device.

## Documentation

For detailed usage instructions and all available options, visit: https://grml.org/grml2usb/

## License

This project is licensed under the GPL v2+.

## Contributing

- **Source code**: https://github.com/grml/grml2usb
- **Issues**: https://github.com/grml/grml2usb/issues
- **Releases**: https://github.com/grml/grml2usb/releases
- **Grml Live Linux**: https://grml.org
