// PDF preview using PDF.js
// Renders first page of PDF as thumbnail preview

(function() {
    'use strict';

    // Get PDF.js library - check multiple possible locations
    function getPdfJsLib() {
        // Try different ways PDF.js might be exported
        // PDF.js exports as pdfjsLib in global scope
        if (typeof pdfjsLib !== 'undefined' && pdfjsLib.getDocument) {
            return pdfjsLib;
        }
        if (typeof window !== 'undefined' && window.pdfjsLib && window.pdfjsLib.getDocument) {
            return window.pdfjsLib;
        }
        // Also check for UMD export path
        if (typeof globalThis !== 'undefined' && globalThis['pdfjs-dist/build/pdf'] && globalThis['pdfjs-dist/build/pdf'].getDocument) {
            return globalThis['pdfjs-dist/build/pdf'];
        }
        if (typeof window !== 'undefined' && window['pdfjs-dist/build/pdf'] && window['pdfjs-dist/build/pdf'].getDocument) {
            return window['pdfjs-dist/build/pdf'];
        }
        return null;
    }

    // Wait for PDF.js to load
    function waitForPdfJs(callback, maxAttempts) {
        maxAttempts = maxAttempts || 50; // 5 seconds max wait
        let attempts = 0;

        function check() {
            const pdfLib = getPdfJsLib();
            if (pdfLib) {
                callback(pdfLib);
            } else if (attempts < maxAttempts) {
                attempts++;
                setTimeout(check, 100);
            } else {
                // Debug: log what we found
                console.warn('PDF.js failed to load after waiting');
                console.log('Available globals:', {
                    pdfjsLib: typeof pdfjsLib,
                    windowPdfjsLib: typeof window !== 'undefined' ? typeof window.pdfjsLib : 'N/A',
                    globalThisPdf: typeof globalThis !== 'undefined' ? typeof globalThis['pdfjs-dist/build/pdf'] : 'N/A'
                });
            }
        }

        check();
    }

    function renderPdfPreview(container, pdfUrl, pdfjsLib) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Set preview size (160x120)
        const previewWidth = 160;
        const previewHeight = 120;
        
        // Style canvas
        canvas.style.width = previewWidth + 'px';
        canvas.style.height = previewHeight + 'px';
        canvas.style.maxWidth = '100%';
        canvas.style.display = 'block';
        
        // Clear container and add canvas
        // Keep the link functionality - canvas will be inside <a> tag
        container.innerHTML = '';
        container.appendChild(canvas);

        // Load and render PDF
        pdfjsLib.getDocument(pdfUrl).promise.then(function(pdf) {
            // Get first page
            return pdf.getPage(1);
        }).then(function(page) {
            // Calculate scale to fit preview size
            const viewport = page.getViewport({ scale: 1.0 });
            const scale = Math.min(
                previewWidth / viewport.width,
                previewHeight / viewport.height
            );
            const scaledViewport = page.getViewport({ scale: scale });

            // Set canvas actual size (for high DPI displays)
            const outputScale = window.devicePixelRatio || 1;
            canvas.width = Math.floor(scaledViewport.width * outputScale);
            canvas.height = Math.floor(scaledViewport.height * outputScale);
            
            // Scale context for high DPI
            ctx.scale(outputScale, outputScale);

            // Render page
            const renderContext = {
                canvasContext: ctx,
                viewport: scaledViewport
            };
            
            return page.render(renderContext).promise;
        }).then(function() {
            // Success - preview is rendered
        }).catch(function(error) {
            // Error loading PDF
            console.error('Error loading PDF:', error);
            container.innerHTML = '<span style="color:#999; font-size:12px;">PDF preview error</span>';
        });
    }

    // Initialize all PDF previews when DOM is ready and PDF.js is loaded
    function initPdfPreviews(pdfjsLib) {
        // Set worker path
        pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/pdf/pdf.worker.min.js';
        
        const containers = document.querySelectorAll('a.pdf-preview');
        containers.forEach(function(container) {
            const pdfUrl = container.href;
            if (pdfUrl) {
                renderPdfPreview(container, pdfUrl, pdfjsLib);
            }
        });
    }

    // Wait for PDF.js to load, then initialize
    waitForPdfJs(function(pdfjsLib) {
        // Run on DOMContentLoaded or immediately if already loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initPdfPreviews(pdfjsLib);
            });
        } else {
            // DOM already loaded
            initPdfPreviews(pdfjsLib);
        }

        // Also run after Django admin inline forms are added
        // This handles dynamically added forms
        if (typeof django !== 'undefined' && django.jQuery) {
            django.jQuery(document).on('formset:added', function() {
                setTimeout(function() {
                    initPdfPreviews(pdfjsLib);
                }, 100);
            });
        }
    });
})();

