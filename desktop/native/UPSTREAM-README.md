# Classic Control Strip

**Created by Drew Owen — MacaqueOS Project**

A classic Mac OS 9-inspired Control Strip for Linux/KDE Plasma Wayland, built with C++ and Qt 6 / LayerShellQt.

## Current version: 2.0.6

### Features

- Mac OS 9-inspired Control Strip with customizable modules
- Classic Platinum, Light, Dark, Bondi Blue, Grape, Graphite and custom themes
- Theme creator with colors, background patterns, images and portable theme import/export
- Custom module icons, position, spacing and monitor settings
- Real Linux volume, display, storage, memory and network controls
- Consolidated **Customize…** menu
- **Classic App Viewer:** compact quick launcher and full Finder-style application browser
- Application search, categories and favorites
- App Viewer colors follow the selected Control Strip theme
- **Quit** and **Restart** commands

## Build

Requires Qt 6 Widgets, LayerShellQt, CMake and a C++17 compiler.

```bash
cmake -S . -B build
cmake --build build -j$(nproc)
./build/classic-control-strip
```

For KDE Plasma on Wayland. Some modules use Linux utilities that may need separate installation.

## Creator

**Drew Owen**, creator and project lead for [MacaqueOS](https://github.com/Zerocool66612/MacaqueOS).

## Status and licensing

Early public source release. Please test on your system before packaging for distribution. No open-source license has been selected yet; permission to reuse or redistribute the source should not be assumed.

AI-assisted development, with iterative project direction and testing.
