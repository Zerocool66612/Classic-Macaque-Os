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

## Installer password check workaround

If this ISO rejects passwords with a dictionary-check message before installation begins, close the installer and run the following in the live Macaque Terminal, then reopen Install Macaque Classic:

```bash
sudo python3 -c 'from pathlib import Path; import yaml; p=Path("/etc/calamares/modules/users.conf"); d=yaml.safe_load(p.read_text()); d["passwordRequirements"]={"minLength":8,"maxLength":128}; p.write_text(yaml.safe_dump(d,sort_keys=False))'
```

Choose a password of 8–128 characters and enter the same password in both fields. This changes only Calamares validation in the live session, not the system PAM password policy. Current source applies the correction to future builds; the already-built 0.30.4 ISO still needs this live-session workaround. Passwords are never included in the command.
