# Fordo NDI Streamer — Build and Installation Notes

This document records the verified build, configuration, deployment, and troubleshooting steps used while developing Fordo NDI Streamer.

It is intended to be updated throughout development and serves as the engineering reference behind the public-facing README and installer.

## Project Goals

Fordo NDI Streamer is being developed as a cross-platform NDI application supporting:

- Raspberry Pi OS
- Linux
- macOS
- Windows
- ARM64 and x86_64 where supported by the NDI runtime

The Raspberry Pi implementation currently operates primarily as an NDI display appliance.

Future macOS development is planned to handle heavier streaming and transcoding workloads.

## Current Verified Raspberry Pi Platform

- Raspberry Pi 5
- 8 GB RAM
- 64-bit Raspberry Pi OS / Debian
- Architecture: ARM64 / aarch64
- Desktop compositor: labwc
- Display protocol: Wayland
- Chromium: /usr/bin/chromium
- Gigabit Ethernet

## Current Application Architecture

NDI Network Source
→ Native NDI Receiver
→ FastAPI Backend
→ MJPEG Browser Preview
→ Chromium Kiosk Display

Core components:

- app/main.py
- app/ndi_discovery.py
- app/system_metrics.py
- app/static/index.html
- native/ndi_preview.cpp
- scripts/start-appliance.sh

## Verified Features

- Automatic NDI source discovery
- Web dashboard
- CPU, temperature, memory, and network monitoring
- Live NDI browser preview
- Start and Stop preview controls
- Automatic recovery when an NDI source disappears
- Automatic reconnection when the source returns
- Preview status indicators:
  - Red — Stopped
  - Amber — Connecting or Reconnecting
  - Green — LIVE
- Remember last selected NDI source
- Automatically start the remembered source
- Fullscreen kiosk display mode
- Esc returns from NDI-only view to the Fordo dashboard
- Kiosk Mode button returns to NDI-only display
- Alt+F4 closes the dedicated Fordo Chromium window
- Automatic startup after Raspberry Pi reboot
- Dedicated Chromium profile
- Chromium keyring prompt avoided with --password-store=basic

## Raspberry Pi Service

Fordo runs as a systemd service:

fordo-ndi.service

The working service configuration uses:

- the current project directory as WorkingDirectory
- the project virtual environment
- Uvicorn
- host 0.0.0.0
- port 8080
- automatic restart on failure
- network-online.target

The current development machine uses the user:

metrotimer

The installer must NOT hardcode this username. It must determine the current installation user dynamically.

The current development project path is:

/home/metrotimer/Documents/Timer/Fordo-NDI-streamer

The installer must NOT hardcode this path. It must determine or configure the installation path dynamically.

## Appliance Startup

The verified appliance launcher is:

scripts/start-appliance.sh

Its working startup flow is:

1. Wait for the Fordo health endpoint to become available.
2. Allow NDI discovery a short period to initialize.
3. Launch Chromium using a dedicated Fordo browser profile.
4. Start Chromium in kiosk mode.
5. Open Fordo using the appliance query parameter.
6. Restore the previously selected NDI source.
7. Automatically start the preview.
8. Display the NDI source fullscreen.

Verified boot sequence:

Raspberry Pi Boot
→ Desktop / labwc
→ Fordo systemd service
→ FastAPI health endpoint available
→ Chromium kiosk
→ Saved NDI source selected
→ Preview starts
→ NDI video fills the physical display

## Chromium Appliance Configuration

The working Chromium launcher uses a dedicated profile:

~/.config/fordo-chromium

Important Chromium options include:

- --kiosk
- --no-first-run
- --disable-session-crashed-bubble
- --disable-infobars
- --disable-translate
- --autoplay-policy=no-user-gesture-required
- --password-store=basic

The --password-store=basic option was required to prevent the desktop keyring prompt from interrupting unattended appliance startup.

