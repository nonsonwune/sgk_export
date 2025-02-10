document.addEventListener('DOMContentLoaded', function() {
    console.log('=== Dashboard Initialization Start ===');
    
    // Initialize dashboard with retry mechanism
    initializeDashboardWithRetry();
});

function initializeDashboardWithRetry(retryCount = 0, maxRetries = 3) {
    console.log(`Initializing dashboard (attempt ${retryCount + 1}/${maxRetries})`);
    
    // Ensure Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        showChartError('Chart.js library failed to load. Please refresh the page.');
        return;
    }
    
    try {
        initializeDashboard();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        if (retryCount < maxRetries - 1) {
            console.log(`Retrying initialization in 1 second... (${retryCount + 1}/${maxRetries})`);
            setTimeout(() => {
                initializeDashboardWithRetry(retryCount + 1, maxRetries);
            }, 1000);
        } else {
            showChartError('Failed to initialize dashboard after multiple attempts. Please refresh the page.');
        }
    }
}

function initializeDashboard() {
    console.log('=== Dashboard Initialization ===');
    
    // Get dashboard container
    const container = document.querySelector('.container');
    if (!container) {
        console.error('Dashboard container not found');
        throw new Error('Dashboard container not found');
    }
    
    // Get and parse error state
    const errorState = container.getAttribute('data-error');
    console.log('Error state:', errorState);
    
    if (errorState === 'true') {
        console.error('Dashboard in error state');
        showChartError('Dashboard is currently in an error state');
        return;
    }
    
    // Get and validate chart data
    const chartData = getValidatedChartData(container);
    console.log('Validated chart data:', chartData);
    
    // Initialize charts if data is valid
    if (chartData && Object.keys(chartData).length > 0) {
        console.log('Initializing charts with data');
        initializeCharts(chartData);
    } else {
        console.error('No valid chart data available');
        showChartError('No chart data available');
    }
}

