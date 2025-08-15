# GitHub Release Checklist

## Pre-Release Steps

1. **Update Version Numbers**
   - [ ] Update version in `debian/DEBIAN/control`
   - [ ] Update version in `build-deb.sh`
   - [ ] Update version in `CHANGELOG.md`
   - [ ] Update version in `RELEASE_NOTES.md`

2. **Test the Package**
   - [ ] Build the .deb package: `./build-deb.sh`
   - [ ] Test installation: `sudo dpkg -i rdp2gui_1.0.0_all.deb`
   - [ ] Test the application runs correctly
   - [ ] Test uninstallation: `sudo dpkg -r rdp2gui`

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "Prepare for v1.0.0 release"
   git push origin main
   ```

## Creating the Release

### Option 1: Manual GitHub Release

1. Go to https://github.com/rjeffmyers/rdp2gui/releases
2. Click "Create a new release"
3. Create a new tag: `v1.0.0`
4. Release title: `RDP2GUI v1.0.0`
5. Copy contents from `RELEASE_NOTES.md` to the description
6. Upload the `.deb` file: `rdp2gui_1.0.0_all.deb`
7. Check "Set as the latest release"
8. Click "Publish release"

### Option 2: Automated Release (using GitHub Actions)

1. Create and push a tag:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. The GitHub Action will automatically:
   - Build the .deb package
   - Create a GitHub release
   - Upload the package as a release asset

## Post-Release

1. **Verify the Release**
   - [ ] Check the release page
   - [ ] Download and test the .deb package
   - [ ] Verify all links work

2. **Update Documentation** (if needed)
   - [ ] Update installation instructions
   - [ ] Update any screenshots
   - [ ] Update wiki (if applicable)

## Release Assets

The following files are included in the release:
- `rdp2gui_1.0.0_all.deb` - Debian package for easy installation
- Source code (automatically included by GitHub)

## Download Links

After release, users can download from:
- Direct: `https://github.com/rjeffmyers/rdp2gui/releases/download/v1.0.0/rdp2gui_1.0.0_all.deb`
- Release page: `https://github.com/rjeffmyers/rdp2gui/releases/latest`