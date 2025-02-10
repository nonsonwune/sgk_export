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

        // Find the content to print (support both templates)
        const contentToClone = document.querySelector('.preview-container') || document.querySelector('.print-form');
        if (!contentToClone) {
            console.error('[Print] Print content not found - missing .preview-container or .print-form element');
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
        printFrame.style.visibility = 'hidden';
        printFrame.className = 'print-frame';
        document.body.appendChild(printFrame);

        // Clone content and prepare for print
        const clonedContent = contentToClone.cloneNode(true);
        
        // Handle QR code if present
        const qrCodeImg = clonedContent.querySelector('.qr-code-container img');
        if (qrCodeImg) {
            const originalQrImg = contentToClone.querySelector('.qr-code-container img');
            if (originalQrImg) {
                qrCodeImg.src = originalQrImg.src;
                console.debug('[Print] QR code image cloned successfully');
            }
        }

        console.debug('[Print] Cloned content successfully');

        // Setup iframe document with proper viewport and print styles
        const frameDoc = printFrame.contentWindow.document;
        frameDoc.open();
        frameDoc.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Print</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
                <link rel="stylesheet" href="/static/css/main.css">
                <link rel="stylesheet" href="/static/css/components/preview.css">
                <link rel="stylesheet" href="/static/css/components/print.css">
                <style>
                    @page {
                        size: A4;
                    }
                    html {
                        margin: 0 !important;
                        padding: 0 !important;
                    }
                    body {
                        margin: 0 !important;
                        padding: 8mm !important;
                        width: 100% !important;
                        max-width: 100% !important;
                        background: white !important;
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }
                    .preview-container,
                    .print-form {
                        width: 100% !important;
                        max-width: 100% !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        background: white !important;
                        box-shadow: none !important;
                    }
                    .info-section {
                        width: 100% !important;
                        max-width: 100% !important;
                        padding: 0 !important;
                    }
                    .info-cards-grid {
                        display: grid !important;
                        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
                        gap: 4mm !important;
                        width: 100% !important;
                        max-width: 100% !important;
                        margin: 4mm 0 !important;
                    }
                    .info-card {
                        width: 100% !important;
                        max-width: 100% !important;
                    }
                    .company-header {
                        width: 100% !important;
                        max-width: 100% !important;
                        padding: 0 !important;
                        margin-bottom: 4mm !important;
                    }
                    .company-info-section {
                        max-width: calc(100% - 160px) !important;
                    }
                    .document-header {
                        width: 100% !important;
                        max-width: 100% !important;
                        padding: 0 !important;
                        margin-bottom: 4mm !important;
                    }
                    /* Remove any bootstrap container constraints */
                    .container, 
                    .container-fluid {
                        width: 100% !important;
                        max-width: 100% !important;
                        margin: 0 !important;
                        padding: 0 !important;
                    }
                    @media print {
                        body {
                            width: 100% !important;
                            max-width: 100% !important;
                        }
                        .preview-container {
                            width: 100% !important;
                            max-width: 100% !important;
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

        // Wait for resources to load
        setTimeout(() => {
            try {
                console.debug('[Print] Initiating print');
                printFrame.contentWindow.print();

                // Cleanup after printing
                printFrame.contentWindow.onafterprint = function() {
                    document.body.removeChild(printFrame);
                    hidePrintPreview();
                    console.debug('[Print] Print completed and cleanup finished');
                };

                // Fallback cleanup
                setTimeout(() => {
                    if (document.body.contains(printFrame)) {
                        document.body.removeChild(printFrame);
                        hidePrintPreview();
                        console.debug('[Print] Cleanup after timeout');
                    }
                }, 1000);
            } catch (e) {
                console.error('[Print] Error during print:', e);
                hidePrintPreview();
                if (document.body.contains(printFrame)) {
                    document.body.removeChild(printFrame);
                }
            }
        }, 1000);

    } catch (e) {
        console.error('[Print] Error preparing print:', e);
        hidePrintPreview();
    }
}

// Export additional print-related functions
export { initializePrint as default }; 