FROM debian:trixie-slim
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
 live-build debootstrap debian-archive-keyring ca-certificates xorriso squashfs-tools \
 dosfstools mtools isolinux syslinux syslinux-common syslinux-utils grub-pc-bin grub-efi-amd64-bin \
 grub-efi-amd64-signed shim-signed python3 file && apt-get clean
CMD ["bash"]
