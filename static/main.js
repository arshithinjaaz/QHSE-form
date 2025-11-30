// static/main.js

// --- Global Data Store ---
// Array to hold the dynamically added report items
window.pendingItems = [];

// Global variable to hold the photo files (since FormData is easier for file handling)
window.photoFiles = []; 

// --- Utility Functions ---

/**
 * Custom alert/notification display using the Bootstrap Modal.
 * @param {string} type - 'success', 'error', 'warning', 'info'
 * @param {string} title - The title of the notification.
 * @param {string} message - The message body.
 */
window.showNotification = function(type, title, message) {
    const modalElement = document.getElementById('customAlertModal');
    if (!modalElement) return;

    const iconMap = {
        'success': { class: 'fa-circle-check text-success', border: 'border-success' },
        'error': { class: 'fa-circle-xmark text-danger', border: 'border-danger' },
        'warning': { class: 'fa-triangle-exclamation text-warning', border: 'border-warning' },
        'info': { class: 'fa-circle-info text-info', border: 'border-info' }
    };

    const iconData = iconMap[type] || iconMap['info'];

    document.getElementById('customAlertTitle').innerHTML = 
        `<i class="fas fa-2x me-3 ${iconData.class}" id="customAlertIcon"></i>${title}`;
    
    document.getElementById('customAlertBody').innerHTML = message;

    const modalDialog = modalElement.querySelector('.modal-content');
    // Ensure existing border classes are removed before adding the new one
    modalDialog.className = modalDialog.className.replace(/border-(success|danger|warning|info)/g, '').trim() + ' ' + iconData.border;

    new bootstrap.Modal(modalElement).show();
}


// --- Report Item Handling ---

/**
 * Draws the current list of pending items in the Report Items tab.
 */
