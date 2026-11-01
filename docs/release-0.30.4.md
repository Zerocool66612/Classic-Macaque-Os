# Macaque Classic 0.30.4 Preview

Experimental Debian 13 amd64 live/install image with a native labwc Wayland session, Classic Control Strip and classic-inspired desktop apps.

- New white side-profile macaque menu icon.
- System-menu accent appears only on hover or press.
- Light and dark desktop themes, internal Files and Notes, Chess and Teapot Studio.
- Wi-Fi/battery/USB controls and installer preview retained.

## Desktop pictures

### Dark
![Dark desktop UI preview](https://raw.githubusercontent.com/Zerocool66612/Classic-Macaque-Os/main/docs/desktop-0.30.4-dark.png)

### Light
![Light desktop UI preview](https://raw.githubusercontent.com/Zerocool66612/Classic-Macaque-Os/main/docs/desktop-0.30.4-light.png)

The pictures are offscreen captures of the current Qt UI, including the actual native Control Strip. The author reports reaching the desktop in VirtualBox after enabling VMSVGA 3D acceleration. Physical USB boot and disk installation are not validated for this version. The automated BIOS boot check timed out without serial output; manual VM testing was used instead. This is a testing preview, not a production release.

Download the ISO and its SHA-256 checksum from the release assets. Write the ISO using an image-writing tool; copying extracted source files onto USB does not make it bootable. Source archives contain the builder and desktop code. No Apple ROM, OS image or application is bundled.