Using a dedicated Chromium profile was required because launching kiosk mode with an already-running normal Chromium session could cause the Fordo URL to open as a normal browser tab instead of a dedicated kiosk window.

## Raspberry Pi Desktop Autostart

The Raspberry Pi appliance currently uses a user-level labwc autostart file:

~/.config/labwc/autostart

The verified development configuration includes:

/usr/bin/lwrespawn /usr/bin/pcmanfm-pi &
/usr/bin/lwrespawn /usr/bin/wf-panel-pi &
/usr/bin/kanshi &
/usr/bin/lxsession-xdg-autostart &
/home/metrotimer/Documents/Timer/Fordo-NDI-streamer/scripts/start-appliance.sh &

This autostart configuration is outside the Git repository.

The production installer must configure desktop autostart automatically when appliance mode is enabled.

## Installer Rules for Desktop Autostart

The installer must not blindly replace an existing user autostart file.

It should:

1. Detect whether ~/.config/labwc/autostart already exists.
2. Create ~/.config/labwc if necessary.
3. Back up an existing autostart file before modifying it.
4. Preserve existing user entries.
5. Add the Fordo appliance launcher only if it is not already present.
6. Avoid duplicate Fordo launcher entries when the installer is rerun.
7. Use the actual installation path instead of hardcoding /home/metrotimer.
8. Use the actual user's HOME directory instead of hardcoding a username.
9. Make the appliance launcher executable.
10. Provide a clean uninstall path that removes only the Fordo entry and preserves unrelated user configuration.

## Idempotent Installation Requirement

The installer should be safe to run more than once.

Repeated installation must not:

- duplicate autostart entries
- recreate the virtual environment unnecessarily
- overwrite user configuration without backup
- create duplicate services
- repeatedly reinstall already-satisfied dependencies
- leave multiple Fordo Chromium profiles or startup processes

Where possible, the installer should detect existing configuration and update it safely.

## NDI Runtime and SDK

The verified Raspberry Pi development system currently has the NDI runtime and development files installed.

Verified locations include:

- /usr/local/lib/libndi.so
- /usr/local/lib/libndi.so.5
- /usr/local/lib/libndi.so.5.6.1
- /usr/local/include/Processing.NDI.Lib.h
- /usr/local/lib/ndi_hx

The application currently depends on these Linux NDI components being available.

The cross-platform installer must not assume these paths are valid on every operating system.

Platform-specific NDI handling will be required for:

- Raspberry Pi OS
- other Linux distributions
- macOS
- Windows

The installer should first detect whether a compatible NDI runtime and required development components are already installed.

NDI SDK/runtime redistribution must only be automated where the applicable NDI licensing terms permit it. Until redistribution requirements are verified, the installer should support detection and clear installation guidance rather than assuming NDI binaries can be bundled with Fordo.

## Native NDI Preview Receiver

Native source:

native/ndi_preview.cpp

The verified Raspberry Pi receiver:

- initializes the NDI library
- discovers NDI sources
- selects the requested source by exact name
- creates an NDI receiver
- receives video frames
- converts received BGRX/BGRA video to RGB
- JPEG-encodes frames using libjpeg
- outputs multipart MJPEG to stdout
- exits after an extended video timeout so the browser recovery logic can reconnect

The generated native executable is:

native/ndi_preview

Generated native binaries should not be committed to Git.

## Verified Raspberry Pi Native Build

The working Raspberry Pi build command is:

g++ -O2 -std=c++17 native/ndi_preview.cpp -I/usr/local/include -L/usr/local/lib -lndi -ljpeg -Wl,-rpath,/usr/local/lib -o native/ndi_preview

The installer should eventually generate or select the correct native build procedure for the detected operating system and architecture.

Linux currently uses libndi.so.

macOS and Windows will require their respective NDI runtime/library formats and platform-specific native executable handling.

## Current Application Platform Assumptions

