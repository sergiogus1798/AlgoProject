#!/bin/bash
# mt5-wine-system — the root half of MetaQuotes' official mt5linux.sh, run once per machine.
#
# Source: https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5linux.sh
# (fetched 2026-09-27). It does, for Ubuntu 22.04 (jammy): i386 architecture, the WineHQ key
# and repo, and winehq-staging with its recommends. Two deliberate departures:
#   - no `apt upgrade -y` of the whole system: Wine does not need it, and upgrading
#     everything under running SQX installs is not this script's decision to make;
#   - Ubuntu jammy only, the one distribution this project runs on. Other machines: use
#     the official script.
# The user half (prefix, WebView2, the terminal) is bin/mt5-install.sh and needs no root.
#
# Usage:  bin/mt5-wine-system.sh      asks for the sudo password itself
set -euo pipefail

. /etc/os-release
if [ "$ID" != "ubuntu" ] || [ "$VERSION_CODENAME" != "jammy" ]; then
  echo "this script covers Ubuntu jammy only (found $NAME $VERSION_ID); use MetaQuotes' mt5linux.sh"
  exit 1
fi

if command -v wine >/dev/null; then
  echo "wine already installed: $(wine --version)"; exit 0
fi

sudo dpkg --add-architecture i386
sudo mkdir -pm755 /etc/apt/keyrings
wget -qO - https://dl.winehq.org/wine-builds/winehq.key \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/winehq-archive.key -
sudo rm -f /etc/apt/sources.list.d/winehq*
sudo wget -NP /etc/apt/sources.list.d/ \
  https://dl.winehq.org/wine-builds/ubuntu/dists/jammy/winehq-jammy.sources
sudo apt update
sudo apt install --install-recommends winehq-staging -y

echo "installed: $(wine --version). Next, without sudo: bin/mt5-install.sh"
