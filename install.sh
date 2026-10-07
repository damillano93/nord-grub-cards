#!/bin/bash
# Installs the theme into /usr/share/grub/themes and enables it in /etc/default/grub.
set -euo pipefail
[ "$EUID" -eq 0 ] || { echo "run with sudo"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -f "$HERE/theme/theme.txt" ] || { echo "theme/ missing: run 'python3 build.py' first"; exit 1; }

DEST=/usr/share/grub/themes/nord-cards
rm -rf "$DEST"; mkdir -p "$DEST"
cp -r "$HERE"/theme/* "$DEST"/
chmod -R a+rX "$DEST"

cp /etc/default/grub "/etc/default/grub.bak-$(date +%s)"
if grep -q '^GRUB_THEME=' /etc/default/grub; then
    sed -i "s|^GRUB_THEME=.*|GRUB_THEME=\"$DEST/theme.txt\"|" /etc/default/grub
else
    echo "GRUB_THEME=\"$DEST/theme.txt\"" >> /etc/default/grub
fi
if grep -q '^GRUB_GFXMODE=' /etc/default/grub; then
    sed -i 's|^GRUB_GFXMODE=.*|GRUB_GFXMODE=1080x1920,auto|' /etc/default/grub
else
    echo 'GRUB_GFXMODE=1080x1920,auto' >> /etc/default/grub
fi

if command -v update-grub >/dev/null; then update-grub; else grub-mkconfig -o /boot/grub/grub.cfg; fi
echo "Done. Reboot to see it. Previous settings saved as /etc/default/grub.bak-*"