Some application code is still Raspberry Pi/Linux-oriented.

Examples include:

- ./native/ndi_preview executable path
- LD_LIBRARY_PATH
- /usr/local/lib
- /usr/local/lib/ndi_hx
- systemd
- labwc
- /usr/bin/chromium

Therefore, the installer framework can be cross-platform from the beginning, but Windows and macOS support must not be marked as complete until the application runtime itself has been adapted and tested on those platforms.

## Cross-Platform Installer Architecture

Fordo should use a Python-based installer entry point rather than a single Bash-only installer.

Planned structure:

install/
├── install.py
├── platforms/
│   ├── linux.py
│   ├── raspberry_pi.py
│   ├── macos.py
│   └── windows.py
├── checks/
└── templates/

The installer entry point will detect the host operating system and architecture, then delegate platform-specific work to the appropriate module.

## Platform Detection

The installer should detect at minimum:

- operating system
- CPU architecture
- current user
- HOME directory
- installation directory
- Raspberry Pi hardware where applicable
- Python availability
- compiler availability
- Chromium or compatible browser availability
- NDI runtime/development files
- service/startup capabilities

Likely Python detection methods include:

- platform.system()
- platform.machine()
- pathlib.Path.home()
- environment variables
- Linux hardware/model inspection for Raspberry Pi detection

## Platform Strategy

### Raspberry Pi / Linux

This is the first fully implemented and tested target.

Responsibilities include:

- dependency validation
- Python virtual environment
- Python package installation
- native preview compilation
- NDI validation
- systemd service installation
- labwc appliance autostart where applicable
- Chromium kiosk configuration
- health verification

### macOS

The macOS installer module should eventually handle:

- macOS NDI runtime detection
- native receiver compilation
- Python environment setup
- browser detection
- LaunchAgent or LaunchDaemon startup configuration
- macOS-specific library search paths
- streaming/transcoding components when Mac streaming work begins

### Windows

The Windows installer module should eventually handle:

- Windows NDI runtime detection
- Visual C++ or suitable compiler/toolchain detection
- Python environment setup
- Windows native executable build or packaged binary selection
- browser detection
- startup/service configuration appropriate for Windows
- Windows DLL discovery and runtime paths

Windows and macOS support should initially report incomplete platform-specific requirements clearly rather than pretending installation is fully supported before those platforms have been tested.

## Other Raspberry Pi Models

The installer should not assume every Raspberry Pi has the same resources as Raspberry Pi 5.

It should identify the model and architecture where possible and validate:

- 64-bit operating system
- available memory
- CPU architecture
- required compiler support
- NDI runtime compatibility
- browser availability

Unsupported combinations should fail with a clear explanation rather than attempting an unsafe installation.

## Installer Design Principles

The installer should be:

- cross-platform
- modular
- idempotent
- rerunnable
- safe for existing user configuration
- explicit about unsupported platforms
- capable of clean health validation
- suitable for future upgrade and uninstall workflows

## Verified Installer Platform Detection

The initial cross-platform installer framework has been created and tested successfully on the Raspberry Pi development system.

Verified installer entry point:

install/install.py

Verified supporting modules:

- install/checks/system_requirements.py
- install/platforms/raspberry_pi.py

The installer successfully detects:

- Operating system: Linux
- Architecture: aarch64
- Python version
- Current user
- HOME directory
- Project root
- Raspberry Pi hardware
- Raspberry Pi model
- Desktop environment
- Session type

Verified Raspberry Pi model:

Raspberry Pi 5 Model B Rev 1.1

The installer correctly detected the project root dynamically rather than relying on a hardcoded installation path.

## Verified Requirement Checks

The following requirements were detected successfully on the working Raspberry Pi:

- python3
- pip3
- g++
- git
- curl
- chromium
- systemctl
- libjpeg development header
- NDI library
- NDI development header

All requirement checks returned OK.

## Verified Raspberry Pi Platform Validation

