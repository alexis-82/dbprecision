import os
import sys
import subprocess
import tempfile
import shutil
import zipfile
import json
import requests
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QAction, QIcon
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import array  # Per la lettura dei dati audio
import wave   # Per la lettura dei file WAV
import numpy as np  # Per il calcolo matematico

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Informazioni su dBPrecision")
        self.setFixedSize(400, 250)
        
        layout = QVBoxLayout()
        
        title = QLabel("<h2>dBPrecision</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        description = QLabel(
            "<p>Versione: 1.0</p>"
            "<p>Applicazione per normalizzare il volume dei file MP3 mantenendo la qualità audio originale "
            "e tutti i metadati (incluse le immagini).</p>"
            "<p>Per ulteriori informazioni, visita il sito web: https://dbsp.io</p>"
            "<p>Realizzato da: Alessio Abrugiati</p>"
            "<p>Copyright 2025 dBPrecision. Tutti i diritti riservati.</p>"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        self.setLayout(layout)

class MP3Normalizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # Imposta il focus policy per evitare che la finestra principale riceva focus e input
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Imposta l'attributo Qt.WA_TransparentForMouseEvents per impedire eventi del mouse sulla finestra principale
        # ma questo potrebbe influire anche sui widget figli, quindi non lo usiamo
        
        # Imposta la finestra come non focalizzabile da mouse
        self.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        
    def keyPressEvent(self, event):
        # Sovrascrive l'evento di pressione tasti per ignorare l'input da tastiera
        # nella finestra principale, ma permette che funzioni nei widget come i pulsanti
        event.ignore()
        
    def mousePressEvent(self, event):
        # Sovrascrive l'evento di clic del mouse per evitare che la finestra principale prenda il focus
        # I widget figli (pulsanti, ecc.) continueranno a ricevere eventi mouse normalmente
        self.clearFocus()
        super().mousePressEvent(event)

    def initUI(self):
        self.setWindowTitle('dBPrecision')
        self.setWindowIcon(QIcon("icons/dbprecision.png"))
        self.setGeometry(100, 100, 800, 600)  
        
        # Creazione della barra dei menu
        menubar = self.menuBar()
        
        # Determina il colore di sfondo in base al sistema operativo
        if sys.platform.startswith('win'):
            # Windows - sfondo chiaro #f0f0f0
            menubar.setStyleSheet("""
                QMenuBar {
                    padding-top: 5px;
                    padding-bottom: 5px;
                    background-color: #f0f0f0;
                }
                QMenuBar::item {
                    padding: 5px 10px;
                    margin: 2px 0px;
                    background-color: #f0f0f0;
                }
            """)
        else:
            # Linux - sfondo scuro #3d3d3d (mantiene il colore originale)
            menubar.setStyleSheet("""
                QMenuBar {
                    padding-top: 5px;
                    padding-bottom: 5px;
                    background-color: #3d3d3d;
                }
                QMenuBar::item {
                    padding: 5px 10px;
                    margin: 2px 0px;
                    background-color: #3d3d3d;
                }
            """)
        
        # Menu File
        file_menu = menubar.addMenu('&File')
        
        select_file_action = QAction('Seleziona &File MP3...', self)
        select_file_action.setShortcut('Ctrl+F')
        select_file_action.triggered.connect(self.select_file)
        file_menu.addAction(select_file_action)
        
        select_folder_action = QAction('Seleziona &Cartella...', self)
        select_folder_action.setShortcut('Ctrl+D')
        select_folder_action.triggered.connect(self.select_folder)
        file_menu.addAction(select_folder_action)
        
        # Aggiungi azione per cancellare lista
        clear_list_action = QAction('&Cancella Lista File', self)
        clear_list_action.setShortcut('Ctrl+R')
        clear_list_action.triggered.connect(self.clear_file_list)
        file_menu.addAction(clear_list_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('&Esci', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Strumenti
        tools_menu = menubar.addMenu('&Strumenti')
        
        analyze_action = QAction('&Analizza File MP3', self)
        analyze_action.setShortcut('Ctrl+A')
        analyze_action.triggered.connect(self.analyze_mp3_files)
        tools_menu.addAction(analyze_action)
        
        normalize_action = QAction('&Normalizza File MP3', self)
        normalize_action.setShortcut('Ctrl+N')
        normalize_action.triggered.connect(self.normalize_mp3_files)
        tools_menu.addAction(normalize_action)
        
        # Menu Tools (per Windows)
        tools_en_menu = menubar.addMenu('&Sistema')
        
        # Sottomenu per ffmpeg
        ffmpeg_menu = QMenu('Windows', self)
        tools_en_menu.addMenu(ffmpeg_menu)
        
        # Aggiungi azione per il controllo e download di ffmpeg
        check_ffmpeg_action = QAction('Download ffmpeg', self)
        check_ffmpeg_action.triggered.connect(self.check_ffmpeg)
        ffmpeg_menu.addAction(check_ffmpeg_action)
        
        # Sottomenu per linux
        linux_menu = QMenu('Linux', self)
        tools_en_menu.addMenu(linux_menu)
        
        # Aggiungi azione per l'installazione della patch
        install_patch_action = QAction('Installa patch', self)
        install_patch_action.triggered.connect(self.install_linux_patch)
        linux_menu.addAction(install_patch_action)
        
        # Menu Aiuto
        help_menu = menubar.addMenu('&Aiuto')
        
        about_action = QAction('&Informazioni...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Aggiungi padding (spazio) in alto e in basso
        layout.setContentsMargins(10, 20, 10, 20)  # Sinistra, Alto, Destra, Basso
        layout.setSpacing(10)  # Spazio tra gli elementi
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        
        # Imposta il widget centrale come non focalizzabile
        main_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Definisci stile comune per i pulsanti
        button_style = "padding: 5px 15px; font-weight: bold;"
        button_height = 32  # Altezza fissa per tutti i pulsanti

        # Layout per selezione file/cartella
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('Seleziona una cartella o un file MP3')
        
        # Pulsante per selezionare file singolo
        select_file_btn = QPushButton('Seleziona File MP3')
        select_file_btn.clicked.connect(self.select_file)
        select_file_btn.setStyleSheet(button_style)
        select_file_btn.setFixedHeight(button_height)
        
        # Pulsante per selezionare cartella
        select_folder_btn = QPushButton('Seleziona Cartella')
        select_folder_btn.clicked.connect(self.select_folder)
        select_folder_btn.setStyleSheet(button_style)
        select_folder_btn.setFixedHeight(button_height)
        
        # Pulsante per cancellare la lista
        clear_list_btn = QPushButton('Cancella Lista')
        clear_list_btn.clicked.connect(self.clear_file_list)
        clear_list_btn.setStyleSheet(button_style)
        clear_list_btn.setFixedHeight(button_height)
        
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(select_file_btn)
        folder_layout.addWidget(select_folder_btn)
        folder_layout.addWidget(clear_list_btn)
        layout.addLayout(folder_layout)

        db_layout = QHBoxLayout()
        self.db_label = QLabel('Livello di Normalizzazione: -20 dB')
        self.db_slider = QSlider(Qt.Orientation.Horizontal)
        self.db_slider.setMinimum(-40)
        self.db_slider.setMaximum(0)
        self.db_slider.setValue(-20)
        self.db_slider.valueChanged.connect(self.update_db_label)
        db_layout.addWidget(self.db_label)
        db_layout.addWidget(self.db_slider)
        layout.addLayout(db_layout)
        
        # Aggiungi opzioni per preservare la qualità
        quality_main_layout = QVBoxLayout()  # Layout verticale principale
        
        # Layout orizzontale per gli elementi della qualità
        quality_controls_layout = QHBoxLayout()
        quality_controls_layout.setContentsMargins(0, 0, 0, 0)  # Margine superiore di 10px
        
        # Etichetta e slider per la qualità di codifica
        quality_label = QLabel('Qualità codifica:')
        quality_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        quality_label.setStyleSheet("margin-top: 0px;")  # Spostare verso il basso
        
        # Crea un contenitore per l'etichetta con margine
        label_container = QWidget()
        label_layout = QVBoxLayout(label_container)
        label_layout.setContentsMargins(0, 0, 0, 0)  # Rimuovere i margini
        label_layout.addWidget(quality_label)
        
        quality_controls_layout.addWidget(label_container)
        
        # Imposta il layout per allineare verticalmente al centro
        quality_controls_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(0)
        self.quality_slider.setMaximum(2)  # Solo 3 posizioni: 0, 1, 2
        self.quality_slider.setValue(2)    # Valore predefinito: Alta qualità
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(1)
        self.quality_slider.setPageStep(1)
        self.quality_slider.setSingleStep(1)
        self.quality_slider.setEnabled(False)  # Disabilitato quando si usa bitrate originale
        self.quality_slider.valueChanged.connect(self.update_quality_label)
        # Crea un contenitore per lo slider con margine superiore
        slider_container = QWidget()
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setContentsMargins(0, 12, 0, 0)  # Aggiungi margine superiore allo slider
        slider_layout.addWidget(self.quality_slider)
        quality_controls_layout.addWidget(slider_container)
        
        self.quality_value_label = QLabel('Alta (320k)')  # Aggiornato per riflettere il valore predefinito dello slider
        self.quality_value_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        quality_controls_layout.addWidget(self.quality_value_label)

        # Aggiungi il layout orizzontale al layout verticale principale
        quality_main_layout.addLayout(quality_controls_layout)
        
        # Checkbox per mantenere bitrate originale (sotto alla riga della qualità)
        self.keep_bitrate_checkbox = QCheckBox('Mantieni bitrate originale')
        self.keep_bitrate_checkbox.setChecked(True)
        quality_main_layout.addWidget(self.keep_bitrate_checkbox)
        
        # Collega il checkbox alla funzione che abilita/disabilita lo slider
        self.keep_bitrate_checkbox.stateChanged.connect(self.toggle_quality_slider)
        
        layout.addLayout(quality_main_layout)

        buttons_layout = QHBoxLayout()
        
        analyze_btn = QPushButton('Analizza File MP3')
        analyze_btn.clicked.connect(self.analyze_mp3_files)
        analyze_btn.setStyleSheet(button_style)
        analyze_btn.setFixedHeight(button_height)
        buttons_layout.addWidget(analyze_btn)
        
        normalize_btn = QPushButton('Normalizza File MP3')
        normalize_btn.clicked.connect(self.normalize_mp3_files)
        normalize_btn.setStyleSheet(button_style)
        normalize_btn.setFixedHeight(button_height)
        buttons_layout.addWidget(normalize_btn)
        
        layout.addLayout(buttons_layout)

        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)  # Aggiungi colonna per bitrate
        self.files_table.setHorizontalHeaderLabels(['File MP3', 'Valore dB', 'Bitrate', 'Stato'])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.files_table.setMinimumHeight(200)
        
        # Imposta la tabella in modalità sola lettura
        self.files_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Imposta le intestazioni come non modificabili e non selezionabili
        self.files_table.horizontalHeader().setSectionsClickable(True)  # Mantiene cliccabile per l'ordinamento
        self.files_table.horizontalHeader().setDefaultSectionSize(120)
        
        # Imposta il comportamento di selezione della tabella
        self.files_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.files_table)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        layout.addWidget(self.log_area)
        
        # Aggiungi la barra di progresso
        progress_layout = QHBoxLayout()
        progress_label = QLabel('Progresso:')
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('%v/%m file - %p%')
        self.progress_bar.setValue(0)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # Aggiungi il pulsante Esci sotto alla barra di progresso
        exit_layout = QHBoxLayout()
        exit_layout.addStretch(1)  # Questo spinge il pulsante a destra
        
        exit_btn = QPushButton('Esci')
        exit_btn.setStyleSheet("background-color: red; color: white; " + button_style)
        exit_btn.clicked.connect(self.close)  # Chiude l'applicazione
        exit_btn.setFixedWidth(100)  # Larghezza fissa per il pulsante
        exit_btn.setFixedHeight(button_height)  # Stessa altezza degli altri pulsanti
        exit_layout.addWidget(exit_btn)
        
        layout.addLayout(exit_layout)

        # Inizializzazione variabili
        self.selected_folder = None
        self.selected_files = []  # Lista dei file selezionati
        self.is_single_file_mode = False  # Modalità file singolo o cartella

    def toggle_quality_slider(self, state):
        """Abilita o disabilita lo slider della qualità in base allo stato del checkbox"""
        self.quality_slider.setEnabled(not state)
        
    def update_quality_label(self):
        """Aggiorna l'etichetta che mostra il valore di qualità selezionato"""
        quality_value = self.quality_slider.value()
        # Mappa i valori dello slider a bitrate specifici
        if quality_value == 0:
            bitrate = 192
            quality_text = f"Bassa ({bitrate}k)"
        elif quality_value == 1:
            bitrate = 256
            quality_text = f"Media ({bitrate}k)"
        else:  # quality_value == 2
            bitrate = 320
            quality_text = f"Alta ({bitrate}k)"
        self.quality_value_label.setText(quality_text)

    def select_folder(self):
        # Utilizziamo opzioni speciali per permettere la selezione di unità intere
        dialog = QFileDialog(self)
        dialog.setWindowTitle('Seleziona una cartella o un\'unità')
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        # Rimuoviamo ShowDirsOnly per consentire la selezione di unità
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        
        if dialog.exec():
            folder = dialog.selectedFiles()[0]
            if folder:
                self.selected_folder = folder
                self.selected_files = []  # Resetta file selezionati
                self.is_single_file_mode = False
                self.folder_label.setText(f'Cartella selezionata: {folder}')
                self.log_area.append(f'Cartella selezionata: {folder}')
                
                # Riempi la tabella con i nomi dei file (senza analisi)
                mp3_files = self.get_mp3_files()
                self.files_table.setRowCount(len(mp3_files))
                
                for i, file_path in enumerate(mp3_files):
                    filename = os.path.basename(file_path)
                    self.files_table.setItem(i, 0, QTableWidgetItem(filename))
                    self.files_table.setItem(i, 1, QTableWidgetItem(''))  # Colonna volume vuota
                    self.files_table.setItem(i, 2, QTableWidgetItem(''))  # Colonna bitrate vuota
                    self.files_table.setItem(i, 3, QTableWidgetItem('In attesa di analisi'))
                
                # Aggiungi un messaggio
                self.log_area.append(f'Trovati {len(mp3_files)} file MP3. Premi "Analizza file MP3" per iniziare l\'analisi')

    def select_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Seleziona File MP3', '', 'File MP3 (*.mp3)')
        if files:
            # Aggiungi i nuovi file alla lista esistente invece di sostituirla
            self.selected_files.extend(files)
            
            # Rimuovi eventuali duplicati mantenendo l'ordine
            self.selected_files = list(dict.fromkeys(self.selected_files))
            
            self.selected_folder = None  # Resetta cartella selezionata
            self.is_single_file_mode = True
            
            if len(self.selected_files) == 1:
                self.folder_label.setText(f'Seleziona un file MP3 o una cartella')
            else:
                self.folder_label.setText(f'{len(self.selected_files)} file MP3 selezionati')
            
            # Riempi la tabella con i nomi dei file (senza analisi)
            self.files_table.setRowCount(len(self.selected_files))
            
            for i, file_path in enumerate(self.selected_files):
                filename = os.path.basename(file_path)
                self.files_table.setItem(i, 0, QTableWidgetItem(filename))
                self.files_table.setItem(i, 1, QTableWidgetItem(''))  # Colonna volume vuota
                self.files_table.setItem(i, 2, QTableWidgetItem(''))  # Colonna bitrate vuota
                self.files_table.setItem(i, 3, QTableWidgetItem('In attesa di analisi'))
                
            self.log_area.append(f'{len(files)} file MP3 aggiunti alla lista (totale: {len(self.selected_files)})')
            self.log_area.append('Premi "Analizza file MP3" per iniziare l\'analisi')

    def update_db_label(self):
        db_value = self.db_slider.value()
        self.db_label.setText(f'Livello di Normalizzazione: {db_value} dB')

    def get_mp3_files(self):
        """Restituisce la lista dei file MP3 da processare in base alla modalità selezionata"""
        if self.is_single_file_mode:
            return self.selected_files
        elif self.selected_folder:
            mp3_files = []
            # Normalizziamo il percorso dell'unità
            folder_path = self.selected_folder
            
            # Per semplificare, verifichiamo direttamente se il percorso è un'unità usando una regola più semplice
            # Un'unità ha la forma "X:" o "X:\" o "X:/"
            
            # FORZIAMO is_drive a True per testare
            is_drive = True
            
            # Normalizziamo il percorso sostituendo forward slash con backslash
            if '/' in folder_path:
                folder_path = folder_path.replace('/', '\\')
                self.log_area.append(f'Percorso normalizzato: {folder_path}')
            
            # Assicuriamoci che il percorso termini con \\
            if folder_path.endswith(':'):
                folder_path = folder_path + '\\'
            elif not folder_path.endswith(':\\'):
                # Se non termina già con ':\\', verifichiamo se è un'unità senza '\\'
                drive_part = os.path.splitdrive(folder_path)[0]
                if drive_part and len(drive_part) == 2:  # Se ha la forma "G:"
                    # Assicuriamoci che sia nella forma G:\
                    if not folder_path.endswith('\\'):
                        folder_path = drive_part + '\\'
            
            # Debug esteso
            # self.log_area.append(f'Drive part: {os.path.splitdrive(folder_path)[0]}')
            # self.log_area.append(f'Path part: {os.path.splitdrive(folder_path)[1]}')
                
            # Log per debugging
            # self.log_area.append(f'Cartella selezionata: {folder_path}')
            
            if is_drive:
                progress_dialog = QProgressDialog("Scansione in corso...", "Annulla", 0, 100, self)
                progress_dialog.setWindowTitle("Ricerca file MP3")
                progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                progress_dialog.setMinimumDuration(500)  # Mostra dopo 500ms
                progress_dialog.setValue(0)
                progress_dialog.show()
                
                # Conta file trovati per il progresso
                file_count = 0
                total_dirs_processed = 0
                skipped_dirs = []
                
                try:
                    self.log_area.append(f'Avvio scansione ricorsiva dell\'unità {folder_path} per trovare file MP3...')
                    # Usa os.walk per la scansione ricorsiva di tutte le directory
                    for root, dirs, files in os.walk(folder_path, topdown=True):
                        # Salta directory di sistema o nascoste per velocizzare
                        dirs[:] = [d for d in dirs if not d.startswith('$') and not d.startswith('.')]
                        
                        # Aggiorniamo l'interfaccia e verifichiamo se l'utente ha annullato
                        QApplication.processEvents()
                        if progress_dialog.wasCanceled():
                            self.log_area.append('Scansione annullata dall\'utente')
                            break
                        
                        # Aggiorna progresso ogni 10 directory
                        total_dirs_processed += 1
                        if total_dirs_processed % 10 == 0:
                            progress_dialog.setLabelText(f"Scansione in corso...\nDirectory: {total_dirs_processed}\nFile MP3 trovati: {file_count}")
                            progress_dialog.setValue(total_dirs_processed % 100)  # Valore circolare
                        
                        try:
                            # Filtra solo i file MP3
                            for file in files:
                                if file.lower().endswith('.mp3'):
                                    mp3_files.append(os.path.join(root, file))
                                    file_count += 1
                                    # Aggiorna ogni 20 file
                                    if file_count % 20 == 0:
                                        progress_dialog.setLabelText(f"Scansione in corso...\nDirectory: {total_dirs_processed}\nFile MP3 trovati: {file_count}")
                        except (PermissionError, OSError) as e:
                            skipped_dirs.append(root)
                            self.log_area.append(f'Errore di accesso alla directory {root}: {str(e)}')
                            continue
                            
                    self.log_area.append(f'Scansione completata: trovati {len(mp3_files)} file MP3 nell\'unità {folder_path}')
                    if skipped_dirs:
                        self.log_area.append(f'Saltate {len(skipped_dirs)} directory per problemi di permesso')
                except Exception as e:
                    self.log_area.append(f'Errore durante la scansione: {str(e)}')
                finally:
                    progress_dialog.close()
            else:
                # Comportamento originale per cartelle normali (non unità)
                try:
                    mp3_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]
                    self.log_area.append(f'Trovati {len(mp3_files)} file MP3 nella cartella {folder_path}')
                except (PermissionError, OSError) as e:
                    self.log_area.append(f'Errore di accesso alla cartella {folder_path}: {str(e)}')
            
            return mp3_files
        return []

    def normalize_mp3_files(self):
        mp3_files = self.get_mp3_files()
        
        if not mp3_files:
            self.log_area.append('Errore: Nessun file MP3 selezionato')
            return

        target_db = self.db_slider.value()
        self.log_area.append(f'Inizio normalizzazione a {target_db} dB')
        
        total_files = self.files_table.rowCount()
        self.progress_bar.setMaximum(total_files)
        self.progress_bar.setValue(0)

        for row in range(total_files):
            # Ottieni il percorso completo dal nome del file nella tabella
            filename = self.files_table.item(row, 0).text()
            file_path = None
            
            # Trova il percorso completo del file
            if self.is_single_file_mode:
                for path in self.selected_files:
                    if os.path.basename(path) == filename:
                        file_path = path
                        break
            else:
                file_path = os.path.join(self.selected_folder, filename)
            
            if not file_path or not os.path.exists(file_path):
                self.log_area.append(f'Errore: Impossibile trovare il file {filename}')
                continue
                
            self.files_table.setItem(row, 3, QTableWidgetItem('Normalizzazione in corso...'))
            temp_path = None
            
            try:
                # Crea un file temporaneo
                fd, temp_path = tempfile.mkstemp(suffix='.mp3')
                os.close(fd)  # Chiudi il descrittore di file
                temp_wav_path = temp_path.replace('.mp3', '.wav')
                input_wav_path = temp_path.replace('.mp3', '_input.wav')
                
                # Salva i metadati originali (inclusa l'immagine thumbnail)
                try:
                    original_tags = ID3(file_path)
                except:
                    original_tags = None
                
                # Ottieni informazioni sul bitrate originale se necessario
                original_bitrate = None
                if self.keep_bitrate_checkbox.isChecked():
                    try:
                        mp3_info = MP3(file_path)
                        original_bitrate = mp3_info.info.bitrate
                    except:
                        self.log_area.append(f"Avviso: impossibile determinare il bitrate di {filename}, verrà usato 320k")
                        original_bitrate = 320000  # Default a 320kbps se non rilevabile
                
                # Trova ffmpeg
                ffmpeg_path = self.find_ffmpeg_executable()
                if ffmpeg_path:
                    ffmpeg_cmd = ffmpeg_path
                else:
                    ffmpeg_cmd = 'ffmpeg'
                
                # Converti MP3 in WAV per l'analisi
                subprocess.run([ffmpeg_cmd, '-y', '-v', 'quiet', '-i', file_path, input_wav_path], check=True)
                
                # Leggi i dati audio usando wave
                with wave.open(input_wav_path, 'rb') as wav_file:
                    # Ottieni informazioni sul file
                    n_channels = wav_file.getnchannels()
                    sampwidth = wav_file.getsampwidth()
                    framerate = wav_file.getframerate()
                    n_frames = wav_file.getnframes()
                    
                    # Leggi tutti i frame
                    frames = wav_file.readframes(n_frames)
                    
                    # Converti i byte in valori numerici
                    if sampwidth == 2:  # 16-bit audio
                        fmt = f"{n_frames * n_channels}h"
                        samples = array.array('h', frames)
                        # Normalizza i valori tra -1 e 1
                        samples = [s / 32768.0 for s in samples]
                    elif sampwidth == 4:  # 32-bit audio
                        fmt = f"{n_frames * n_channels}i"
                        samples = array.array('i', frames)
                        # Normalizza i valori tra -1 e 1
                        samples = [s / 2147483648.0 for s in samples]
                    else:
                        samples = []
                
                # Calcola il valore dB RMS corrente
                if samples:
                    mean_square = sum(s*s for s in samples) / len(samples)
                    rms = np.sqrt(mean_square)
                    db_current = 20 * np.log10(rms + 1e-10)
                else:
                    raise Exception("Impossibile leggere i dati audio")
                
                # Calcola il guadagno necessario (in dB)
                gain = target_db - db_current
                
                # Applica il guadagno lineare
                gain_linear = 10 ** (gain / 20.0)
                normalized_samples = [s * gain_linear for s in samples]
                
                # Converti i valori normalizzati in bytes
                if sampwidth == 2:  # 16-bit audio
                    # Limita i valori tra -1 e 1 per evitare clipping
                    normalized_samples = [max(min(s, 1.0), -1.0) for s in normalized_samples]
                    # Converti da float a int16
                    int_samples = [int(s * 32767) for s in normalized_samples]
                    normalized_array = array.array('h', int_samples)
                elif sampwidth == 4:  # 32-bit audio
                    # Limita i valori tra -1 e 1 per evitare clipping
                    normalized_samples = [max(min(s, 1.0), -1.0) for s in normalized_samples]
                    # Converti da float a int32
                    int_samples = [int(s * 2147483647) for s in normalized_samples]
                    normalized_array = array.array('i', int_samples)
                
                # Scrivi il file WAV normalizzato
                with wave.open(temp_wav_path, 'wb') as wav_out:
                    wav_out.setnchannels(n_channels)
                    wav_out.setsampwidth(sampwidth)
                    wav_out.setframerate(framerate)
                    wav_out.writeframes(normalized_array.tobytes())
                
                # Prepara le opzioni per ffmpeg
                ffmpeg_options = []
                
                # Aggiungi le opzioni di bitrate o qualità
                if self.keep_bitrate_checkbox.isChecked() and original_bitrate:
                    # Converti da bit/sec a kbit/sec e arrotonda ai valori standard
                    bitrate_kbps = min(round(original_bitrate / 1000), 320)  # Limite massimo di 320kbps
                    ffmpeg_options.extend(['-b:a', f"{bitrate_kbps}k"])
                    self.log_area.append(f"Mantenendo bitrate originale: {bitrate_kbps}k per {filename}")
                else:
                    # Usa un bitrate fisso basato sul valore di qualità (invece di -q:a)
                    quality_value = self.quality_slider.value()
                    
                    # Mappa i valori dello slider a bitrate specifici
                    if quality_value == 0:
                        bitrate_kbps = 192  # Bassa qualità
                    elif quality_value == 1:
                        bitrate_kbps = 256  # Media qualità
                    else:  # quality_value == 2
                        bitrate_kbps = 320  # Alta qualità
                        
                    ffmpeg_options.extend(['-b:a', f"{bitrate_kbps}k"])
                    quality_text = "bassa" if quality_value == 0 else "media" if quality_value == 1 else "alta"
                    self.log_area.append(f"Usando qualità di codifica {quality_text} ({bitrate_kbps}k) per {filename}")
                
                # Converti da WAV a MP3 con ffmpeg
                try:
                    subprocess.run(
                        [ffmpeg_cmd, '-y', '-i', temp_wav_path, '-codec:a', 'libmp3lame'] + 
                        ffmpeg_options + [temp_path], 
                        check=True, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                    )
                    
                    # Rimuovi i file WAV temporanei
                    for wav_file in [temp_wav_path, input_wav_path]:
                        if os.path.exists(wav_file):
                            os.remove(wav_file)
                except subprocess.CalledProcessError as e:
                    raise Exception(f"Errore nella codifica MP3: {e}")
                
                # Ripristina i metadati originali (inclusa l'immagine thumbnail)
                if original_tags:
                    try:
                        # Copia tutti i tag ID3 originali nel nuovo file
                        new_tags = ID3(temp_path)
                        for key in original_tags.keys():
                            new_tags[key] = original_tags[key]
                        new_tags.save(temp_path)
                    except Exception as e:
                        self.log_area.append(f"Avviso: impossibile ripristinare i metadati per {filename}: {str(e)}")
                
                # Sovrascrivi il file originale
                shutil.move(temp_path, file_path)
                
                # Aggiorna la colonna di stato
                self.files_table.setItem(row, 3, QTableWidgetItem(f'Normalizzato (Target: {target_db} dB, Gain: {gain:.2f} dB)'))
                self.log_area.append(f'Normalizzato: {filename} -> {gain:.2f} dB')
            
            except Exception as e:
                self.files_table.setItem(row, 3, QTableWidgetItem(f'Errore: {str(e)}'))
                self.log_area.append(f'Errore con {filename}: {str(e)}')
                # Pulisci i file temporanei in caso di errore
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
                    os.remove(temp_wav_path)
                if 'input_wav_path' in locals() and os.path.exists(input_wav_path):
                    os.remove(input_wav_path)
                
            # Aggiorna la barra di progresso
            self.progress_bar.setValue(row + 1)
            QApplication.processEvents()  # Assicura che l'UI venga aggiornata

        self.log_area.append('Normalizzazione completata')

    def analyze_mp3_files(self):
        mp3_files = self.get_mp3_files()
        
        if not mp3_files:
            self.log_area.append('Errore: Nessun file MP3 selezionato')
            return
            
        self.log_area.append('Inizio analisi dei file MP3...')
        
        # Assicurati che la tabella abbia il corretto numero di righe (i file dovrebbero già essere nella tabella)
        # Non impostiamo più il numero di righe qui, poiché la tabella dovrebbe già essere stata riempita
        # dalla selezione dei file
        
        # Imposta la barra di progresso
        self.progress_bar.setMaximum(len(mp3_files))
        self.progress_bar.setValue(0)
        
        # Analizza ogni file e aggiorna i dati nella tabella
        for i, file_path in enumerate(mp3_files):
            filename = os.path.basename(file_path)
            
            # Aggiorna lo stato nella tabella
            self.files_table.setItem(i, 3, QTableWidgetItem('Analisi in corso...'))
            QApplication.processEvents()  # Assicura che l'UI venga aggiornata
            
            db_value = None
            
            try:
                # Trova ffmpeg
                ffmpeg_path = self.find_ffmpeg_executable()
                
                # Crea un file temporaneo WAV
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    tmp_wav = tmp_file.name
                
                # Converti MP3 in WAV con opzioni semplici
                if ffmpeg_path:
                    cmd = [ffmpeg_path, '-y', '-v', 'quiet', '-i', file_path, tmp_wav]
                    self.log_area.append(f'Utilizzo ffmpeg da: {ffmpeg_path}')
                else:
                    cmd = ['ffmpeg', '-y', '-v', 'quiet', '-i', file_path, tmp_wav]
                    self.log_area.append(f'Utilizzo ffmpeg dal PATH di sistema')
                
                subprocess.run(cmd, check=True)
                
                # Leggi il file WAV usando il modulo wave (molto più semplice di librosa)
                if os.path.exists(tmp_wav) and os.path.getsize(tmp_wav) > 0:
                    with wave.open(tmp_wav, 'rb') as wav_file:
                        # Ottieni informazioni sul file
                        n_channels = wav_file.getnchannels()
                        sampwidth = wav_file.getsampwidth()
                        n_frames = wav_file.getnframes()
                        
                        # Leggi tutti i frame
                        frames = wav_file.readframes(n_frames)
                        
                        # Converti i byte in valori numerici
                        if sampwidth == 2:  # 16-bit audio
                            fmt = f"{n_frames * n_channels}h"
                            samples = array.array('h', frames)
                            # Normalizza i valori tra -1 e 1
                            samples = [s / 32768.0 for s in samples]
                        elif sampwidth == 4:  # 32-bit audio
                            fmt = f"{n_frames * n_channels}i"
                            samples = array.array('i', frames)
                            # Normalizza i valori tra -1 e 1
                            samples = [s / 2147483648.0 for s in samples]
                        else:
                            samples = []
                        
                        if samples:
                            # Calcola il valore RMS
                            mean_square = sum(s*s for s in samples) / len(samples)
                            rms = np.sqrt(mean_square)
                            # Converti in dB
                            db_value = 20 * np.log10(rms + 1e-10)
                            self.log_area.append(f'File {filename} analizzato con successo')
                
                # Rimuovi il file temporaneo
                try:
                    os.unlink(tmp_wav)
                except:
                    pass
                
                # Mostra il valore dB originale effettivo
                if db_value is not None:
                    self.files_table.setItem(i, 1, QTableWidgetItem(f'{db_value:.2f} dB'))
                else:
                    self.files_table.setItem(i, 1, QTableWidgetItem('N/D'))
                
                # Analizza il bitrate
                try:
                    mp3_info = MP3(file_path)
                    bitrate_kbps = round(mp3_info.info.bitrate / 1000)
                    self.files_table.setItem(i, 2, QTableWidgetItem(f'{bitrate_kbps} kbps'))
                except:
                    self.files_table.setItem(i, 2, QTableWidgetItem('N/D'))
                
                self.files_table.setItem(i, 3, QTableWidgetItem('Pronto per la normalizzazione'))
                
            except Exception as e:
                self.files_table.setItem(i, 1, QTableWidgetItem('Errore'))
                self.files_table.setItem(i, 2, QTableWidgetItem('N/D'))
                self.files_table.setItem(i, 3, QTableWidgetItem(f'Errore: {str(e)}'))
                self.log_area.append(f'Errore durante l\'analisi di {filename}: {str(e)}')
            
            # Aggiorna la barra di progresso
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()  # Assicura che l'UI venga aggiornata
        
        self.log_area.append('Analisi completata')
    
    def find_ffmpeg_executable(self):
        """Trova il percorso dell'eseguibile ffmpeg."""
        # Prima cerca nella cartella del programma (Windows)
        if sys.platform == "win32":
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            ffmpeg_path = os.path.join(app_dir, "ffmpeg", "bin", "ffmpeg.exe")
            if os.path.exists(ffmpeg_path):
                return ffmpeg_path
        
        # Per Linux/macOS, cerca nella home dell'utente
        else:
            ffmpeg_path = os.path.join(os.path.expanduser("~"), "ffmpeg", "bin", "ffmpeg")
            if os.path.exists(ffmpeg_path):
                return ffmpeg_path
        
        # Quindi cerca nel PATH di sistema
        try:
            if sys.platform == "win32":
                # Su Windows, esegui where ffmpeg
                result = subprocess.run(['where', 'ffmpeg'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split('\n')[0]
            else:
                # Su Linux/macOS, esegui which ffmpeg
                result = subprocess.run(['which', 'ffmpeg'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
        except:
            pass
        
        # Se non è stato trovato, restituisci None
        return None

    def show_about(self):
        """Mostra la finestra di dialogo con le informazioni sull'applicazione"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    # Aggiunta nuova funzione per cancellare la lista di file
    def clear_file_list(self):
        # Verifica se ci sono file selezionati o se è stata selezionata una cartella/unità
        if self.selected_files or self.selected_folder:
            # Chiudi qualsiasi finestra di dialogo di progresso aperta
            # Cerca tutte le finestre di dialogo figlie di tipo QProgressDialog
            for widget in self.findChildren(QProgressDialog):
                if widget.isVisible():
                    self.log_area.append('Chiusura della finestra di progresso in corso...')
                    widget.close()
                    
            self.selected_files = []
            self.selected_folder = None
            self.is_single_file_mode = False
            self.folder_label.setText('Seleziona una cartella o un file MP3')
            self.files_table.setRowCount(0)
            self.log_area.append('Lista file cancellata')
            
            # Reset completo della barra di progresso
            self.progress_bar.reset()
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(1)  # Imposta a 1 invece di 0 per evitare il loop infinito
            QApplication.processEvents()  # Forza l'aggiornamento dell'interfaccia
        else:
            self.log_area.append('Nessun file da cancellare')

    def check_ffmpeg(self):
        """Scarica FFmpeg direttamente senza verificare se è già installato."""
        reply = QMessageBox.question(self, 
                                    "Download FFmpeg", 
                                    "Vuoi scaricare FFmpeg?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.download_ffmpeg()
            
    def download_ffmpeg(self):
        """Scarica FFmpeg da Internet."""
        import urllib.request
        import zipfile
        
        # Determina la cartella di destinazione prima di tutto
        if sys.platform == "win32":
            # Per Windows, la cartella ffmpeg va nella directory principale del software
            # Otteniamo il percorso del file eseguibile corrente
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            dest_dir = os.path.join(app_dir, "ffmpeg")
        else:
            # Per Linux e macOS, creiamo la cartella nella home dell'utente
            dest_dir = os.path.join(os.path.expanduser("~"), "ffmpeg")
        
        # Crea la cartella ffmpeg e la sua sottocartella bin prima di iniziare
        os.makedirs(dest_dir, exist_ok=True)
        os.makedirs(os.path.join(dest_dir, "bin"), exist_ok=True)
        
        # URL per il download di FFmpeg
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        
        # Crea una finestra di dialogo con barra di progresso
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Download FFmpeg")
        progress_dialog.setFixedSize(400, 100)
        layout = QVBoxLayout(progress_dialog)
        
        status_label = QLabel("Inizializzazione download...")
        layout.addWidget(status_label)
        
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)
        
        # Mostra la finestra di dialogo
        progress_dialog.show()
        QApplication.processEvents()
        
        try:
            # Cartella per il download temporaneo
            download_dir = os.path.join(os.path.expanduser("~"), "ffmpeg_download")
            os.makedirs(download_dir, exist_ok=True)
            
            # Percorso del file zip
            zip_path = os.path.join(download_dir, "ffmpeg.zip")
            
            # Funzione per aggiornare il progresso del download
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    # Calcola la percentuale di download completata
                    percent = min(100, int(block_num * block_size * 100 / total_size))
                    status_label.setText(f"Download in corso: {percent}% completato")
                    progress_bar.setValue(percent)
                    QApplication.processEvents()
            
            # Scarica il file con callback per il progresso
            status_label.setText("Download in corso...")
            QApplication.processEvents()
            urllib.request.urlretrieve(ffmpeg_url, zip_path, reporthook=report_progress)
            
            # Aggiorna il messaggio e resetta la barra di progresso per l'estrazione
            status_label.setText("Estrazione dei file in corso...")
            progress_bar.setValue(0)
            QApplication.processEvents()
            
            # Estrai il file zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Conta il numero totale di file nell'archivio
                total_files = len(zip_ref.namelist())
                extracted_files = 0
                
                # Estrai i file uno per uno, aggiornando il progresso
                for file in zip_ref.namelist():
                    zip_ref.extract(file, download_dir)
                    extracted_files += 1
                    percent = min(100, int(extracted_files * 100 / total_files))
                    progress_bar.setValue(percent)
                    if extracted_files % 10 == 0:  # Aggiorna solo ogni 10 file per performance
                        status_label.setText(f"Estrazione in corso: {percent}% completato")
                        QApplication.processEvents()
            
            # Cerca i file ffmpeg, ffprobe e ffplay all'interno della cartella estratta
            ffmpeg_files = []
            extracted_dir = None
            
            # Aggiorna stato
            status_label.setText("Individuazione dei file ffmpeg...")
            QApplication.processEvents()
            
            # Trova la directory principale estratta (di solito contiene una sola cartella con tutti i file)
            for item in os.listdir(download_dir):
                item_path = os.path.join(download_dir, item)
                if os.path.isdir(item_path) and item.startswith("ffmpeg"):
                    extracted_dir = item_path
                    break
            
            if extracted_dir:
                status_label.setText("Copia dei file in corso...")
                progress_bar.setValue(0)
                QApplication.processEvents()
                
                # Cerchiamo nella cartella bin all'interno della directory estratta
                bin_dir = os.path.join(extracted_dir, "bin")
                if os.path.exists(bin_dir):
                    # Conta il numero totale di file da copiare
                    bin_files = [f for f in os.listdir(bin_dir) if os.path.isfile(os.path.join(bin_dir, f))]
                    total_bin_files = len(bin_files)
                    copied_files = 0
                    
                    # Copia tutti i file dalla cartella bin alla cartella di destinazione
                    for file in bin_files:
                        src_file = os.path.join(bin_dir, file)
                        dest_file = os.path.join(dest_dir, "bin", file)
                        shutil.copy2(src_file, dest_file)
                        
                        # Se è un file eseguibile, aggiungi permessi di esecuzione su Linux/macOS
                        if sys.platform != "win32" and (file.startswith("ff") and not file.endswith(".txt")):
                            os.chmod(dest_file, 0o755)  # Aggiungi permessi di esecuzione
                        
                        ffmpeg_files.append(dest_file)
                        copied_files += 1
                        percent = min(100, int(copied_files * 100 / total_bin_files))
                        progress_bar.setValue(percent)
                        status_label.setText(f"Copia dei file in corso: {percent}% completato")
                        QApplication.processEvents()
                
                # Mostra un messaggio con le istruzioni appropriate
                if ffmpeg_files:
                    # Completato con successo
                    progress_bar.setValue(100)
                    status_label.setText("Installazione completata!")
                    QApplication.processEvents()
                    
                    if sys.platform == "win32":
                        msg = (
                            "FFmpeg è stato scaricato e installato in:\n"
                            f"{dest_dir}\n\n"
                            "I file ffmpeg sono stati installati nella cartella del programma."
                        )
                    else:
                        msg = (
                            "FFmpeg è stato scaricato e installato in:\n"
                            f"{dest_dir}\n\n"
                            "Per utilizzare FFmpeg globalmente, aggiungi questa cartella al tuo PATH:\n"
                            f"echo 'export PATH=\"$PATH:{os.path.join(dest_dir, 'bin')}\"' >> ~/.bashrc\n"
                            "e riavvia il terminale.\n\n"
                            "Oppure puoi utilizzare il percorso completo:\n"
                            f"{os.path.join(dest_dir, 'bin', 'ffmpeg')}"
                        )
                    progress_dialog.close()
                    QMessageBox.information(self, "Installazione completata", msg)
                else:
                    progress_dialog.close()
                    QMessageBox.warning(self, "Errore", "Impossibile trovare i file ffmpeg nel pacchetto scaricato.")
            else:
                progress_dialog.close()
                QMessageBox.warning(self, "Errore", "Impossibile trovare la cartella estratta di ffmpeg.")
            
            # Pulizia: rimuove il file zip scaricato e la cartella temporanea
            try:
                status_label.setText("Pulizia dei file temporanei...")
                QApplication.processEvents()
                
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                # Rimuoviamo i file temporanei di estrazione, ma manteniamo quelli nella destinazione finale
                if sys.platform == "win32":
                    # Su Windows può essere problematico rimuovere file in uso, usiamo shutil
                    shutil.rmtree(download_dir, ignore_errors=True)
                else:
                    for item in os.listdir(download_dir):
                        item_path = os.path.join(download_dir, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
            except Exception as e:
                print(f"Errore durante la pulizia: {str(e)}")
            
            # Chiude la finestra di dialogo del progresso se ancora aperta
            if progress_dialog.isVisible():
                progress_dialog.close()
            
        except Exception as e:
            # Assicurati che la finestra di dialogo sia chiusa in caso di errore
            if progress_dialog.isVisible():
                progress_dialog.close()
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore durante il download:\n{str(e)}")

    def install_linux_patch(self):
        if sys.platform.startswith('win'):
            QMessageBox.warning(self, 'Errore', 'Questa funzione è disponibile solo su sistemi Linux.')
            return
        
        try:
            # Salva il percorso assoluto del file di patch
            app_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(app_path, 'linux', 'patch')
            
            self.log_area.append(f'Installazione patch in corso da: {script_path}')
            
            # Esegui lo script con privilegi di amministratore
            # Passa esplicitamente il percorso completo come parametro extra
            process = subprocess.Popen(['pkexec', 'bash', script_path, app_path], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
        
            if process.returncode == 0:
                QMessageBox.information(self, 'Successo', 'Patch installata con successo!')
                self.log_area.append('Patch installata con successo!')
            else:
                error_msg = stderr.decode()
                self.log_area.append(f'Errore durante l\'installazione della patch: {error_msg}')
                QMessageBox.critical(self, 'Errore', f'Errore durante l\'installazione della patch:\n{error_msg}')
        except Exception as e:
            self.log_area.append(f'Errore: {str(e)}')
            QMessageBox.critical(self, 'Errore', f'Errore durante l\'installazione della patch:\n{str(e)}')

def main():
    app = QApplication(sys.argv)
    normalizer = MP3Normalizer()
    normalizer.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()