function getValidatedChartData(container) {
    console.log('=== Chart Data Validation Start ===');
    console.log('Container:', container);
    
    // Get debug output if available
    const debugOutput = document.getElementById('debug-output');
    if (debugOutput) {
        console.log('Debug output content:', debugOutput.textContent);
        
        // Try to extract data from debug output first
        try {
            const safeJsonMatch = debugOutput.textContent.match(/Safe JSON trend_data: (.*)/);
            if (safeJsonMatch && safeJsonMatch[1]) {
                console.log('Found data in debug output');
                const debugData = JSON.parse(safeJsonMatch[1].trim());
                if (validateChartDataStructure(debugData)) {
                    console.log('Using valid data from debug output');
                    return debugData;
                }
            }
        } catch (debugError) {
            console.warn('Failed to parse debug output:', debugError);
        }
    }
    
    try {
        // Get raw chart data from container attribute
        const rawChartData = container.getAttribute('data-chart-data');
        console.log('Raw chart data string:', rawChartData);
        
        if (!rawChartData) {
            console.error('Chart data attribute is empty or null');
            throw new Error('No chart data found');
        }
        
        // Parse chart data
        let chartData;
        try {
            chartData = JSON.parse(rawChartData);
            console.log('Successfully parsed chart data:', chartData);
        } catch (parseError) {
            console.error('Error parsing chart data:', parseError);
            console.error('Raw string that failed to parse:', rawChartData);
            throw new Error(`Failed to parse chart data: ${parseError.message}`);
        }
        
        // Validate structure
        if (!validateChartDataStructure(chartData)) {
            throw new Error('Invalid chart data structure');
        }
        
        console.log('Chart data validation successful');
        return chartData;
        
    } catch (error) {
        console.error('Error processing chart data:', error);
        console.error('Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        showChartError(error.message);
        return null;
    }
}

function validateChartDataStructure(data) {
    if (!data || typeof data !== 'object') {
        console.error('Chart data is not an object');
        return false;
    }
    
    const requiredKeys = ['labels', 'shipments', 'revenue'];
    
    // Check for required keys
    const hasAllKeys = requiredKeys.every(key => {
        const hasKey = key in data;
        if (!hasKey) console.error(`Missing required key: ${key}`);
        return hasKey;
    });
    
    if (!hasAllKeys) return false;
    
    // Validate arrays
    const hasValidArrays = requiredKeys.every(key => {
        const isArray = Array.isArray(data[key]);
        if (!isArray) console.error(`${key} is not an array`);
        return isArray;
    });
    
    if (!hasValidArrays) return false;
    
    // Check array lengths match
    const arrayLength = data.labels.length;
    const hasMatchingLengths = requiredKeys.every(key => {
        const matches = data[key].length === arrayLength;
        if (!matches) console.error(`${key} length doesn't match labels length`);
        return matches;
    });
    
    if (!hasMatchingLengths) return false;
    
    // Validate data types
    const isValid = data.labels.every(label => typeof label === 'string') &&
                   data.shipments.every(val => typeof val === 'number') &&
                   data.revenue.every(val => typeof val === 'number');
    
    if (!isValid) {
        console.error('Invalid data types in arrays');
        return false;
    }
    
    return true;
}

function initializeCharts(chartData) {
    // Initialize shipment trend chart
    const shipmentCtx = document.getElementById('shipmentTrendChart');
    if (shipmentCtx) {
        const shipmentChart = new Chart(shipmentCtx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Shipments',
                    data: chartData.shipments,
                    borderColor: '#4299E1',
                    backgroundColor: 'rgba(66, 153, 225, 0.1)',
                    borderWidth: 2,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        
        shipmentCtx.style.display = 'block';
        hideChartLoading(shipmentCtx.closest('.chart-container'));
    }
    
    // Initialize revenue chart
    const revenueCtx = document.getElementById('revenueChart');
    if (revenueCtx) {
        const revenueChart = new Chart(revenueCtx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Revenue',
                    data: chartData.revenue,
                    backgroundColor: '#48BB78',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        
        revenueCtx.style.display = 'block';
        hideChartLoading(revenueCtx.closest('.chart-container'));
    }
}

function showChartError(message, container = null) {
    const containers = container ? [container] : document.querySelectorAll('.chart-container');
    
    containers.forEach(container => {
        const loadingState = container.querySelector('.chart-loading-state');
        const errorState = container.querySelector('.chart-error-state');
        const canvas = container.querySelector('canvas');
        
        if (loadingState) loadingState.style.display = 'none';
        if (canvas) canvas.style.display = 'none';
        
        if (errorState) {
            const errorMessage = errorState.querySelector('.error-message');
            if (errorMessage) errorMessage.textContent = message;
            errorState.style.display = 'flex';
        }
    });
}

function hideChartError(container = null) {
    const containers = container ? [container] : document.querySelectorAll('.chart-container');
    
    containers.forEach(container => {
        const errorState = container.querySelector('.chart-error-state');
        if (errorState) errorState.style.display = 'none';
    });
}

function showChartLoading(container = null) {
    const containers = container ? [container] : document.querySelectorAll('.chart-container');
    
    containers.forEach(container => {
        const loadingState = container.querySelector('.chart-loading-state');
        const errorState = container.querySelector('.chart-error-state');
        const canvas = container.querySelector('canvas');
        
        if (loadingState) loadingState.style.display = 'flex';
        if (errorState) errorState.style.display = 'none';
        if (canvas) canvas.style.display = 'none';
    });
}

function hideChartLoading(container = null) {
    const containers = container ? [container] : document.querySelectorAll('.chart-container');
    
    containers.forEach(container => {
        const loadingState = container.querySelector('.chart-loading-state');
        if (loadingState) loadingState.style.display = 'none';
    });
}

// Add retry functionality
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.retry-btn').forEach(button => {
        button.addEventListener('click', function() {
            const container = this.closest('.chart-container');
            console.log('Retrying chart initialization for container:', container);
            
            hideChartError(container);
            showChartLoading(container);
            
            // Retry initialization after a short delay
            setTimeout(() => {
                try {
                    initializeDashboard();
                } catch (error) {
                    console.error('Error during retry:', error);
                    showChartError('Failed to reload chart data', container);
                }
            }, 100);
        });
    });
}); 