The Raspberry Pi platform validation successfully confirmed:

- Raspberry Pi hardware detected
- Supported 64-bit ARM architecture
- Raspberry Pi model detected
- Project root exists

Final validation result:

Raspberry Pi platform validation PASSED.

This confirms that the current installer framework can distinguish a supported Raspberry Pi environment before performing installation actions.

## Verified Linux Installation Inspection

The Linux installation inspection layer has been created and tested successfully.

Verified module:

install/platforms/linux.py

The installer currently checks for:

- apt availability
- existing project virtual environment
- requirements.txt
- native/ndi_preview.cpp
- compiled native/ndi_preview binary

On the working Raspberry Pi, all of the following were detected as PRESENT:

- apt_available
- virtual_environment
- requirements_file
- native_preview_source
- native_preview_binary

This confirms the installer can inspect an existing Fordo installation without modifying it.

The inspection layer is intentionally non-destructive.

No packages are installed, no services are changed, no files are overwritten, and no compilation is triggered during inspection.

## Verified Python Virtual Environment Handling

A reusable Python virtual environment module has been created:

install/platforms/python_environment.py

The module supports platform-specific virtual environment layouts:

- Linux/macOS: .venv/bin/
- Windows: .venv/Scripts/

Verified behavior on the working Raspberry Pi:

- Existing .venv detected successfully
- Installer reported that the environment already exists
- No recreation was attempted
- No files were modified
- No existing environment was overwritten

Verified result:

Python virtual environment already exists. No changes made.

This confirms the first installation action is idempotent and safe to rerun.

## Verified Python Dependency Health Check

A Python requirements module has been created:

install/platforms/python_requirements.py

Verified behavior on the working Raspberry Pi:

- The installer located the Python interpreter inside the existing .venv.
- requirements.txt was found successfully.
- pip check completed successfully.
- No package installation was performed during this verification step.

Verified result:

Python package dependency check PASSED.

Note:

pip check confirms that installed Python packages have compatible dependencies, but it does not by itself guarantee that every package and exact version listed in requirements.txt is installed. The installer should perform an additional requirements-file comparison before deciding whether installation is necessary.

## Verified Exact Python Requirements Comparison

An exact requirements comparison module has been created:

install/checks/python_requirements_check.py

The checker:

- reads pinned package versions from requirements.txt
- reads installed packages from the project virtual environment
- detects missing packages
- detects version mismatches
- reports whether installation action is required

Verified result on the working Raspberry Pi:

Pinned requirements checked: 20

Requirements status: SATISFIED

This confirms that the current .venv matches the pinned Python package versions required by the project.

The installer can use this result to avoid unnecessary pip installation when requirements are already satisfied.

## Verified Raspberry Pi OS / Debian Package Mapping

Package ownership was verified directly on the working Raspberry Pi rather than inferred from executable names.

Verified mappings:

- Chromium executable /usr/bin/chromium -> chromium
- pip3 executable /usr/bin/pip3 -> python3-pip
- g++ launcher /usr/bin/g++ -> g++
- curl executable /usr/bin/curl -> curl
- git executable /usr/bin/git -> git
- JPEG header /usr/include/jpeglib.h -> libjpeg62-turbo-dev:arm64

Python virtual environment support installed on the verified system:

- python3-venv
- python3.13-venv

For installation, the generic python3-venv package should be preferred rather than hardcoding the current Python minor version.

Likewise, the generic g++ package should be preferred. Although the resolved compiler binary is supplied by a version/architecture-specific compiler package, /usr/bin/g++ is owned by the generic g++ package.

The Linux installer must account for distribution differences. Package names verified on Raspberry Pi OS / Debian must not automatically be assumed to be valid on Ubuntu, Fedora, Arch, or other Linux distributions.

NDI remains separate from normal operating-system package installation and requires its own detection and platform-specific handling.

