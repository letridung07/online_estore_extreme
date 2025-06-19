// chart_utils.js
// Utility functions for initializing Chart.js charts with common configurations

/**
 * Initialize a Chart.js chart with the provided configuration.
 * @param {string} chartId - The ID of the canvas element to render the chart.
 * @param {string} chartType - The type of chart (e.g., 'line', 'bar').
 * @param {Object} dataConfig - Configuration for chart data including labels and datasets.
 * @param {Object} optionsConfig - Configuration for chart options like scales and responsiveness.
 */
function initChart(chartId, chartType, dataConfig, optionsConfig) {
    const ctx = document.getElementById(chartId).getContext('2d');
    return new Chart(ctx, {
        type: chartType,
        data: {
            labels: dataConfig.labels || [],
            datasets: dataConfig.datasets || []
        },
        options: {
            responsive: true,
            ...optionsConfig
        }
    });
}

/**
 * Helper to create a dataset object for a chart.
 * @param {string} label - Label for the dataset.
 * @param {Array} data - Data points for the dataset.
 * @param {string} borderColor - Border color for the dataset.
 * @param {string} backgroundColor - Background color for the dataset.
 * @param {Object} additionalConfig - Additional configuration options.
 */
function createDataset(label, data, borderColor, backgroundColor, additionalConfig = {}) {
    return {
        label: label,
        data: data,
        borderColor: borderColor,
        backgroundColor: backgroundColor,
        borderWidth: 1,
        fill: typeof additionalConfig.fill !== 'undefined' ? additionalConfig.fill : false,
        tension: additionalConfig.tension || 0.1,
        ...additionalConfig
    };
}
