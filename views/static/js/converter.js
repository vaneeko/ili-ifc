document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed");
    const fileInput = document.getElementById('xtfFiles');
    const fileInfo = document.getElementById('file-info');
    const previewContainer = document.getElementById('preview-container');
    const convertBtn = document.getElementById('convertBtn');
    const alertContainer = document.getElementById('alert-container');
    const outputList = document.getElementById('output-list');
    const extractedDataContainer = document.getElementById('extracted-data');

    console.log("File input element:", fileInput);
    
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelection);
        console.log("File selection event listener added");
    } else {
        console.error("File input element not found");
    }

    fileInput.addEventListener('change', handleFileSelection);
    convertBtn.addEventListener('click', convertFiles);

    const themeButtons = document.querySelectorAll('.switch-theme-buttons button');
    themeButtons.forEach(button => {
        button.addEventListener('click', () => switchTheme(button.dataset.theme));
    });

    function handleFileSelection(e) {
        console.log("File selection event triggered");
        const files = e.target.files;
        if (files.length > 0) {
            console.log(`${files.length} file(s) selected`);
            fileInfo.textContent = `${files.length} Datei(en) ausgewählt`;
            previewContainer.innerHTML = '';
            
            Array.from(files).forEach(file => {
                const fileElement = document.createElement('div');
                fileElement.textContent = file.name;
                previewContainer.appendChild(fileElement);
            });
    
            console.log("Calling extractData function with all selected files");
            extractData(files);
        } else {
            console.log("No files selected");
            resetFileInfo();
        }
    }
    
    function extractData(files) {
        console.log(`Extracting data from ${files.length} file(s)`);
        const formData = new FormData();
        
        Array.from(files).forEach(file => {
            formData.append('xtfFile', file);
        });
        
        const configInputs = ['default_sohlenkote', 'default_durchmesser', 'default_hoehe', 'default_wanddicke', 'default_bodendicke', 'default_rohrdicke'];
        configInputs.forEach(input => {
            formData.append(input, document.getElementById(input).value);
        });
    
        formData.append('einfaerben', document.getElementById('einfaerben').checked);
    
        fetch('/extract', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("Data received from server:", data);
            displayExtractedData(data);
        })
        .catch(error => {
            console.error('Error:', error);
            extractedDataContainer.innerHTML = '<p>Fehler beim Extrahieren der Daten.</p>';
        });
    }

    function resetFileInfo() {
        fileInfo.textContent = 'Keine Dateien ausgewählt';
        previewContainer.innerHTML = '';
        extractedDataContainer.innerHTML = '';
    }

    function convertFiles() {
        const formData = new FormData();
        const files = fileInput.files;
        
        if (files.length === 0) {
            showAlert('Bitte wählen Sie mindestens eine XTF-Datei aus.', 'error');
            return;
        }

        Array.from(files).forEach(file => {
            formData.append('xtfFiles', file);
        });

        const configInputs = ['default_sohlenkote', 'default_durchmesser', 'default_hoehe', 'default_wanddicke', 'default_bodendicke', 'default_rohrdicke'];
        configInputs.forEach(input => {
            formData.append(input, document.getElementById(input).value);
        });

        formData.append('einfaerben', document.getElementById('einfaerben').checked);

        convertBtn.disabled = true;
        convertBtn.textContent = 'Converting...';

        fetch('/convert', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showAlert(data.error, 'error');
            } else {
                showAlert(data.message, 'success');
                displayDownloadLinks(data.downloadLinks);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.', 'error');
        })
        .finally(() => {
            convertBtn.disabled = false;
            convertBtn.textContent = 'Convert to IFC';
        });
    }

    function showAlert(message, type) {
        alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
        alertContainer.scrollIntoView({ behavior: 'smooth' });
    }

    function displayDownloadLinks(links) {
        outputList.innerHTML = '';
        links.forEach(link => {
            const linkElement = document.createElement('div');
            linkElement.innerHTML = `<a href="${link.url}" class="download-link" download>${link.filename}</a>`;
            outputList.appendChild(linkElement);
        });
    }

    function displayExtractedData(data) {
        console.log("Raw data received:", data);
        extractedDataContainer.innerHTML = '';
    
        if (!data || Object.keys(data).length === 0) {
            console.log("No data received or empty data object");
            extractedDataContainer.innerHTML = '<p>Keine Daten extrahiert.</p>';
            return;
        }
    
        if (data.models && typeof data.models === 'object') {
            console.log("Multiple models detected");
            const modelCount = Object.keys(data.models).length;
            console.log(`Number of models: ${modelCount}`);
            for (const [modelName, modelData] of Object.entries(data.models)) {
                console.log(`Processing model: ${modelName}`);
                const modelAccordion = createModelAccordion(modelName, modelData);
                if (modelAccordion) {
                    extractedDataContainer.appendChild(modelAccordion);
                }
            }
        } else if (data.model) {
            console.log("Single model detected");
            const modelAccordion = createModelAccordion(data.model, data);
            if (modelAccordion) {
                extractedDataContainer.appendChild(modelAccordion);
            }
        } else {
            console.log("Unknown data structure");
            extractedDataContainer.innerHTML = '<p>Unbekannte Datenstruktur</p>';
        }
    }
    
    function createModelAccordion(modelName, modelData) {
        console.log(`Creating accordion for model: ${modelName}`, modelData);
        
        const relevantData = {};
        const dataTypes = [
            'abwasserknoten',
            'haltungspunkte',
            'normschachte',
            'kanale',
            'haltungen',
            'nicht_verarbeitete_normschachte',
            'nicht_verarbeitete_kanale',
            'nicht_verarbeitete_haltungen'
        ];
    
        dataTypes.forEach(type => {
            if (modelData[type] && modelData[type].length > 0) {
                relevantData[type] = modelData[type];
            }
        });
    
        // Übersetze die Schlüssel ins Deutsche für die Anzeige
        const germanTranslations = {
            'abwasserknoten': 'Abwasserknoten',
            'haltungspunkte': 'Haltungspunkte',
            'normschachte': 'Normschächte',
            'kanale': 'Kanäle',
            'haltungen': 'Haltungen',
            'nicht_verarbeitete_normschachte': 'Nicht verarbeitete Normschächte',
            'nicht_verarbeitete_kanale': 'Nicht verarbeitete Kanäle',
            'nicht_verarbeitete_haltungen': 'Nicht verarbeitete Haltungen'
        };
    
        const displayData = {};
        Object.entries(relevantData).forEach(([key, value]) => {
            displayData[germanTranslations[key] || key] = value;
        });
    
        return createAccordion(modelName, displayData);
    }

    function createAccordion(title, content) {
        console.log(`Creating accordion for: ${title}`, content);
        const accordion = document.createElement('div');
        accordion.className = 'accordion';
        
        const header = document.createElement('div');
        header.className = 'accordion-header';
        header.textContent = `${title} (${Array.isArray(content) ? content.length : Object.keys(content).length})`;
        
        const body = document.createElement('div');
        body.className = 'accordion-body';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'accordion-content';
        
        if (Array.isArray(content)) {
            if (content.length > 0) {
                const table = createDataTable(content);
                contentDiv.appendChild(table);
            } else {
                contentDiv.textContent = 'Keine Daten vorhanden';
            }
        } else if (typeof content === 'object' && content !== null) {
            for (const [key, value] of Object.entries(content)) {
                if (Array.isArray(value) || (typeof value === 'object' && value !== null)) {
                    contentDiv.appendChild(createAccordion(key, value));
                } else {
                    const p = document.createElement('p');
                    p.textContent = `${key}: ${value !== undefined ? value : 'Nicht definiert'}`;
                    contentDiv.appendChild(p);
                }
            }
        } else {
            const p = document.createElement('p');
            p.textContent = content !== undefined ? content : 'Nicht definiert';
            contentDiv.appendChild(p);
        }
        
        body.appendChild(contentDiv);
        accordion.appendChild(header);
        accordion.appendChild(body);
        
        header.addEventListener('click', () => {
            const isOpen = body.classList.contains('open');
            body.style.height = isOpen ? '0px' : `${contentDiv.offsetHeight}px`;
            body.classList.toggle('open');
            
            if (!isOpen) {
                setTimeout(() => {
                    body.style.height = 'auto';
                }, 300); // This should match the transition duration
            }
        });
        
        return accordion;
    }

    function createDataTable(data) {
        const table = document.createElement('table');
        table.className = 'data-table';
        
        if (data.length > 0) {
            // Sammle alle einzigartigen Schlüssel aus allen Datensätzen
            const allKeys = new Set();
            data.forEach(item => {
                Object.keys(item).forEach(key => allKeys.add(key));
            });
    
            // Erstelle die Kopfzeile
            const headerRow = table.insertRow();
            allKeys.forEach(key => {
                if (key !== 'lage') {  // 'lage' separat behandeln
                    const th = document.createElement('th');
                    th.textContent = translateHeader(key);
                    headerRow.appendChild(th);
                }
            });
            // Füge Lage X und Lage Y hinzu, wenn 'lage' vorhanden ist
            if (allKeys.has('lage')) {
                const thX = document.createElement('th');
                thX.textContent = 'Lage X';
                headerRow.appendChild(thX);
                const thY = document.createElement('th');
                thY.textContent = 'Lage Y';
                headerRow.appendChild(thY);
            }
    
            // Fülle die Tabelle mit Daten
            data.forEach(item => {
                const row = table.insertRow();
                allKeys.forEach(key => {
                    if (key !== 'lage') {
                        const cell = row.insertCell();
                        let value = item[key];
                        if (typeof value === 'number') {
                            value = value.toFixed(3);
                        }
                        cell.textContent = value !== undefined ? value : 'Nicht definiert';
                    }
                });
                // Behandle 'lage' separat
                if (allKeys.has('lage')) {
                    const cellX = row.insertCell();
                    const cellY = row.insertCell();
                    cellX.textContent = item.lage && item.lage.c1 !== undefined ? Number(item.lage.c1).toFixed(3) : 'Nicht definiert';
                    cellY.textContent = item.lage && item.lage.c2 !== undefined ? Number(item.lage.c2).toFixed(3) : 'Nicht definiert';
                }
            });
        }
        
        return table;
    }
    
    function translateHeader(key) {
        const translations = {
            'id': 'TID',
            'ref': 'REF',
            'kote': 'Kote',
            'bezeichnung': 'Bezeichnung',
            'letzte_aenderung': 'Letzte Änderung',
            'model': 'Modell'
            // Fügen Sie hier weitere Übersetzungen hinzu
        };
        return translations[key] || key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');
    }

    function switchTheme(themeName) {
        const link = document.querySelector('link[rel="stylesheet"]');
        link.href = `/static/css/${themeName}`;
    }
});