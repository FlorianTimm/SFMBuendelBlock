# Bündelblockausgleichung zur Vorbereitung von SFM

Structure-from-Motion bietet die Möglichkeit mit einfachsten (Hardware-)Mitteln 3D-Modelle bzw. farbige Punktwolken zu erzeugen. Die meisten, vorallem die Open-Source-Lösungen nutzen hierbei die Automatische Detektion von Verknüpfungspunkten. Das Setzen des Maßstabes oder von anderen festen Bedingungen ist hier nicht möglich. Es werden maximal die GNSS-Koordinaten des Bildes und ggf. die Ausrichtung aus den EXIF-Daten der Bilder genutzt. 

Zur Verbesserung des Matchings von Punkten ist es daher geplant, ein Tool zu entwickeln, mit dem das manuelle Erzeugen von Passpunkten möglich ist. Außerdem sollen auch vor Ort angebrachte Arurco-Marker erkannt und verwendet werden, um den Aufwand der Nachbearbeitung zu verkleinern. Eine Angabe von Abständen zwischen zweier Verknüpfungspunkte bzw. das Setzen von Nebenbedingungen, wie z.B. das zwei Punkte  übereinander liegen, die gleiche Höhe haben oder die X-Achse bilden, sind weitere Erweiterungsideen. Die ausgeglichen Daten sollen dann den EIngangsbildern als EXIF-Tags angehängt werden. So wird eine Weiterverarbeitung in verschiedensten Softwarepaketen (OpenDroneMap, VisualSFM, Agisoft MetaShape) ermöglicht.

## Geplante Python-Pakete

* OpenCV
* Numpy
* Qt
* Sympy
* Scipy

## Durchführung

### Anlegen von Verknüpfungspunkten

Es soll eine grafische Benutzeroberfläche geschaffen werden, die das Setzen von Passpunkten ermöglicht. Diese soll mit Qt oder Tk erzeugt werden. Alternativ könnte auch eine Weboberfläche erzeugt werden.

### Erkennen von Aruco-Markern

OpenCV bietet die Möglichkeit, Aruco-Marker zu finden und zu identifizieren. Dies wurde bereits mit einem Testdatensatz ausprobiert und funktioniert.

### Nebenbedingungen für die Ausgleichung

Er soll die Möglichkeit geschaffen werden, Nebenbedingungen festzulegen. Dies könnte beispielsweise per Konfiguratonsdatei oder in der grafischen Benutzeroberfläche ermöglicht werden.

### Bündelblockausgleichung

Es soll in Numpy mit Zuhilfenahme von Sympy (Ableitungen von Funktionen) eine Bündelblockausgleichung gerechnet werden. Grobe Fehler in den Passpunkten sollten erkennbar werden. Ein Ansatz wurde testweise erzeugt, bisherige Versuche der Ausgleichung scheiterten an Rechenfehlern oder zu großen Datenmengen.

### Schreiben von EXIF-Daten

Das Ergebnis soll als EXIF-Daten abgelegt werden. Außerdem evtl. in entsprechenden Datenformaten, mit den OpenSFM, OpenDroneMap oder MetaShape arbeiten können.
