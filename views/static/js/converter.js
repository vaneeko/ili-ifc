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
            
            Array.from(files).forEach(file => {
                const fileElement = document.createElement('div');
                fileElement.textContent = file.name;
                previewContainer.appendChild(fileElement);
            });

            displayExtractedData(files[0]);
        } else {
            resetFileInfo();
        }
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

    function displayExtractedData(file) {
        const formData = new FormData();
        formData.append('xtfFile', file);
        
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
        
        const table = createDataTable(data);
        body.appendChild(table);
        
        accordion.appendChild(header);
        accordion.appendChild(body);
        
        header.addEventListener('click', () => {
            body.style.display = body.style.display === 'none' ? 'block' : 'none';
        });
        
        return accordion;
    }

    function createDataTable(data) {
        const table = document.createElement('table');
        table.className = 'data-table';
        
        if (data.length > 0) {
            const headerRow = table.insertRow();
            Object.keys(data[0]).forEach(key => {
                const th = document.createElement('th');
                th.textContent = key;
                headerRow.appendChild(th);
            });
            
            data.forEach(item => {
                const row = table.insertRow();
                Object.entries(item).forEach(([key, value]) => {
                    const cell = row.insertCell();
                    cell.textContent = JSON.stringify(value);
                    
                    if (isDefaultValue(key, value)) {
                        cell.classList.add('default-value');
                    }
                });
            });
        }
        
        return table;
    }

    function isDefaultValue(key, value) {
        const defaultValues = {
            'dimension1': '800.0',
            'dimension2': '800.0',
            'kote': document.getElementById('default_sohlenkote').value,
        };
    
        return defaultValues[key] && value == defaultValues[key];
    }

    function switchTheme(themeName) {
        const link = document.querySelector('link[rel="stylesheet"]');
        link.href = `/static/css/${themeName}`;
    }
});