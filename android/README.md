# Slipway Android app (APK wrapper) - experimental

This is a thin Android shell around the web app at https://discodave-glitch.github.io/slipway/app/
(a Trusted Web Activity, using Google's androidbrowserhelper). It needs Chrome installed and an internet
connection, and it opens the same page, so Web MIDI, the firmware list and the stock-first rules are exactly the
same as in Chrome. It has **not** been tested yet.

Build it: GitHub -> Actions -> "Build Android app (APK)" -> Run workflow. The APK is saved on the run page under
Artifacts (Slipway-apk). Each build is signed with a fresh key, so to install a newer build you must uninstall
the old one first. Installing needs "Install unknown apps" allowed for the app you open the file from.

Without a Digital Asset Links file on discodave-glitch.github.io the app shows a small Chrome address bar at the
top; it still works.
