---
layout: post
type: note
title: Running MacOS on VMware Fusion
alias: macos
---

## 1. Get MacOS Installer

References:
- https://dortania.github.io/OpenCore-Install-Guide/installer-guide/mac-install-pkg.html
- https://osxdaily.com/2020/07/20/how-convert-macos-installer-iso/

### i. Download the desired version

There are links to download from the App Store at https://support.apple.com/en-us/HT211683. For example, I want to download Catalina.

If it mentions that the version is not suitable to be installed, it doesn't really matter. The important thing is **/Applications** contains a file called **Install macOS Catalina.app** (or other version).

Alternatively, an installer can be downloaded with Munki's InstallMacOS utility (but I didn't try this)

```sh
mkdir -p ~/macOS-installer && cd ~/macOS-installer && curl https://raw.githubusercontent.com/munki/macadmin-scripts/main/installinstallmacos.py > installinstallmacos.py && sudo python installinstallmacos.py
```

### ii. Set up the installer

Using either method in the previous step, there should be a **Install macOS \<version\>.app** file.

With Catalina as an example, run the following commands.

1. Create a DMG disk image
```sh
hdiutil create -o /tmp/Catalina -size 8500m -volname Catalina -layout SPUD -fs HFS+J
```

2. Mount the disk image
```sh
hdiutil attach /tmp/Catalina.dmg -noverify -mountpoint /Volumes/Catalina
```

3. Use `createinstallmedia` utility to create the installer on the mounted volume
```sh
sudo /Applications/Install\ macOS\ Catalina.app/Contents/Resources/createinstallmedia --volume /Volumes/Catalina --nointeraction
```

4. Once `createinstallemdia` has finished, unmount the volume
```sh
hdiutil detach /Volumes/Install\ macOS\ Catalina
```

5. Convert the DMG disk image to CDR
```sh
hdiutil convert /tmp/Catalina.dmg -format UDTO -o ~/Desktop/Catalina.cdr
```

6. Rename ISO to CDR
```sh
mv ~/Desktop/Catalina.cdr ~/Desktop/Catalina.iso
```

Done!

## 2. Install macOS in VMware Fusion

1. Create new VM
1. Install from disc or image
1. Select .iso file created earlier
1. Follow installation steps
1. Wait 20 mins maybe

Simples.

## 3. Disable System Integrity Protection (SIP)

References:
- https://www.virtual-odyssey.com/2017/10/23/disable-sip-within-osx-virtual-machine/#:~:text=At%20the%20terminal%20screen%20type,that%20SIP%20is%20indeed%20disabled.

It is best to disable SIP when doing security research. Otherwise, there are some security settings that will make life inconvenient.

To disable SIP, the installer ISO will be used again. (By default, it is still mounted onto the CD/DVD drive, so nothing needs to be done.)

1. Find the Settings button of VMware Fusion
1. Choose `Startup Disk`
1. Choose `CD/DVD` and click `Restart`

The VM will now restart and boot into the ISO used earlier.

1. At the top bar, `Utility`->`Terminal`
1. Enter `csrutil disable` in the terminal

Now, it is time to restart back to the system. Similar to earlier,

1. Find the Settings button of VMware Fusion
1. Choose `Startup Disk`
1. Choose `Hard Disk (SATA)` and click `Restart`

In the VM, open a terminal and enter `csrutil status` to see that SIP has been disabled.