window.renderPendingItems = function() {
    const listContainer = document.getElementById('pendingItemsList');
    // Re-fetch the empty message element every time to ensure we have a current reference
    const emptyMessage = document.getElementById('emptyListMessage'); 
    
    if (!listContainer || !emptyMessage) {
        console.error("DOM element 'pendingItemsList' or 'emptyListMessage' not found.");
        return; 
    }

    // CRITICAL FIX: The next line clears the container, removing the emptyMessage if it's there.
    // The problematic manual removal block has been removed to prevent the element from returning null later.
    listContainer.innerHTML = ''; 
    
    if (window.pendingItems.length === 0) {
        // Re-append the empty message
        listContainer.appendChild(emptyMessage);
        emptyMessage.style.display = 'block'; 
    } else {
        emptyMessage.style.display = 'none'; 
        
        window.pendingItems.forEach((item, index) => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'report-item';
            itemDiv.setAttribute('data-index', index);
            
            // Build the display text
            const displayText = `
                <strong>${item.asset} - ${item.system}</strong>: ${item.description}
                (Qty: ${item.quantity}, Brand: ${item.brand || 'N/A'}, Photos: ${item.photoFiles.length})
            `;

            itemDiv.innerHTML = `
                <div class="item-details">
                    <p class="mb-0">${displayText}</p>
                    ${item.comments ? `<small class="text-muted">Comments: ${item.comments}</small>` : ''}
                </div>
                <div class="item-actions">
                    <button type="button" class="btn btn-sm btn-danger remove-item-btn" data-index="${index}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            listContainer.appendChild(itemDiv);
        });

        // Attach event listeners for the remove buttons
        document.querySelectorAll('.remove-item-btn').forEach(button => {
            button.addEventListener('click', function() {
                const indexToRemove = parseInt(this.getAttribute('data-index'));
                window.pendingItems.splice(indexToRemove, 1);
                window.renderPendingItems(); // Re-render the list after removal
            });
        });
    }
}

/**
 * Gathers data from the input fields and adds a new item to the list.
 */
function handleAddItem() {
    const asset = document.getElementById('assetSelect').value;
    const system = document.getElementById('systemSelect').value;
    const description = document.getElementById('descriptionSelect').value;
    const quantity = document.getElementById('quantityInput').value;
    const brand = document.getElementById('brandInput').value;
    const comments = document.getElementById('commentsTextarea').value;
    const photoInput = document.getElementById('photoInput');

    // Simple validation
    if (!asset || !system || !description) {
        window.showNotification('error', 'Missing Fields', 'Please select an **Asset**, **System**, and **Description**.');
        return;
    }

    // Convert FileList to a simple Array of Files
    const files = Array.from(photoInput.files);
    let photoBase64 = [];

    // Helper function to convert file to Base64 (async operation)
    const fileToBase64 = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    };

    // Use Promise.all to handle multiple file conversions concurrently
    Promise.all(files.map(fileToBase64))
        .then(base64Array => {
            photoBase64 = base64Array;

            // Create the new item object
            const newItem = {
                asset,
                system,
                description,
                quantity: parseInt(quantity) || 1,
                brand,
                comments,
                // Store base64 strings directly in the item
                photoFiles: photoBase64 
            };
            
            window.pendingItems.push(newItem);
            window.renderPendingItems();

            // Reset input fields for the next item
            document.getElementById('assetSelect').value = '';
            document.getElementById('systemSelect').value = '';
            document.getElementById('descriptionSelect').value = '';
            document.getElementById('quantityInput').value = 1;
            document.getElementById('brandInput').value = '';
            document.getElementById('commentsTextarea').value = '';
            photoInput.value = ''; // Clear file input
            
            window.showNotification('success', 'Item Added', 'Defect item successfully added to the report list.');
        })
        .catch(error => {
            console.error("Error converting files to Base64:", error);
            window.showNotification('error', 'Photo Error', 'Failed to process photos.');
        });
}


// --- Submission Logic ---

/**
 * Gathers all form data, including pending items and signatures, and submits to the backend.
 * This is where the automatic download is implemented.
 */
window.onSubmit = function(event) {
    event.preventDefault(); 
    
    const statusDiv = document.getElementById('status');
    const alertDiv = document.getElementById('submission-alert');
    const downloadArea = document.getElementById('downloadArea');
    
    // Clear previous download links/messages
    downloadArea.innerHTML = '';
    
    // Final check for signatures
    const techSigData = document.getElementById('techSignatureData').value;
    
    if (window.techPad && window.techPad.isEmpty()) {
        alertDiv.classList.remove('alert-info');
        alertDiv.classList.add('alert-warning');
        alertDiv.textContent = 'Please provide the Technician Signature before submitting.';
        return;
    }
    
    // 1. Gather all form data
    const form = document.getElementById('visitForm');
    const formData = new FormData(form);
    
    // Convert FormData to a JSON object for complex data structure (report_items)
    const dataToSend = {};
    formData.forEach((value, key) => {
        dataToSend[key] = value;
    });

    // Replace the hidden inputs with the actual signature data (which already happened in the click listener in site_visit_form.html)
    dataToSend['tech_signature'] = techSigData;
    dataToSend['opMan_signature'] = document.getElementById('opManSignatureData').value;

    // Add the list of report items
    dataToSend['report_items'] = window.pendingItems;

    // 2. Update Status UI
    statusDiv.textContent = 'Submitting... Please wait.';
    alertDiv.classList.remove('alert-success', 'alert-danger', 'alert-warning');
    alertDiv.classList.add('alert-info');
    alertDiv.textContent = 'Report is being processed. This may take a moment...';

    // 3. Send data to Flask backend
    axios.post('/submit-report', dataToSend, { 
        headers: {
            'Content-Type': 'application/json' // Send JSON for complex data
        }
    })
    .then(response => {
        statusDiv.textContent = 'Submission Successful!';
        alertDiv.classList.remove('alert-info');
        alertDiv.classList.add('alert-success');
        alertDiv.textContent = 'Report successfully generated. Downloads are starting automatically!';

        // ----------------------------------------------------
        // LOGIC FOR AUTOMATIC DOWNLOAD
        // ----------------------------------------------------
        
        // 1. Get the URLs (assuming response.data contains pdf_url and excel_url, or use fallback endpoints)
        const pdfUrl = response.data.pdf_url || '/download-pdf';
        const excelUrl = response.data.excel_url || '/download-excel';

        /**
         * Triggers a programmatic download by creating a temporary link and simulating a click.
         * @param {string} url - The download URL.
         * @param {string} filename - The desired filename for the download.
         */
        const triggerDownload = (url, filename) => {
            const link = document.createElement('a');
            link.href = url;
            link.download = filename; // Suggests a filename to the browser
            link.style.display = 'none'; // Keep the element invisible
            document.body.appendChild(link);
            // Must use a slight delay for the second file to bypass pop-up blockers
            setTimeout(() => {
                link.click();
                document.body.removeChild(link);
            }, 0); 
        };
        
        // Trigger both downloads
        triggerDownload(pdfUrl, 'Site_Visit_Report.pdf');
        triggerDownload(excelUrl, 'Site_Visit_Report.xlsx');
        // ----------------------------------------------------
        
        window.showNotification('success', 'Reports Generated', 'Your PDF and Excel reports should be downloading automatically. Check your browser downloads.');

    })
    .catch(error => {
        console.error("Submission failed:", error);
        statusDiv.textContent = 'Submission Failed!';
        alertDiv.classList.remove('alert-info');
        alertDiv.classList.add('alert-danger');
        alertDiv.textContent = `Error: ${error.response && error.response.data ? error.response.data.message : error.message}. Check console for details.`;
        window.showNotification('error', 'Submission Failed', 'The report submission to the server failed. Check the console for details.');
    });
}


// --- DOM Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Signature Pads
    const techCanvas = document.getElementById('techSignaturePad');
    const opManCanvas = document.getElementById('opManSignaturePad');
    
    if (techCanvas) {
        window.techPad = new SignaturePad(techCanvas, {
            backgroundColor: 'rgb(255, 255, 255)' // Clear canvas
        });
    }

    if (opManCanvas) {
        window.opManPad = new SignaturePad(opManCanvas, {
            backgroundColor: 'rgb(255, 255, 255)' // Clear canvas
        });
    }

    // 2. Attach Event Listeners
    const addItemButton = document.getElementById('addItemButton'); 
    if (addItemButton) {
        addItemButton.addEventListener('click', handleAddItem);
    }

    // 3. Initialize Dropdown Logic (Assumed to be in dropdown_data.js or here)
    if (typeof window.initializeDropdowns === 'function') {
        window.initializeDropdowns();
    } else {
        console.warn('Dropdown initialization function (initializeDropdowns) not found.');
    }

    // 4. Initial rendering of the list
    window.renderPendingItems();
});