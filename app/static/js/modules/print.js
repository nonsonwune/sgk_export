// Print Module

export function initializePrint() {
    console.debug('[Print] Initializing print functionality');
    
    // Create print preview overlay if it doesn't exist
    createPrintPreviewOverlay();
    
    // Initialize print button handlers
    const printButtons = document.querySelectorAll('.print-button');
    console.debug(`[Print] Found ${printButtons.length} print buttons`);
    
    printButtons.forEach(button => {
        console.debug('[Print] Adding click handler to print button');
        button.addEventListener('click', function(e) {
            e.preventDefault();
            preparePrint();
        });
    });
}

function createPrintPreviewOverlay() {
    if (!document.getElementById('printPreviewOverlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'printPreviewOverlay';
        overlay.className = 'print-preview-overlay';
        overlay.innerHTML = `
            <div class="print-preview-content">
                <h3>Preparing Print Preview</h3>
                <div class="print-preview-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
                <p>Please wait...</p>
            </div>
        `;
        document.body.appendChild(overlay);
    }
}

export function showPrintPreview() {
    const overlay = document.getElementById('printPreviewOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

export function hidePrintPreview() {
    const overlay = document.getElementById('printPreviewOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

export function preparePrint() {
    try {
        console.debug('[Print] Starting print preparation');
        showPrintPreview();

        // Find the content to print
        const contentToClone = document.querySelector('.print-form');
        if (!contentToClone) {
            console.error('[Print] Print content not found - missing .print-form element');
            hidePrintPreview();
            return;
        }
        console.debug('[Print] Found print content to clone');

        // Create a hidden iframe for printing
        const printFrame = document.createElement('iframe');
        printFrame.style.position = 'fixed';
        printFrame.style.right = '0';
        printFrame.style.bottom = '0';
        printFrame.style.width = '0';
        printFrame.style.height = '0';
        printFrame.style.border = '0';
        printFrame.className = 'print-frame';
        document.body.appendChild(printFrame);
        console.debug('[Print] Created print iframe');

        // Clone the print content
        const clonedContent = contentToClone.cloneNode(true);
        console.debug('[Print] Cloned content successfully');

        // Setup iframe document
        const frameDoc = printFrame.contentWindow.document;
        frameDoc.open();
        frameDoc.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Print</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
                <link rel="stylesheet" href="/static/css/main.css">
                <link rel="stylesheet" href="/static/css/components/forms.css">
                <link rel="stylesheet" href="/static/css/components/tables.css">
                <link rel="stylesheet" href="/static/css/components/buttons.css">
                <link rel="stylesheet" href="/static/css/components/print.css">
                <style>
                    @media print {
                        body {
                            margin: 0;
                            padding: 0;
                            background: white;
                        }
                        .print-frame {
                            margin: 0;
                            padding: 0;
                        }
                    }
                </style>
            </head>
            <body class="printing">
                ${clonedContent.outerHTML}
            </body>
            </html>
        `);
        frameDoc.close();
        console.debug('[Print] Initialized print iframe document');

        // Wait for images to load in the iframe
        setTimeout(() => {
            try {
                // Print the iframe
                printFrame.contentWindow.print();

                // Cleanup after printing
                printFrame.contentWindow.onafterprint = function() {
                    document.body.removeChild(printFrame);
                    hidePrintPreview();
                };

                // Fallback cleanup if print is cancelled
                setTimeout(() => {
                    if (document.body.contains(printFrame)) {
                        document.body.removeChild(printFrame);
                        hidePrintPreview();
                    }
                }, 1000);
            } catch (e) {
                console.error('Error during print:', e);
                hidePrintPreview();
                if (document.body.contains(printFrame)) {
                    document.body.removeChild(printFrame);
                }
            }
        }, 500);
    } catch (e) {
        console.error('[Print] Error preparing print:', e);
        hidePrintPreview();
    }
}

// Export additional print-related functions
export { initializePrint as default }; 