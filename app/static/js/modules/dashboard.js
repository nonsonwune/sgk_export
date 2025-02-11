console.log('[Dashboard Module] Loading dashboard.js');
console.log('[Dashboard Module] Current module exports:', Object.keys(window));

document.addEventListener('DOMContentLoaded', function() {
    debugLog('=== Dashboard Initialization Start ===');
    debugLog('Checking for Chart.js availability', { chartjs: typeof Chart !== 'undefined' });
    debugLog('Checking for required DOM elements');
    
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

// Debug logging setup
function debugLog(message, data = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[Dashboard] ${timestamp} - ${message}`;
    console.log(logMessage);
    if (data) {
        console.log('Data:', data);
    }
    
    // Add to debug panel if it exists
    const debugPanel = document.getElementById('debugPanel');
    if (debugPanel) {
        const logEntry = document.createElement('div');
        logEntry.textContent = logMessage;
        debugPanel.appendChild(logEntry);
    }
}

// Loading state management
function showLoadingState() {
    debugLog('Showing loading state');
    const dashboard = document.querySelector('.dashboard-grid');
    if (dashboard) {
        dashboard.style.opacity = '0.6';
        // Add loading spinner if needed
    }
}

function hideLoadingState() {
    debugLog('Hiding loading state');
    const dashboard = document.querySelector('.dashboard-grid');
    if (dashboard) {
        dashboard.style.opacity = '1';
    }
}

// Unified initialization function
async function initializeDashboard() {
    debugLog('Starting dashboard initialization');
    try {
        // Validate required elements first
        if (!validateRequiredElements()) {
            debugLog('Dashboard initialization aborted due to missing elements');
            showError('Dashboard initialization failed: Missing required elements');
            return;
        }

        // Initialize loading state
        showLoadingState();
        
        // Basic initialization
        debugLog('Setting up event listeners');
        setupEventListeners();
        
        // Chart initialization
        debugLog('Initializing charts');
        await initializeCharts();
        
        // Data loading
        debugLog('Loading dashboard data');
        const timeRange = document.getElementById('timeRange').value;
        await refreshDashboardData(timeRange);
        
        // Start auto-refresh
        debugLog('Setting up auto-refresh');
        startAutoRefresh();
        
        // Update timestamp
        debugLog('Updating last refreshed timestamp');
        updateLastRefreshed();
        
        hideLoadingState();
        debugLog('Dashboard initialization complete');
    } catch (error) {
        debugLog('Error during initialization', error);
        handleInitializationError(error);
    }
}

function handleInitializationError(error) {
    debugLog('Handling initialization error', error);
    hideLoadingState();
    
    // Show error in all chart containers
    document.querySelectorAll('.chart-container').forEach(container => {
        showChartError(container, 'Failed to initialize dashboard. Please refresh the page.');
    });
    
    // Show general error message
    showError('Dashboard initialization failed. Please refresh the page.');
    
    // Log to monitoring service if available
    console.error('Dashboard initialization failed:', error);
}

function validateChartDataStructure(data) {
    debugLog('Validating chart data structure');
    if (!data) {
        debugLog('Chart data is null or undefined');
        return false;
    }
    
    const requiredFields = ['labels', 'shipments', 'revenue'];
    const missingFields = requiredFields.filter(field => !data[field]);
    
    if (missingFields.length > 0) {
        debugLog('Missing required fields in chart data', missingFields);
        return false;
    }
    
    // Validate data arrays have matching lengths and are not too large
    const lengths = requiredFields.map(field => data[field].length);
    const allLengthsMatch = lengths.every(len => len === lengths[0]);
    
    if (!allLengthsMatch) {
        debugLog('Data arrays have mismatched lengths', lengths);
        return false;
    }
    
    // Check for reasonable data size
    if (lengths[0] > 1000) {
        debugLog('Data size exceeds reasonable limit', lengths[0]);
        return false;
    }
    
    debugLog('Chart data structure validation passed');
    return true;
}

async function getValidatedChartData() {
    debugLog('Fetching and validating chart data');
    try {
        // Use the main dashboard data endpoint instead
        const timeRange = document.getElementById('timeRange').value;
        const response = await fetch(`/api/dashboard/data?timeRange=${timeRange}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        debugLog('Raw chart data received:', data);
        
        // Transform the data structure to match what the charts expect
        const chartData = {
            labels: data.trends.dates || [],
            shipments: data.trends.shipments || [],
            revenue: data.trends.revenue || []
        };
        
        if (!validateChartDataStructure(chartData)) {
            throw new Error('Invalid chart data structure received from API');
        }
        
        return chartData;
    } catch (error) {
        debugLog('Error fetching chart data', error);
        throw error;
    }
}

function handleChartError(chartId, error) {
    debugLog(`Error handling for chart: ${chartId}`, error);
    const chartContainer = document.getElementById(`${chartId}Container`);
    if (chartContainer) {
        chartContainer.innerHTML = `
            <div class="chart-error">
                <p>Failed to load chart</p>
                <button onclick="retryChartLoad('${chartId}')">Retry</button>
            </div>
        `;
    }
}

async function retryChartLoad(chartId) {
    debugLog(`Retrying chart load: ${chartId}`);
    try {
        await initializeCharts();
        debugLog(`Successfully reloaded chart: ${chartId}`);
    } catch (error) {
        debugLog(`Failed to reload chart: ${chartId}`, error);
        handleChartError(chartId, error);
    }
}

// Add chart registry
const chartRegistry = {
    instances: {},
    register: function(id, instance) {
        debugLog(`Registering chart: ${id}`);
        this.instances[id] = instance;
    },
    get: function(id) {
        return this.instances[id];
    },
    destroy: function(id) {
        debugLog(`Attempting to destroy chart: ${id}`);
        const chart = this.instances[id];
        if (chart && typeof chart.destroy === 'function') {
            debugLog(`Destroying chart: ${id}`);
            chart.destroy();
            delete this.instances[id];
        } else {
            debugLog(`No valid chart instance found for: ${id}`);
        }
    }
};

function destroyChart(chartId) {
    debugLog(`Cleanup requested for chart: ${chartId}`);
    chartRegistry.destroy(chartId);
}

// Update chart initialization
async function initializeCharts() {
    debugLog('Starting chart initialization with registry');
    try {
        // Clean up existing charts
        ['shipmentTrendChart', 'revenueChart', 'statusDistributionChart'].forEach(chartId => {
            destroyChart(chartId);
        });

        const chartData = await getValidatedChartData();
        debugLog('Chart data received', chartData);
        
        if (!validateChartDataStructure(chartData)) {
            throw new Error('Invalid chart data structure');
        }

        // Initialize shipment trend chart
        const shipmentCtx = document.getElementById('shipmentTrendChart');
        if (shipmentCtx) {
            debugLog('Initializing shipment trend chart');
            // Show canvas
            shipmentCtx.style.display = 'block';
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
                    animation: {
                        duration: chartData.labels.length > 50 ? 0 : 1000
                    },
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
            chartRegistry.register('shipmentTrendChart', shipmentChart);
            hideChartLoading(shipmentCtx.closest('.chart-container'));
        }

        // Initialize revenue chart
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            debugLog('Initializing revenue chart');
            // Show canvas
            revenueCtx.style.display = 'block';
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
                    animation: {
                        duration: chartData.labels.length > 50 ? 0 : 1000
                    },
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
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
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
            chartRegistry.register('revenueChart', revenueChart);
            hideChartLoading(revenueCtx.closest('.chart-container'));
        }

        // Initialize status distribution chart
        const statusCtx = document.getElementById('statusDistributionChart');
        if (statusCtx) {
            debugLog('Initializing status distribution chart');
            // Show canvas
            statusCtx.style.display = 'block';
            const statusChart = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Pending', 'Processing', 'In Transit', 'Delivered', 'Cancelled'],
                    datasets: [{
                        data: [0, 0, 0, 0, 0],
                        backgroundColor: [
                            '#FCD34D',
                            '#60A5FA',
                            '#34D399',
                            '#A78BFA',
                            '#F87171'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true
                            }
                        }
                    },
                    animation: {
                        duration: 500
                    },
                    cutout: '70%'
                }
            });
            chartRegistry.register('statusDistributionChart', statusChart);
            hideChartLoading(statusCtx.closest('.chart-container'));
        }

        debugLog('Charts initialized successfully');
    } catch (error) {
        debugLog('Error initializing charts', error);
        throw error;
    }
}