## Verified Debian Package Inspection

A Debian/Raspberry Pi package-management module has been created:

install/platforms/debian_packages.py

The module currently:

- verifies apt-get availability
- checks required packages using dpkg-query
- identifies missing packages
- prints a package installation plan
- makes no system changes during inspection

Verified required packages on the working Raspberry Pi:

- python3
- python3-pip
- python3-venv
- g++
- git
- curl
- chromium
- libjpeg62-turbo-dev

Verified result:

All required Debian packages are installed.

This confirms the installer can determine package state accurately before attempting installation.

## Verified Debian Package Installation Safety

The Debian package-management module now includes an installation action:

install_missing_packages()

The action supports dry-run behavior and is designed to install only missing packages.

Verified behavior on the working Raspberry Pi:

- All required Debian packages were already installed.
- The installation action detected that no package changes were necessary.
- sudo was not invoked.
- apt-get was not invoked.
- No packages were modified.

Verified result:

No Debian package installation required.

This confirms the Debian package installation action is idempotent on an already-configured system.

## Verified Integrated Installer Dry-Run Flow

The main installer entry point now integrates:

- environment detection
- system requirement checks
- Debian package inspection
- Debian package installation planning in dry-run mode
- Linux installation-state inspection
- exact Python requirements comparison
- Raspberry Pi platform validation

Verified result on the working Raspberry Pi:

- All required Debian packages reported INSTALLED.
- No Debian package installation was required.
- Existing virtual environment was detected.
- requirements.txt was detected.
- Native preview source was detected.
- Native preview binary was detected.
- All 20 pinned Python requirements were satisfied.
- Raspberry Pi platform validation passed.
- No system changes were performed.

This confirms the integrated installer is currently safe to run on an already-configured Fordo Raspberry Pi installation.

## Verified Missing-Package Dry-Run Simulation

The Debian package installation action was tested using a simulated missing-package state without uninstalling or modifying any packages on the development Raspberry Pi.

Simulated missing packages:

- git
- libjpeg62-turbo-dev

The installer correctly generated:

sudo apt-get install -y git libjpeg62-turbo-dev

The installer also clearly reported:

DRY RUN - no packages will be installed.

No packages were installed, removed, or modified during this test.

This verifies that the installer can construct an installation command containing only missing packages before performing privileged package-management operations.

## Verified Native NDI Preview Build Inspection

A native preview build module has been created:

install/platforms/native_preview.py

The module currently checks for:

- g++ compiler
- native/ndi_preview.cpp
- NDI development header
- NDI shared library
- JPEG development header
- existing native/ndi_preview binary

Verified result on the working Raspberry Pi:

- compiler PRESENT
- source PRESENT
- ndi_header PRESENT
- ndi_library PRESENT
- jpeg_header PRESENT
- binary PRESENT

Because the native preview binary already existed, the installer correctly reported:

Native preview binary already exists. No build required.

No compilation was performed and the existing working native binary was not modified.

This confirms the native build action is idempotent on an already-configured system.

## Verified Integrated Native Preview Check

The main installer now integrates native NDI preview build inspection.

Verified behavior on the working Raspberry Pi:

- compiler detected
- native preview source detected
- NDI header detected
- NDI shared library detected
- JPEG development header detected
- existing native preview binary detected

Because the binary already existed, the installer correctly skipped compilation and reported:

Native preview binary already exists. No build required.

This verified that native build inspection is correctly integrated into the main installer without overwriting the working binary.

## Verified Integrated Installer Dry-Run

The Fordo installer dry-run now validates the complete Raspberry Pi/Linux deployment stack without making system changes.

Verified stages:

- Linux and Raspberry Pi environment detection
- Debian 13 trixie distribution detection
- Debian package inspection
- NDI runtime inspection
- native NDI preview build inspection
- systemd service inspection
- labwc appliance autostart inspection
- Python virtual environment inspection
- Python requirements dry-run
- exact pinned requirements comparison
- Raspberry Pi platform validation

