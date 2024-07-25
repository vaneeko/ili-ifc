document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('xtfFiles');
    const fileInfo = document.getElementById('file-info');
    const previewContainer = document.getElementById('preview-container');
    const convertBtn = document.getElementById('convertBtn');
    const alertContainer = document.getElementById('alert-container');
    const outputList = document.getElementById('output-list');
    const extractedDataContainer = document.getElementById('extracted-data');

    fileInput.addEventListener('change', handleFileSelection);
    convertBtn.addEventListener('click', convertFiles);

    const themeButtons = document.querySelectorAll('.switch-theme-buttons button');
    themeButtons.forEach(button => {
        button.addEventListener('click', () => switchTheme(button.dataset.theme));
    });

    function handleFileSelection(e) {
        const files = e.target.files;
        if (files.length > 0) {
            fileInfo.textContent = `${files.length} Datei(en) ausgewählt`;
            previewContainer.innerHTML = '';
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const fileElement = document.createElement('div');
                fileElement.textContent = file.name;
                previewContainer.appendChild(fileElement);
            }
            displayExtractedData(files[0]);
        } else {
            fileInfo.textContent = 'Keine Dateien ausgewählt';
            previewContainer.innerHTML = '';
            extractedDataContainer.innerHTML = '';
        }
    }

    function convertFiles() {
        const formData = new FormData();
        const files = fileInput.files;
        
        if (files.length === 0) {
            showAlert('Bitte wählen Sie mindestens eine XTF-Datei aus.', 'error');
            return;
        }

        for (let i = 0; i < files.length; i++) {
            formData.append('xtfFiles', files[i]);
        }

        formData.append('default_sohlenkote', document.getElementById('default_sohlenkote').value);
        formData.append('default_durchmesser', document.getElementById('default_durchmesser').value);
        formData.append('default_hoehe', document.getElementById('default_hoehe').value);
        formData.append('default_wanddicke', document.getElementById('default_wanddicke').value);
        formData.append('default_bodendicke', document.getElementById('default_bodendicke').value);
        formData.append('default_rohrdicke', document.getElementById('default_rohrdicke').value);
        formData.append('einfaerben', document.getElementById('einfaerben').checked);

        fetch('/convert', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
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
        });
    }

    function showAlert(message, type) {
        alertContainer.innerHTML = `<div class="alert ${type === 'error' ? 'alert-error' : ''}">${message}</div>`;
    }

    function displayDownloadLinks(links) {
        outputList.innerHTML = '';
        links.forEach(link => {
            const linkElement = document.createElement('div');
            linkElement.innerHTML = `<a href="${link.url}" class="download-link">${link.filename}</a>`;
            outputList.appendChild(linkElement);
        });
    }

    function displayExtractedData(file) {
        const formData = new FormData();
        formData.append('xtfFile', file);
        
        formData.append('default_sohlenkote', document.getElementById('default_sohlenkote').value);
        formData.append('default_durchmesser', document.getElementById('default_durchmesser').value);
        formData.append('default_hoehe', document.getElementById('default_hoehe').value);
        formData.append('default_wanddicke', document.getElementById('default_wanddicke').value);
        formData.append('default_bodendicke', document.getElementById('default_bodendicke').value);
        formData.append('default_rohrdicke', document.getElementById('default_rohrdicke').value);
        formData.append('einfaerben', document.getElementById('einfaerben').checked);

        fetch('/extract', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            extractedDataContainer.innerHTML = '';
            if (Object.keys(data).length === 0) {
                extractedDataContainer.innerHTML = '<p>Keine Daten extrahiert.</p>';
            } else {
                for (const [key, value] of Object.entries(data)) {
                    if (Array.isArray(value) && value.length > 0) {
                        const accordion = createAccordion(key, value);
                        extractedDataContainer.appendChild(accordion);
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            extractedDataContainer.innerHTML = '<p>Fehler beim Extrahieren der Daten.</p>';
        });
    }

    function createAccordion(title, data) {
        const accordion = document.createElement('div');
        accordion.className = 'accordion';
        
        const header = document.createElement('div');
        header.className = 'accordion-header';
        header.textContent = `${title} (${data.length})`;
        
        const body = document.createElement('div');
        body.className = 'accordion-body';
        body.style.display = 'none';
        
        const table = document.createElement('table');
        table.className = 'data-table';
        
        if (data.length > 0) {
            const headerRow = table.insertRow();
            for (const key of Object.keys(data[0])) {
                const th = document.createElement('th');
                th.textContent = key;
                headerRow.appendChild(th);
            }
            
            data.forEach(item => {
                const row = table.insertRow();
                for (const [key, value] of Object.entries(item)) {
                    const cell = row.insertCell();
                    cell.textContent = JSON.stringify(value);
                    
                    // Prüfen auf Default-Werte
                    if (isDefaultValue(key, value)) {
                        cell.classList.add('default-value');
                    }
                }
            });
        }
        
        body.appendChild(table);
        accordion.appendChild(header);
        accordion.appendChild(body);
        
        header.addEventListener('click', () => {
            body.style.display = body.style.display === 'none' ? 'block' : 'none';
        });
        
        return accordion;
    }

    function isDefaultValue(key, value) {
        const defaultValues = {
            'dimension1': '800.0',
            'dimension2': '800.0',
            'kote': document.getElementById('default_sohlenkote').value,
            // Fügen Sie hier weitere Default-Werte hinzu
        };
    
        return defaultValues[key] && value == defaultValues[key];
    }

    function switchTheme(themeName) {
        const link = document.querySelector('link[rel="stylesheet"]');
        link.href = `/static/css/${themeName}`;
    }
});