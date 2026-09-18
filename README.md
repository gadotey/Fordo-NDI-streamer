# Fordo NDI Streamer

Fordo NDI Streamer turns a supported Raspberry Pi into a dedicated NDI network display appliance.

Fordo automatically discovers NDI sources on your local network and provides a browser-based interface for selecting and displaying them. It is designed to start automatically when the Raspberry Pi boots.

## Features

- Automatic NDI source discovery
- Live NDI video preview
- Source selection from a web dashboard
- Full-screen kiosk display
- Automatic reconnection when an NDI source disappears and returns
- Remembers the last selected NDI source
- Automatically starts the remembered source
- NDI source thumbnail previews
- Source availability status
- Raspberry Pi system health information
- Automatic startup using systemd
- Chromium kiosk mode
- Install, repair, and uninstall commands

## Current Supported Platform

The current Raspberry Pi release has been developed and tested primarily with:

- Raspberry Pi 5
- 64-bit Raspberry Pi OS
- ARM64 / aarch64
- Debian-based Raspberry Pi OS
- labwc / Wayland desktop
- Ethernet network connection recommended

Support for additional Linux platforms, Windows, and macOS is planned.

## What You Need

Before installing Fordo, you need:

- A supported Raspberry Pi
- 64-bit Raspberry Pi OS with Desktop
- Internet access during installation
- Ethernet or Wi-Fi connection to the same network as your NDI sources
- Git
- The official NDI SDK/runtime for Linux

## Important NDI Requirement

Fordo uses the official NDI SDK/runtime to receive NDI video.

Fordo does **not** bundle or redistribute the NDI SDK/runtime.

You must obtain the NDI SDK/runtime directly from the official NDI developer website and accept any applicable NDI license terms yourself.

Official NDI SDK download page:

https://ndi.video/for-developers/ndi-sdk/download/

For Raspberry Pi 5 running 64-bit Raspberry Pi OS, Fordo uses the ARM64/aarch64 NDI runtime.

The Fordo installer is being designed to detect an officially downloaded and extracted NDI SDK and handle the technical installation of the required runtime files automatically.

---

## Installation

### 1. Prepare Raspberry Pi OS

Install 64-bit Raspberry Pi OS with Desktop.

Complete the normal Raspberry Pi first-boot setup and connect the Pi to your network.

For the best NDI performance, a wired Gigabit Ethernet connection is recommended.

### 2. Download the Official NDI SDK

Download the Linux NDI SDK from the official NDI developer website:

https://ndi.video/for-developers/ndi-sdk/download/

Accept the applicable NDI license terms and download the Linux SDK.

Do not obtain the NDI runtime from an unofficial source.

> **Development note:** The final fresh-install workflow for automatically detecting and installing the downloaded NDI SDK is currently being finalized. This section will be validated on a freshly imaged Raspberry Pi before the installation guide is marked production-ready.

### 3. Clone Fordo

Open Terminal on the Raspberry Pi and run:

```bash
git clone https://github.com/gadotey/Fordo-NDI-streamer.git
cd Fordo-NDI-streamer
```

### 4. Check the System

Run:

```bash
python3 install/install.py --check
```

Fordo will inspect the Raspberry Pi and report the status of required components.

### 5. Preview the Installation

Before making changes, run:

```bash
python3 install/install.py --dry-run
```

This shows what Fordo intends to configure without performing the installation.

### 6. Install Fordo

Run:

```bash
python3 install/install.py --install
```

The installer configures the Fordo application, Python environment, native NDI receiver, systemd service, and Raspberry Pi appliance startup.

### 7. Reboot

After installation completes successfully, reboot:

```bash
sudo reboot
```

After the Raspberry Pi desktop starts, Fordo should launch automatically in Chromium kiosk mode.

---

## Using Fordo

When Fordo starts, the dashboard displays NDI sources discovered on the local network.

Each source appears as a 16:9 source card with a thumbnail preview.

Select a source to display it in the main preview.

Fordo remembers the last selected source and can automatically restore it after reboot.

If an NDI source temporarily disappears, Fordo continues monitoring for it and reconnects when the source becomes available again.

## Appliance Controls

### Return to the Dashboard

While viewing an NDI source full-screen, press:

```text
Esc
```

This returns to the Fordo dashboard while keeping Chromium in kiosk mode.