The current working Raspberry Pi reports all required components present and healthy.

Installer modes are currently:

- default / --check: inspection only
- --dry-run: inspection plus planned installation actions
- --install: intentionally blocked until final installation workflow verification is complete


## Verified Installer Hardening Checkpoint

Additional installer safety and portability work was completed and verified on the working Raspberry Pi.

### Python Virtual Environment

`install/platforms/python_environment.py` now supports dry-run operation through `create_virtual_environment(project_root, dry_run=True)`.

Verified behavior on the configured Raspberry Pi:

- the existing `.venv` is detected
- no virtual environment is recreated
- the helper is now suitable for both dry-run and future real-install workflows
- the main installer now uses this helper instead of duplicating virtual-environment logic

The complete integrated installer dry-run was rerun successfully after this change.

### systemd Service Backup Protection

`install/platforms/systemd_service.py` now protects existing systemd configurations before replacement.

Behavior:

- a matching Fordo service remains unchanged
- a missing service can be installed normally in future install mode
- an existing mismatched service is backed up before replacement
- backups use a timestamped filename

The mismatched-service path was safely simulated using a temporary service file under `/tmp`.

The dry-run correctly planned:

- backup of the existing service
- writing the replacement service
- `systemctl daemon-reload`
- enabling `fordo-ndi.service`
- restarting `fordo-ndi.service`

The production `/etc/systemd/system/fordo-ndi.service` was not modified during this test.

### labwc Stale Autostart Entry Handling

`install/platforms/labwc_autostart.py` now detects stale Fordo appliance startup entries instead of only checking for an exact current path.

This prevents an installation moved to a different directory from accumulating multiple Fordo startup entries.

A temporary labwc autostart file was used to verify the real replacement path.

Verified behavior:

- stale Fordo `scripts/start-appliance.sh` entry detected
- stale entry replaced with the current project path
- unrelated labwc startup entries preserved
- backup created before modification
- no duplicate Fordo entry created
- configuration validation returned success

The real user labwc autostart file was not modified during this test.

### Desktop-Aware labwc Configuration

The main installer now checks the detected desktop environment before running labwc-specific appliance autostart logic.

labwc configuration is performed only when the desktop environment identifies labwc.

This prevents generic Linux installations using another desktop environment from receiving Raspberry Pi/labwc-specific autostart configuration.

The Raspberry Pi reports:

`Desktop Environment: labwc:wlroots`

and therefore continues to use the correct labwc configuration path.

The complete integrated dry-run was rerun successfully after this change.

### Safe Fresh Native Preview Build Test

`install/platforms/native_preview.py` now supports an optional output path for native builds.

This allows the installer build process to be tested without deleting or replacing the working production binary.

A real compilation was performed using:

`/tmp/fordo-ndi-preview-test`

Verified result:

- C++ source compiled successfully
- NDI headers and library linked successfully
- JPEG dependency linked successfully
- temporary native executable was created
- build helper returned success
- production `native/ndi_preview` was not modified
- temporary test executable was removed afterward

This verifies that Fordo can build the native NDI preview executable from source on the current Raspberry Pi rather than merely detecting an already-built binary.

### Current Safety Status

At this checkpoint the installer has verified:

- Debian package inspection and missing-package planning
- NDI runtime inspection
- Python virtual environment handling
- Python requirements inspection and dry-run installation
- exact pinned Python dependency comparison
- native NDI preview inspection
- real native preview compilation to a safe temporary target
- systemd service inspection and backup protection
- labwc autostart inspection, backup, and stale-entry replacement
- desktop-aware labwc configuration
- Raspberry Pi platform validation
- complete integrated dry-run

`--install` remains intentionally disabled.

No production service, appliance autostart configuration, installed package, Python environment, or working native preview binary was modified while performing these installer-hardening tests.
