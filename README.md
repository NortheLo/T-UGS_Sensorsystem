# Quick Start Guide
Um dieses Projekt nachzubauen, benötigt man:  
  - Raspberry Pi (3rd oder 4rd Gen) mit Raspberry OS/Linux
  - MPU-6050 Beschleunigungssensor
  - USB Mikrofon

## 1. Schritt
Als Erstes muss die Hardware gemäß folgendem Bild angeschlossen werden:
![image](https://user-images.githubusercontent.com/8748052/217887944-113fb95c-6dc0-466d-9ec7-e0cd19fd9d04.png)

## 2. Schritt
Nun muss das Projekt auf dem Raspberry entpackt werden.
Ausserdem muss unser Fork der MPU Bibliothek als submodul mittels dem Befehl ``git submodule init`` initialisiert werden. 
Sind diese beiden Dinge erledigt, müssen zuletzt noch die Bibliotheken installiert werden, dies geschieht durch das Ausführen des Skripts mit ``./Dependencies.sh``.
Jetzt kann das Skript mit ``python T-UGS.py`` gestartet werden, um den Detektor zu starten.