### Return to NDI-Only View

Use the **Kiosk Mode** button on the Fordo dashboard.

### Close Chromium

Press:

```text
Alt+F4
```

---

## Repair Fordo

If the installation becomes damaged or its configuration needs to be restored, run:

```bash
cd ~/Fordo-NDI-streamer
python3 install/install.py --repair
```

Repair validates and restores Fordo-managed components without requiring a complete reinstall.

---

## Uninstall Preview

To see what Fordo would remove without changing anything, run:

```bash
cd ~/Fordo-NDI-streamer
python3 install/install.py --uninstall-dry-run
```

## Uninstall Fordo

To uninstall Fordo, run:

```bash
cd ~/Fordo-NDI-streamer
python3 install/install.py --uninstall
```

The uninstall process is intentionally conservative.

Fordo removes system components managed by Fordo while preserving items that may be useful to the user or other applications.

The uninstall process preserves:

- The Fordo Git repository
- The Python virtual environment
- The compiled native NDI receiver
- The separately installed NDI SDK/runtime
- Chromium
- Debian packages installed on the system
- Unrelated desktop autostart entries
- Existing systemd backup files

---

## Network Recommendations

NDI video can use significant network bandwidth.

For reliable operation:

- Use Gigabit Ethernet whenever possible
- Keep the Raspberry Pi and NDI sender on the same LAN when practical
- Use quality Gigabit switches
- Avoid congested Wi-Fi for important productions
- Verify that host firewalls allow NDI communication
- Make sure the NDI sender is visible to other NDI-capable devices

If Fordo discovers an NDI source but cannot receive video, check the sender computer's firewall and network configuration.

---

## Health Check

Fordo provides a local health endpoint:

```text
http://127.0.0.1:8080/api/health
```

A healthy Fordo service should return a successful response.

---

## Troubleshooting

### Fordo Does Not Discover Any NDI Sources

Check that:

- The NDI sender is running
- The Raspberry Pi and sender are on the same network
- The sender firewall allows NDI traffic
- The Ethernet connection is active
- The NDI source is visible from another NDI-capable device if available

### Source Appears but Video Does Not Start

Check the sender firewall first.

A source may sometimes be discoverable while its video connection is blocked.

### Fordo Does Not Start After Reboot

Run:

```bash
cd ~/Fordo-NDI-streamer
python3 install/install.py --check
```

If Fordo reports configuration problems, run:

```bash
python3 install/install.py --repair
```

Then reboot.

### Check Fordo Service Status

Run:

```bash
systemctl status fordo-ndi.service
```

### Restart Fordo Service

Run:

```bash
sudo systemctl restart fordo-ndi.service
```

---

## Installer Commands

Fordo currently provides the following installer commands:

```text
python3 install/install.py --check
python3 install/install.py --dry-run
python3 install/install.py --install
python3 install/install.py --repair
python3 install/install.py --uninstall-dry-run
python3 install/install.py --uninstall
```

---

## Project Architecture

Fordo currently consists of:

- FastAPI backend
- Native NDI receiver
- Web-based dashboard
- WebSocket source/status updates
- NDI source discovery
- Thumbnail capture
- Main continuous NDI preview receiver
- System health monitoring
- systemd service management
- Chromium kiosk appliance startup

Fordo uses a single-owner continuous receiver architecture for the main NDI preview. Thumbnail captures use independent single-frame receivers.

---

## Project Status

The Raspberry Pi NDI display appliance is operational.

Current development is focused on making installation simple and repeatable for a brand-new Raspberry Pi.

The installation documentation will be validated by completely reimaging a Raspberry Pi and following only the instructions in this README.

Future development includes:

- Additional Raspberry Pi/Linux validation
- Generic Ubuntu/Linux support
- Windows installer
- macOS installer
- Mac-based NDI to RTMP/RTMPS streaming

---

## Third-Party Software and Licensing

Fordo is a separate project and does not bundle the NDI SDK/runtime.

NDI and related NDI technologies are provided by their respective owners.

Users are responsible for obtaining the appropriate NDI software and reviewing the license terms that apply to their intended use, particularly when building or distributing commercial products or dedicated appliances.

---

## Repository

Fordo NDI Streamer:

https://github.com/gadotey/Fordo-NDI-streamer