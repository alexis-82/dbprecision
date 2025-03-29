<div align="center">

# 🎚️ dBPrecision

<img src="https://img.shields.io/badge/versione-1.0-blue">

</div>

**dBPrecision** è un'applicazione professionale per normalizzare il volume dei file MP3 mantenendo la qualità audio originale e tutti i metadati, incluse le immagini di copertina.

<p align="center">
  <img src="https://i.postimg.cc/d0Xq1kyX/dbprecision.png" alt="Logo dBPrecision" width="150">
</p>

## ✨ Caratteristiche

- 🔊 **Normalizzazione professionale** dei file MP3
- 🖼️ **Conservazione completa dei metadati** (incluse le immagini)
- 📁 Elaborazione di **file singoli o intere cartelle**
- 📊 **Analisi audio** dettagliata prima della normalizzazione
- 🖥️ **Interfaccia grafica intuitiva** multipiattaforma
- 🔄 **Elaborazione in batch** di più file MP3

## 📋 Requisiti di Sistema

### Per tutte le piattaforme
- Python 3.6 o superiore
- PyQt6
- mutagen
- numpy
- ffmpeg (installato automaticamente su Windows, richiede patch su Linux)

## 🚀 Installazione

### Windows
1. Clona o scarica questo repository
2. Installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```
3. Esegui l'applicazione:
   ```
   python main.py
   ```
4. L'applicazione installerà automaticamente ffmpeg al primo utilizzo

### Linux
1. Clona o scarica questo repository
2. Installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```
3. Esegui l'applicazione dal menu applicazioni o con il comando:
   ```
   python3 main.py
   ```

## 🎯 Utilizzo

1. **Seleziona i file MP3** utilizzando "Seleziona File MP3" per file singoli o "Seleziona Cartella" per elaborare intere cartelle
2. **Analizza i file** con il pulsante "Analizza" per ottenere informazioni dettagliate sul livello audio
3. **Normalizza i file** con il pulsante "Normalizza" per equalizzare il volume mantenendo la qualità originale
4. I file normalizzati verranno salvati con un suffisso "_normalized" per impostazione predefinita

<p align="center">
  <img src="https://i.postimg.cc/T3fdMXz7/dbprecision.webp" alt="Screenshot dell'applicazione" width="600">
  <br>
  <em>Screenshot dell'interfaccia di dBPrecision</em>
</p>

## ⌨️ Scorciatoie da Tastiera

- **Ctrl+F**: Seleziona file MP3
- **Ctrl+D**: Seleziona cartella
- **Ctrl+A**: Analizza i file MP3
- **Ctrl+N**: Normalizza i file MP3
- **Ctrl+R**: Cancella la lista dei file
- **Ctrl+Q**: Esci dall'applicazione

## 🔧 Risoluzione dei Problemi

### Windows
- Se l'applicazione non riesce a scaricare ffmpeg automaticamente, puoi scaricarlo manualmente da [ffmpeg.org](https://ffmpeg.org/download.html)

### Linux
- Se l'icona dell'applicazione non appare nel menu, riavvia la sessione di desktop o esegui:
  ```
  sudo update-desktop-database
  ```

## 📝 Note

dBPrecision è progettato per offrire una normalizzazione audio professionale preservando la massima qualità del suono originale.

## 🤝 Contributi

Per contribuire al progetto o segnalare problemi, contatta l'autore.

## 📜 Licenza

Copyright 2025 dBPrecision. Tutti i diritti riservati.

---

<p align="center">
  <a href="https://dbsp.io">https://dbsp.io</a>
</p>
