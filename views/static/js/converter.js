document.addEventListener('DOMContentLoaded', function() {
    // Log when the DOM is fully loaded
    console.log("DOM fully loaded and parsed");

    // Get references to DOM elements
    const fileInput = document.getElementById('xtfFiles');
    const fileInfo = document.getElementById('file-info');
    const previewContainer = document.getElementById('preview-container');
    const convertBtn = document.getElementById('convertBtn');
    const alertContainer = document.getElementById('alert-container');
    const outputList = document.getElementById('output-list');
    const extractedDataContainer = document.getElementById('extracted-data');

    // !! Diesen Bereich könnte man entfernen um den Hinweis zum Testbetrieb zu entfernen
    // Alert overlay elements
    const alertOverlay = document.getElementById('alert-overlay');
    const alertCloseBtn = document.getElementById('alert-close');

    // Show the alert overlay when the page loads
    alertOverlay.style.display = 'flex'; // Use 'flex' if you're using Flexbox for centering

    // Event listener for closing the alert overlay
    alertCloseBtn.addEventListener('click', function() {
        alertOverlay.style.display = 'none';
    });
    // !! Ende Bereich den man entfernen kann um den Hinweis zum Testbetrieb zu entfernen

    // Check if file input element exists and add event listener
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelection);
        console.log("File selection event listener added");
    } else {
        console.error("File input element not found");
    }

    // Add event listener for the convert button
    convertBtn.addEventListener('click', convertFiles);

    // Theme switching buttons
    const themeButtons = document.querySelectorAll('.switch-theme-buttons button');
    themeButtons.forEach(button => {
        button.addEventListener('click', () => switchTheme(button.dataset.theme));
    });

    // Handle file selection event
    function handleFileSelection(e) {
        console.log("File selection event triggered");
        const files = e.target.files;
        if (files.length > 0) {
            console.log(`${files.length} file(s) selected`);
            fileInfo.textContent = `${files.length} Datei(en) ausgewählt`;
            previewContainer.innerHTML = '';

            // Display selected file names
            Array.from(files).forEach(file => {
                const fileElement = document.createElement('div');
                fileElement.textContent = file.name;
                previewContainer.appendChild(fileElement);
            });

            // Load data tables with selected files
            loadDataTables(files);
        } else {
            console.log("No files selected");
            resetFileInfo();
        }
    }

    // Extract data from selected files
    function extractData(files) {
        console.log(`Extracting data from ${files.length} file(s)`);
        const formData = new FormData();

        // Append files to form data
        Array.from(files).forEach(file => {
            formData.append('xtfFile', file);
        });

        // Append configuration inputs to form data
        const configInputs = ['default_sohlenkote', 'default_durchmesser', 'default_hoehe', 'default_wanddicke', 'default_bodendicke', 'default_rohrdicke'];
        configInputs.forEach(input => {
            formData.append(input, document.getElementById(input).value);
        });

        formData.append('einfaerben', document.getElementById('einfaerben').checked);

        // Send POST request to extract endpoint
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

    // Reset file information display
    function resetFileInfo() {
        fileInfo.textContent = 'Keine Dateien ausgewählt';
        previewContainer.innerHTML = '';
        extractedDataContainer.innerHTML = '';
    }

    // Convert selected files
    function convertFiles() {
        const formData = new FormData();
        const files = fileInput.files;

        // Check if files are selected
        if (files.length === 0) {
            showAlert('Bitte wählen Sie mindestens eine XTF-Datei aus.', 'error');
            return;
        }

        // Append files to form data
        Array.from(files).forEach(file => {
            formData.append('xtfFiles', file);
        });

        // Append configuration inputs to form data
        const configInputs = ['default_sohlenkote', 'default_durchmesser', 'default_hoehe', 'default_wanddicke', 'default_bodendicke', 'default_rohrdicke'];
        configInputs.forEach(input => {
            formData.append(input, document.getElementById(input).value);
        });

        formData.append('einfaerben', document.getElementById('einfaerben').checked);

        // Disable convert button during processing
        convertBtn.disabled = true;
        convertBtn.textContent = 'Converting...';

        // Send POST request to convert endpoint
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
            // Re-enable convert button
            convertBtn.disabled = false;
            convertBtn.textContent = 'Convert to IFC';
        });
    }

    // Show alert messages
    function showAlert(message, type) {
        alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
        alertContainer.scrollIntoView({ behavior: 'smooth' });
    }

    // Display download links for converted files
    function displayDownloadLinks(links) {
        outputList.innerHTML = '';
        links.forEach(link => {
            const linkElement = document.createElement('div');
            linkElement.innerHTML = `<a href="${link.url}" class="download-link" download>${link.filename}</a>`;
            outputList.appendChild(linkElement);
        });
    }

    // Display extracted data in the UI
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
        } else {
            console.log("Unknown data structure");
            extractedDataContainer.innerHTML = '<p>Unbekannte Datenstruktur</p>';
        }
    }

    // Create an accordion element for each model
    function createModelAccordion(modelName, modelData) {
        console.log(`Creating accordion for model: ${modelName}`, modelData);

        // Create accordion container
        const accordion = document.createElement('div');
        accordion.className = 'accordion';

        // Create accordion header
        const header = document.createElement('div');
        header.className = 'accordion-header';
        header.textContent = modelName;
        accordion.appendChild(header);

        // Create accordion body
        const body = document.createElement('div');
        body.className = 'accordion-body';

        // Iterate over model data and create sub-accordions
        for (const [key, value] of Object.entries(modelData)) {
            if (Array.isArray(value) && value.length > 0) {
                const subAccordion = createAccordion(key, value);
                body.appendChild(subAccordion);
            }
        }

        accordion.appendChild(body);

        // Event listener for toggling accordion
        header.addEventListener('click', () => {
            body.classList.toggle('open');
        });

        return accordion;
    }

    // Create a sub-accordion for data types
    function createAccordion(title, content) {
        // Create accordion container
        const accordion = document.createElement('div');
        accordion.className = 'accordion';

        // Create accordion header
        const header = document.createElement('div');
        header.className = 'accordion-header';
        header.textContent = `${title} (${content.length})`;
        accordion.appendChild(header);

        // Create accordion body
        const body = document.createElement('div');
        body.className = 'accordion-body';

        // Create data table for content
        const table = createDataTable(content);
        body.appendChild(table);

        accordion.appendChild(body);

        // Event listener for toggling sub-accordion
        header.addEventListener('click', (event) => {
            event.stopPropagation();
            body.classList.toggle('open');
        });

        return accordion;
    }

    // Load data tables from selected files
    function loadDataTables(files) {
        console.log("Files to be sent:", files);
        if (files.length === 0) {
            console.error('Keine Dateien ausgewählt');
            return;
        }

        const formData = new FormData();
        Array.from(files).forEach(file => {
            console.log("Appending file:", file.name);
            formData.append('xtfFile', file);
        });

        // Send POST request to extract endpoint
        fetch('/extract', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Unbekannter Fehler');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Data received from server:", data);
            displayExtractedData(data);
        })
        .catch(error => {
            console.error('Error:', error.message);
            extractedDataContainer.innerHTML = `<p>Fehler beim Extrahieren der Daten: ${error.message}</p>`;
        });
    }

    // Create a data table for displaying content
    function createDataTable(data) {
        console.log("Creating data table with data:", data);

        if (!data || data.length === 0) {
            console.error('No data available for the table');
            return document.createElement('p');
        }

        // Create table wrapper
        const tableWrapper = document.createElement('div');
        tableWrapper.className = 'table-wrapper';

        // Create table container
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-container';

        // Create table element
        const table = document.createElement('table');
        table.className = 'data-table';

        // Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = translateHeader(key);
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const tbody = document.createElement('tbody');
        data.forEach((item, index) => {
            const row = document.createElement('tr');
            Object.entries(item).forEach(([key, value]) => {
                const td = document.createElement('td');
                td.className = 'editable-cell';

                // Recursive function to resolve nested objects
                function resolveValue(val) {
                    if (typeof val === 'object' && val !== null) {
                        if (val.c1 !== undefined && val.c2 !== undefined) {
                            // Special case for location objects
                            return `X: ${val.c1}, Y: ${val.c2}`;
                        } else {
                            return Object.entries(val).map(([k, v]) => `${k}: ${resolveValue(v)}`).join(', ');
                        }
                    } else {
                        return val !== undefined ? val : 'N/A';
                    }
                }

                const resolvedValue = resolveValue(value);
                td.textContent = resolvedValue;

                // Make table cells editable
                td.addEventListener('click', function() {
                    if (this.querySelector('input')) return;

                    const input = document.createElement('input');
                    input.value = this.textContent;
                    const originalValue = this.textContent;

                    input.addEventListener('blur', function() {
                        if (this.value !== originalValue) {
                            td.textContent = this.value;
                            // Update data in the global object if necessary
                            // currentData.models[modelName][dataType][index][key] = this.value;
                        } else {
                            td.textContent = originalValue;
                        }
                    });

                    input.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            this.blur();
                        }
                    });

                    this.textContent = '';
                    this.appendChild(input);
                    input.focus();
                });
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);

        tableContainer.appendChild(table);
        tableWrapper.appendChild(tableContainer);

        console.log("Table created with rows:", tbody.children.length);

        return tableWrapper;
    }

    // Translate table headers
    function translateHeader(key) {
        const translations = {
            'id': 'TID',
            'ref': 'REF',
            'kote': 'Kote',
            'bezeichnung': 'Bezeichnung',
            'letzte_aenderung': 'Letzte Änderung',
            'model': 'Modell'
        };
        return translations[key] || key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');
    }

    // Switch themes by changing the stylesheet
    function switchTheme(themeName) {
        const link = document.querySelector('link[rel="stylesheet"]');
        link.href = `/static/css/${themeName}`;
    }
});
