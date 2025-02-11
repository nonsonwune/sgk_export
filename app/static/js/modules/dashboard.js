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

// Validate chart data structure
function validateChartDataStructure(data) {
    debugLog('Validating chart data structure');
    if (!data) {
        debugLog('Chart data is null or undefined');
        return false;
    }
    
    // Validate required sections
    const requiredSections = ['stats', 'status_distribution', 'trends'];
    const missingSections = requiredSections.filter(section => !data[section]);
    
    if (missingSections.length > 0) {
        debugLog('Missing required sections in chart data', missingSections);
        return false;
    }
    
    // Validate trends data
    const trendFields = ['labels', 'shipments', 'revenue'];
    const missingTrendFields = trendFields.filter(field => !data.trends[field]);
    
    if (missingTrendFields.length > 0) {
        debugLog('Missing required trend fields', missingTrendFields);
        return false;
    }
    
    // Validate data arrays have matching lengths
    const lengths = trendFields.map(field => data.trends[field].length);
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
        const timeRange = document.getElementById('timeRange').value;
        const response = await fetch(`/api/dashboard/data?timeRange=${timeRange}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            debugLog('API error response:', errorData);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error || 'Unknown error'}`);
        }
        
        const data = await response.json();
        debugLog('Raw chart data received:', data);
        
        if (!validateChartDataStructure(data)) {
            throw new Error('Invalid dashboard data structure');
        }
        
        return data;
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