// Update showChartLoading to properly handle canvas visibility
function showChartLoading(container) {
    if (!container) return;
    
    const loadingState = container.querySelector('.chart-loading-state');
    const errorState = container.querySelector('.chart-error-state');
    const canvas = container.querySelector('canvas');
    
    if (loadingState) loadingState.style.display = 'flex';
    if (errorState) errorState.style.display = 'none';
    if (canvas) canvas.style.display = 'none';
}

// Update hideChartLoading to properly handle canvas visibility
function hideChartLoading(container) {
    if (!container) return;
    
    const loadingState = container.querySelector('.chart-loading-state');
    const errorState = container.querySelector('.chart-error-state');
    const canvas = container.querySelector('canvas');
    
    if (loadingState) loadingState.style.display = 'none';
    if (errorState) errorState.style.display = 'none';
    if (canvas) canvas.style.display = 'block';
}

// Setup event listeners
function setupEventListeners() {
    debugLog('Setting up event listeners');
    
    // Time range selector
    const timeRange = document.getElementById('timeRange');
    if (timeRange) {
        timeRange.addEventListener('change', async (event) => {
            debugLog('Time range changed:', event.target.value);
            await refreshDashboardData(event.target.value);
        });
    }
    
    // Chart view controls
    document.querySelectorAll('.chart-controls .btn').forEach(button => {
        button.addEventListener('click', async (event) => {
            const view = event.target.dataset.view;
            const container = event.target.closest('.chart-container');
            if (!container) return;
            
            debugLog('Chart view changed:', { containerId: container.id, view });
            
            // Update active state
            container.querySelectorAll('.chart-controls .btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Update chart
            await updateChartView(container.id, view);
        });
    });
    
    // Retry buttons
    document.querySelectorAll('.retry-btn').forEach(button => {
        button.addEventListener('click', async (event) => {
            const container = event.target.closest('.chart-container');
            if (!container) return;
            
            debugLog('Retry clicked for container:', container.id);
            await retryChartLoad(container.id);
        });
    });
}

// Auto refresh setup
function startAutoRefresh() {
    setInterval(async () => {
        const timeRange = document.getElementById('timeRange').value;
        await refreshDashboardData(timeRange);
        updateLastRefreshed();
    }, 5 * 60 * 1000); // Refresh every 5 minutes
}

// Dashboard data refresh
async function refreshDashboardData(timeRange) {
    debugLog('Refreshing dashboard data', { timeRange });
    try {
        debugLog('Making API request to /api/dashboard/data');
        const response = await fetch(`/api/dashboard/data?timeRange=${timeRange}`);
        
        if (!response.ok) {
            debugLog('API request failed', {
                status: response.status,
                statusText: response.statusText
            });
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        debugLog('Dashboard data received', data);
        
        // Validate data structure
        if (!data || !data.stats || !data.trends) {
            debugLog('Invalid data structure received', data);
            throw new Error('Invalid dashboard data structure');
        }
        
        // Log data structure before updates
        debugLog('Stats data structure:', data.stats);
        debugLog('Trends data structure:', data.trends);
        debugLog('Status distribution:', data.status_distribution);
        
        debugLog('Updating dashboard components');
        await Promise.all([
            updateDashboardMetrics(data.stats),
            updateCharts(data)
        ]);
        
        debugLog('Dashboard refresh complete');
    } catch (error) {
        debugLog('Error refreshing dashboard data', error);
        // Show error in all chart containers
        document.querySelectorAll('.chart-container').forEach(container => {
            showChartError(container, 'Failed to refresh dashboard data. Please try again.');
        });
        throw error;
    }
}

// Update the updateCharts function to handle visibility
function updateCharts(data) {
    debugLog('Updating charts with data', data);
    if (!data || !data.trends) {
        debugLog('Invalid chart data structure');
        return;
    }

    const { dates, shipments, revenue } = data.trends;
    const labels = dates || data.trends.labels;

    // Show all chart canvases
    document.querySelectorAll('.chart-container canvas').forEach(canvas => {
        canvas.style.display = 'block';
    });

    // Update shipment trend chart
    const shipmentChart = chartRegistry.get('shipmentTrendChart');
    if (shipmentChart && labels && shipments) {
        debugLog('Updating shipment trend chart');
        const container = document.getElementById('shipmentTrendChart').closest('.chart-container');
        hideChartLoading(container);
        hideChartError(container);
        shipmentChart.data.labels = labels;
        shipmentChart.data.datasets[0].data = shipments;
        shipmentChart.update('none');
    }

    // Update revenue chart
    const revenueChart = chartRegistry.get('revenueChart');
    if (revenueChart && labels && revenue) {
        debugLog('Updating revenue chart');
        const container = document.getElementById('revenueChart').closest('.chart-container');
        hideChartLoading(container);
        hideChartError(container);
        revenueChart.data.labels = labels;
        revenueChart.data.datasets[0].data = revenue;
        revenueChart.update('none');
    }

    // Update status distribution chart
    const statusChart = chartRegistry.get('statusDistributionChart');
    if (statusChart && data.status_distribution) {
        debugLog('Updating status distribution chart');
        const container = document.getElementById('statusDistributionChart').closest('.chart-container');
        hideChartLoading(container);
        hideChartError(container);
        const statusData = Object.values(data.status_distribution);
        statusChart.data.datasets[0].data = statusData;
        statusChart.update();
    }
}

// Update chart view
async function updateChartView(containerId, view) {
    debugLog('Updating chart view:', { containerId, view });
    const container = document.getElementById(containerId);
    if (!container) {
        debugLog('Container not found:', containerId);
        return;
    }
    
    try {
        showChartLoading(container);
        
        // Get the chart instance
        const chartId = container.querySelector('canvas').id;
        const chart = chartRegistry.get(chartId);
        if (!chart) {
            throw new Error(`Chart instance not found for ${chartId}`);
        }
        
        // Fetch new data with the selected view
        const data = await getValidatedChartData();
        if (!data) {
            throw new Error('No data received');
        }
        
        // Update chart data
        chart.data.labels = data.labels;
        if (chartId === 'shipmentTrendChart') {
            chart.data.datasets[0].data = data.shipments;
        } else if (chartId === 'revenueChart') {
            chart.data.datasets[0].data = data.revenue;
        }
        
        chart.update();
        hideChartLoading(container);
        debugLog('Chart view updated successfully:', { chartId, view });
    } catch (error) {
        debugLog('Error updating chart view:', error);
        showChartError(container, error.message);
    }
}

// Update last refreshed timestamp
function updateLastRefreshed() {
    const element = document.getElementById('lastUpdated');
    if (element) {
        element.textContent = new Date().toLocaleTimeString();
    }
}

// Error handling
function showError(message) {
    debugLog('Showing error message', message);
    const errorContainer = document.querySelector('.error-state');
    if (errorContainer) {
        const errorMessage = errorContainer.querySelector('p');
        if (errorMessage) {
            errorMessage.textContent = message;
        }
        errorContainer.style.display = 'block';
    } else {
        console.error(message);
    }
}

// Track module initialization
console.log('[Dashboard Module] Module initialization complete'); 

function validateRequiredElements() {
    debugLog('Validating required dashboard elements');
    const requiredElements = [
        'shipments-total',
        'revenue-total',
        'shipments-active',
        'shipments-delivered'
    ];
    
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    if (missingElements.length > 0) {
        debugLog('Missing required elements:', { missingElements });
        console.warn('Missing required dashboard elements:', missingElements);
        return false;
    }
    
    debugLog('All required elements present');
    return true;
}

// Update dashboard metrics
async function updateDashboardMetrics(stats) {
    debugLog('Updating dashboard metrics', stats);
    try {
        // Update total shipments
        const totalShipments = document.getElementById('shipments-total');
        if (totalShipments) {
            totalShipments.textContent = stats.total_shipments;
        }

        // Update active shipments
        const activeShipments = document.getElementById('shipments-active');
        if (activeShipments) {
            activeShipments.textContent = stats.active_shipments;
        }

        // Update delivered shipments
        const deliveredShipments = document.getElementById('shipments-delivered');
        if (deliveredShipments) {
            deliveredShipments.textContent = stats.delivered_shipments;
        }

        // Update total revenue
        const totalRevenue = document.getElementById('revenue-total');
        if (totalRevenue) {
            totalRevenue.textContent = `$${stats.total_revenue.toFixed(2)}`;
        }

        debugLog('Dashboard metrics updated successfully');
    } catch (error) {
        debugLog('Error updating dashboard metrics', error);
        throw error;
    }
}

// Update showChartError to handle error states
function showChartError(container, message) {
    debugLog('Showing chart error', { container: container?.id, message });
    if (!container) return;
    
    const loadingState = container.querySelector('.chart-loading-state');
    const errorState = container.querySelector('.chart-error-state');
    const errorMessage = errorState?.querySelector('p');
    const canvas = container.querySelector('canvas');
    
    if (loadingState) loadingState.style.display = 'none';
    if (errorState) {
        errorState.style.display = 'flex';
        if (errorMessage && message) {
            errorMessage.textContent = message;
        }
    }
    if (canvas) canvas.style.display = 'none';
}

// Add hideChartError function
function hideChartError(container) {
    debugLog('Hiding chart error', { container: container?.id });
    if (!container) return;
    
    const errorState = container.querySelector('.chart-error-state');
    const canvas = container.querySelector('canvas');
    
    if (errorState) errorState.style.display = 'none';
    if (canvas) canvas.style.display = 'block';
} 