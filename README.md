# Quick Start Guide
Um das Projekt in Betrieb zunehmen sind ein Raspberry Pi (min. 3.Generation), ein MPU6050 Beschleunigungssensor, und ein USB-Mikrofon erforderlich.
## 1. Schritt
Als erstes muss die Hardware gemäß folgendem Bild angeschlossen werden:
![image](https://user-images.githubusercontent.com/8748052/217887944-113fb95c-6dc0-466d-9ec7-e0cd19fd9d04.png)

## 2.Schritt
Als nächstes muss das Projekt auf dem Raspberry entpackt werden.
Ausserdem muss unser Fork der MPU Bibliothek als submodul mittels dem befehl ``git submodule init`` initialisiert werden. 
Sind diese beiden Dinge erledigt, müssen zuletzt noch die Bibliotheken installiert werden, dies geschieht durch ausführen des Skripts „Dependencies.sh“.
Jetzt kann das Skript mit ``python T-UGS.py`` gestartet werden, um den Detektor zu starten.