// Initialize charts with validated data
async function initializeCharts() {
    debugLog('Starting chart initialization with registry');
    try {
        // Clean up existing charts
        ['shipmentTrendChart', 'revenueChart', 'statusDistributionChart'].forEach(chartId => {
            debugLog(`Cleanup requested for chart: ${chartId}`);
            destroyChart(chartId);
        });
        
        const data = await getValidatedChartData();
        
        // Initialize shipment trend chart
        const shipmentTrendCtx = document.getElementById('shipmentTrendChart');
        if (shipmentTrendCtx) {
            const shipmentChart = new Chart(shipmentTrendCtx, {
                type: 'line',
                data: {
                    labels: data.trends.labels,
                    datasets: [{
                        label: 'Shipments',
                        data: data.trends.shipments,
                        borderColor: '#4169E1',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            chartRegistry.register('shipmentTrendChart', shipmentChart);
        }
        
        // Initialize revenue chart
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            const revenueChart = new Chart(revenueCtx, {
                type: 'line',
                data: {
                    labels: data.trends.labels,
                    datasets: [{
                        label: 'Revenue',
                        data: data.trends.revenue,
                        borderColor: '#2ecc71',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            chartRegistry.register('revenueChart', revenueChart);
        }
        
        // Initialize status distribution chart
        const statusCtx = document.getElementById('statusDistributionChart');
        if (statusCtx) {
            const statusConfig = {
                labels: ['Pending', 'Processing', 'In Transit', 'Delivered', 'Cancelled'],
                colors: {
                    'Pending': '#f1c40f',      // Yellow
                    'Processing': '#3498db',    // Blue
                    'In Transit': '#e67e22',    // Orange
                    'Delivered': '#2ecc71',     // Green
                    'Cancelled': '#e74c3c'      // Red
                }
            };
            
            const statusData = statusConfig.labels.map(label => {
                const key = label.toLowerCase().replace(' ', '_');
                return data.status_distribution[key] || 0;
            });
            
            const statusChart = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: statusConfig.labels,
                    datasets: [{
                        data: statusData,
                        backgroundColor: statusConfig.labels.map(label => statusConfig.colors[label]),
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '60%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                usePointStyle: true,
                                padding: 20,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    animation: {
                        animateScale: true,
                        animateRotate: true
                    }
                }
            });
            chartRegistry.register('statusDistributionChart', statusChart);
        }
        
        // Update dashboard metrics
        updateDashboardMetrics(data.stats);
        
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
        if (!data || !data.stats || !data.status_distribution) {
            debugLog('Invalid data structure received', data);
            throw new Error('Invalid dashboard data structure');
        }
        
        // Update components
        debugLog('Updating dashboard components');
        await Promise.all([
            updateDashboardMetrics(data.stats),
            updateStatusCounts(data.status_distribution),
            updateCharts(data)
        ]);
        
        debugLog('Dashboard refresh complete');
    } catch (error) {
        debugLog('Error refreshing dashboard data', error);
        showError('Failed to refresh dashboard data. Please try again.');
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

    const { labels, shipments, revenue } = data.trends;
    debugLog('Processing trend data', { labels, shipments, revenue });

    if (!labels || !shipments || !revenue) {
        debugLog('Missing trend data components');
        return;
    }

    // Show all chart canvases
    document.querySelectorAll('.chart-container canvas').forEach(canvas => {
        canvas.style.display = 'block';
    });

    // Update shipment trend chart
    const shipmentChart = chartRegistry.get('shipmentTrendChart');
    if (shipmentChart) {
        debugLog('Updating shipment trend chart');
        const container = document.getElementById('shipmentTrendChart').closest('.chart-container');
        hideChartLoading(container);
        hideChartError(container);
        shipmentChart.data.labels = labels;
        shipmentChart.data.datasets[0].data = shipments;
        shipmentChart.update('none');
        debugLog('Shipment trend chart updated', { labels: labels.length, data: shipments.length });
    }

    // Update revenue chart
    const revenueChart = chartRegistry.get('revenueChart');
    if (revenueChart) {
        debugLog('Updating revenue chart');
        const container = document.getElementById('revenueChart').closest('.chart-container');
        hideChartLoading(container);
        hideChartError(container);
        revenueChart.data.labels = labels;
        revenueChart.data.datasets[0].data = revenue;
        revenueChart.update('none');
        debugLog('Revenue chart updated', { labels: labels.length, data: revenue.length });
    }

    // Update status distribution chart
    const statusChart = chartRegistry.get('statusDistributionChart');
    if (statusChart && data.status_distribution) {
        debugLog('Updating status distribution chart');
        const container = document.getElementById('statusDistributionChart').closest('.chart-container');
        hideChartLoading(container);
        hideChartError(container);
        
        const statusConfig = {
            labels: ['Pending', 'Processing', 'In Transit', 'Delivered', 'Cancelled']
        };
        
        const statusData = statusConfig.labels.map(label => {
            const key = label.toLowerCase().replace(' ', '_');
            return data.status_distribution[key] || 0;
        });
        
        statusChart.data.datasets[0].data = statusData;
        statusChart.update('none');
        
        const total = statusData.reduce((a, b) => a + b, 0);
        debugLog('Status distribution chart updated', {
            data: statusData,
            total: total,
            distribution: statusData.map((value, index) => ({
                status: statusConfig.labels[index],
                count: value,
                percentage: total > 0 ? Math.round((value / total) * 100) : 0
            }))
        });
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
        chart.data.labels = data.trends.labels;
        if (chartId === 'shipmentTrendChart') {
            chart.data.datasets[0].data = data.trends.shipments;
        } else if (chartId === 'revenueChart') {
            chart.data.datasets[0].data = data.trends.revenue;
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
function updateDashboardMetrics(stats) {
    debugLog('Updating dashboard metrics');
    try {
        const metrics = {
            'totalShipments': stats.total_shipments,
            'activeShipments': stats.active_shipments,
            'deliveredShipments': stats.delivered_shipments,
            'totalRevenue': stats.total_revenue,
            'averageRevenue': stats.average_revenue
        };
        
        Object.entries(metrics).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (id.includes('Revenue')) {
                    element.textContent = formatCurrency(value);
                } else {
                    element.textContent = value.toLocaleString();
                }
            }
        });
        
        debugLog('Dashboard metrics updated successfully');
    } catch (error) {
        debugLog('Error updating dashboard metrics', error);
        throw error;
    }
}

// Add new function to update status counts
function updateStatusCounts(statusDistribution) {
    debugLog('Updating status counts', statusDistribution);
    try {
        const statusMapping = {
            'pending': 'pending-count',
            'processing': 'processing-count',
            'in_transit': 'in-transit-count',
            'delivered': 'delivered-count',
            'cancelled': 'cancelled-count'
        };
        
        Object.entries(statusMapping).forEach(([status, elementId]) => {
            const element = document.getElementById(elementId);
            if (element) {
                const count = statusDistribution[status] || 0;
                element.textContent = count.toLocaleString();
                debugLog(`Updated ${status} count to ${count}`);
            } else {
                debugLog(`Element not found for status: ${status}`);
            }
        });
        
        debugLog('Status counts updated successfully');
    } catch (error) {
        debugLog('Error updating status counts', error);
        console.error('Failed to update status counts:', error);
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

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
} 