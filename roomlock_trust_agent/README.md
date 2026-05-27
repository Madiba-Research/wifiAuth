# RoomLock Trust Agent

This folder contains a minimal Android `TrustAgentService` plus a Magisk module template.

RoomLock is fully local. It does not use HTTP or Flask. Registration collects 20 Wi-Fi scans, authentication collects 4 Wi-Fi scans, runs the authApp GNN encoder locally, and grants Android trust only when the local RoomLock verifier passes.

## Why this has to be a privileged app

Android's `TrustManagerService` only accepts services that:

- Resolve the `android.service.trust.TrustAgentService` intent.
- Belong to a package granted `android.permission.PROVIDE_TRUST_AGENT`.
- Run as a system or privileged app when discovered by PackageManager.

The Magisk module installs the APK at:

```text
/system/priv-app/RoomLock/RoomLock.apk
```

and overlays the privileged permission allowlist at:

```text
/system/etc/permissions/privapp-permissions-roomlock.xml
```

It also overlays a hidden API whitelist:

```text
/system/etc/sysconfig/roomlock-hiddenapi-whitelist.xml
```

This matters because `TrustAgentService` is not part of the public app SDK on many builds.

## Build

Open this folder in Android Studio:

```text
roomlock_trust_agent
```

Then run:

```text
Gradle panel -> RoomLockTrustAgent -> app -> Tasks -> build -> assembleRelease
```

or build from the Android Studio terminal:

```bash
./gradlew :app:assembleRelease
./scripts/package_magisk.sh
```

If Android Studio has not created a Gradle wrapper for this folder yet, use Android Studio's Gradle panel or run an installed Gradle:

```bash
gradle :app:assembleRelease
./scripts/package_magisk.sh
```

Android Studio can also add a wrapper from its Gradle tooling. After that, `./gradlew :app:assembleRelease` will work from this folder.

The release build is signed with the debug key on purpose. A system privileged app still needs a valid APK signature, but it does not need to be platform-signed for `signature|privileged` permissions when the privileged allowlist grants them.

The Magisk zip will be written to:

```text
build/roomlock_trust_agent_magisk.zip
```

## Install and verify

1. Install the generated zip in Magisk.
2. Reboot.
3. Open the RoomLock app and grant Wi-Fi/location permissions.
4. Tap `Register RoomLock` and wait for `RoomLock profile is registered.` It collects 20 scans, so this takes about 50 seconds.
5. Confirm the package is treated as a system package:

```bash
adb shell pm path com.roomlock.trust
adb shell dumpsys package com.roomlock.trust | grep -E "pkgFlags|privFlags|PROVIDE_TRUST_AGENT"
```

6. Confirm Android can resolve the trust agent service:

```bash
adb shell cmd package resolve-service --user 0 --brief -a android.service.trust.TrustAgentService com.roomlock.trust
```

7. Open Android settings and enable `RoomLock` under Trust agents.

On many builds the path is:

```text
Settings -> Security and privacy -> More security settings -> Trust agents
```

The module intentionally does not force-enable itself. RoomLock should appear as an available trust agent, and you enable it from Android settings.

After enabling it, unlock once with PIN/pattern/password. Trust agents are normally ignored until strong authentication has happened at least once after boot or lockdown.

RoomLock authentication runs from `RoomLockTrustAgentService`: it collects 4 Wi-Fi scans, runs the local verifier, and calls `grantTrust()` only on success.

## Known constraints

- This does not replace the lockscreen credential. It only participates in Android's trust-agent/extend-unlock flow.
- Some OEM builds hide or restrict third-party trust agents even when privileged.
- Wi-Fi scans require location services to be enabled. Android may throttle active scans; the implementation still reads the latest cached scan results so the demo can complete.
- If `RoomLock` does not appear, check logcat for `TrustManagerService` messages about missing `PROVIDE_TRUST_AGENT`.
- If it appears but does not grant trust, first register RoomLock, unlock once manually, and then watch:

```bash
adb logcat -s RoomLockTrustAgent TrustManagerService TrustAgentWrapper
```
