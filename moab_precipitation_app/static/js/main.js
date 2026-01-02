let selectedFileId = null;

// File selection change handler
document.getElementById('fileSelect').addEventListener('change', function(e) {
    selectedFileId = e.target.value;
    const option = e.target.options[e.target.selectedIndex];
    
    if (selectedFileId) {
        const rows = option.getAttribute('data-rows');
        const start = option.getAttribute('data-start');
        const end = option.getAttribute('data-end');
        document.getElementById('fileInfo').innerHTML = 
            `<small>Rows: ${rows} | Date Range: ${start} to ${end}</small>`;
    } else {
        document.getElementById('fileInfo').innerHTML = '';
    }
});

// Generate all checkbox handler
document.getElementById('generateAll').addEventListener('change', function(e) {
    const plotOptions = document.getElementById('plotOptions');
    plotOptions.style.display = e.target.checked ? 'none' : 'block';
});

// Comparison toggle handler
document.getElementById('enableComparison').addEventListener('change', function(e) {
    const comparisonOptions = document.getElementById('comparisonOptions');
    comparisonOptions.style.display = e.target.checked ? 'block' : 'none';
});

function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const uploadStatus = document.getElementById('uploadStatus');
    const uploadSpinner = document.getElementById('uploadSpinner');
    
    if (!file) {
        uploadStatus.innerHTML = '<div class="alert alert-warning">Please select a file</div>';
        return;
    }
    
    uploadSpinner.classList.remove('d-none');
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        // Check if response is OK
        if (!response.ok) {
            // Try to parse as JSON, but if it fails, return text
            return response.text().then(text => {
                try {
                    return Promise.reject(JSON.parse(text));
                } catch {
                    return Promise.reject({error: text || `Server error: ${response.status} ${response.statusText}`});
                }
            });
        }
        return response.json();
    })
    .then(data => {
        uploadSpinner.classList.add('d-none');
        if (data.success) {
            uploadStatus.innerHTML = 
                `<div class="alert alert-success">
                    <strong>Success!</strong> File "${data.filename}" uploaded successfully.<br>
                    Rows: ${data.rows_count} | Date Range: ${data.date_range}
                </div>`;
            fileInput.value = '';
            // Reload page after 2 seconds to show new file
            setTimeout(() => location.reload(), 2000);
        } else {
            uploadStatus.innerHTML = `<div class="alert alert-danger">${data.error || 'Unknown error'}</div>`;
        }
    })
    .catch(error => {
        uploadSpinner.classList.add('d-none');
        const errorMsg = error.error || error.message || 'Unknown error occurred';
        uploadStatus.innerHTML = `<div class="alert alert-danger">Error: ${errorMsg}</div>`;
    });
}

function generatePlots() {
    if (!selectedFileId) {
        alert('Please select a file from the database');
        return;
    }
    
    // Validate that the selected file ID exists in the dropdown
    const fileSelect = document.getElementById('fileSelect');
    const selectedOption = fileSelect.options[fileSelect.selectedIndex];
    if (!selectedOption || selectedOption.value !== selectedFileId || selectedOption.value === '') {
        alert('The selected file is no longer available. Please refresh the page and select a file again.');
        location.reload();
        return;
    }
    
    // Get selected months
    const months = Array.from(document.querySelectorAll('.month-check:checked'))
        .map(cb => parseInt(cb.value));
    
    // Get selected seasons
    const seasons = Array.from(document.querySelectorAll('.season-check:checked'))
        .map(cb => cb.value);
    
    // Get plot types
    const generateAll = document.getElementById('generateAll').checked;
    const plotTypes = generateAll ? [] : 
        Array.from(document.querySelectorAll('.plot-check:checked'))
            .map(cb => cb.value);
    
    if (!generateAll && plotTypes.length === 0) {
        alert('Please select at least one plot type or check "Generate All Plots"');
        return;
    }
    
    // Get comparison settings
    const enableComparison = document.getElementById('enableComparison').checked;
    const opStart = document.getElementById('opStart').value;
    const opEnd = document.getElementById('opEnd').value;
    const climStart = document.getElementById('climStart').value;
    const climEnd = document.getElementById('climEnd').value;
    
    const data = {
        file_id: parseInt(selectedFileId),
        months: months,
        seasons: seasons,
        plot_types: plotTypes,
        generate_all: generateAll,
        enable_comparison: enableComparison,
        op_start: opStart,
        op_end: opEnd,
        clim_start: climStart,
        clim_end: climEnd
    };
    
    const generateSpinner = document.getElementById('generateSpinner');
    const resultsDiv = document.getElementById('results');
    
    generateSpinner.classList.remove('d-none');
    resultsDiv.innerHTML = '<div class="col-12"><div class="alert alert-info">Generating plots, please wait...</div></div>';
    
    fetch('/process', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(async response => {
        // Check if response is ok before parsing JSON
        if (!response.ok) {
            // Try to get error message from response
            const text = await response.text();
            try {
                const json = JSON.parse(text);
                throw new Error(json.error || `Server error: ${response.status}`);
            } catch (e) {
                if (e instanceof SyntaxError) {
                    // Not JSON, return the text or a generic error
                    throw new Error(`Server error (${response.status}): ${text.substring(0, 200) || 'Unknown error'}`);
                }
                throw e;
            }
        }
        
        // Get response text first to check if it's empty
        const text = await response.text();
        if (!text || text.trim() === '') {
            throw new Error('Empty response from server');
        }
        
        try {
            return JSON.parse(text);
        } catch (e) {
            console.error('JSON parse error. Response text:', text.substring(0, 500));
            throw new Error(`Invalid JSON response: ${e.message}`);
        }
    })
    .then(data => {
        generateSpinner.classList.add('d-none');
        if (data.success && data.plots) {
            displayPlots(data.plots, data.comparison_plots, data.comparison_stats);
        } else if (data.error) {
            resultsDiv.innerHTML = `<div class="col-12"><div class="alert alert-danger">Error: ${data.error}</div></div>`;
        } else {
            resultsDiv.innerHTML = '<div class="col-12"><div class="alert alert-warning">No plots generated</div></div>';
        }
    })
    .catch(error => {
        generateSpinner.classList.add('d-none');
        resultsDiv.innerHTML = `<div class="col-12"><div class="alert alert-danger">Error: ${error.message}</div></div>`;
        console.error('Error details:', error);
    });
}

function displayPlots(plots, comparisonPlots = {}, comparisonStats = {}) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';
    
    // Group by precipitation type
    const rainPlots = {};
    const snowPlots = {};
    
    Object.keys(plots).forEach(key => {
        if (key.startsWith('rain_') && plots[key]) {
            rainPlots[key.replace('rain_', '')] = plots[key];
        } else if (key.startsWith('snow_') && plots[key]) {
            snowPlots[key.replace('snow_', '')] = plots[key];
        }
    });
    
    // Display rain plots
    if (Object.keys(rainPlots).length > 0) {
        const rainSection = document.createElement('div');
        rainSection.className = 'col-12 mb-4';
        rainSection.innerHTML = '<div class="card shadow"><div class="card-header bg-danger text-white"><h3 class="mb-0">Rain Plots</h3></div></div>';
        resultsDiv.appendChild(rainSection);
        
        const rainContainer = document.createElement('div');
        rainContainer.className = 'row p-3';
        rainSection.querySelector('.card').appendChild(rainContainer);
        
        Object.keys(rainPlots).forEach(plotName => {
            const plotDiv = createPlotCard('Rain', plotName, rainPlots[plotName]);
            rainContainer.appendChild(plotDiv);
        });
    }
    
    // Display snow plots
    if (Object.keys(snowPlots).length > 0) {
        const snowSection = document.createElement('div');
        snowSection.className = 'col-12 mb-4';
        snowSection.innerHTML = '<div class="card shadow"><div class="card-header bg-info text-white"><h3 class="mb-0">Snow Plots</h3></div></div>';
        resultsDiv.appendChild(snowSection);
        
        const snowContainer = document.createElement('div');
        snowContainer.className = 'row p-3';
        snowSection.querySelector('.card').appendChild(snowContainer);
        
        Object.keys(snowPlots).forEach(plotName => {
            const plotDiv = createPlotCard('Snow', plotName, snowPlots[plotName]);
            snowContainer.appendChild(plotDiv);
        });
    }
    
    // Display comparison plots if available
    if (Object.keys(comparisonPlots).length > 0) {
        const compSection = document.createElement('div');
        compSection.className = 'col-12 mb-4';
        compSection.innerHTML = '<div class="card shadow"><div class="card-header bg-success text-white"><h3 class="mb-0">Period Comparison Analysis</h3></div></div>';
        resultsDiv.appendChild(compSection);
        
        const compContainer = document.createElement('div');
        compContainer.className = 'p-3';
        compSection.querySelector('.card').appendChild(compContainer);
        
        // Add statistics table
        if (Object.keys(comparisonStats).length > 0) {
            const statsDiv = document.createElement('div');
            statsDiv.className = 'mb-4';
            statsDiv.innerHTML = createStatsTable(comparisonStats);
            compContainer.appendChild(statsDiv);
        }
        
        // Add comparison plots
        const plotsRow = document.createElement('div');
        plotsRow.className = 'row';
        compContainer.appendChild(plotsRow);
        
        Object.keys(comparisonPlots).forEach(plotKey => {
            if (comparisonPlots[plotKey]) {
                const plotDiv = createComparisonPlotCard(plotKey, comparisonPlots[plotKey]);
                plotsRow.appendChild(plotDiv);
            }
        });
    }
    
    if (Object.keys(rainPlots).length === 0 && Object.keys(snowPlots).length === 0 && Object.keys(comparisonPlots).length === 0) {
        resultsDiv.innerHTML = '<div class="col-12"><div class="alert alert-warning">No plots were generated. Please check your selections.</div></div>';
    }
}

function createStatsTable(stats) {
    let html = '<h5>Statistical Test Results</h5><div class="table-responsive"><table class="table table-bordered table-sm"><thead><tr><th>Precipitation Type</th><th>Operating Mean (mm)</th><th>Climatology Mean (mm)</th><th>t-test p-value</th><th>Mann-Whitney p-value</th><th>KS-test p-value</th><th>Cohen\'s d</th><th>Significant?</th></tr></thead><tbody>';
    
    Object.keys(stats).forEach(precipType => {
        const s = stats[precipType];
        const significant = s.t_test_pvalue < 0.05 || s.mannwhitney_pvalue < 0.05;
        const sigText = significant ? '<span class="badge bg-danger">Yes</span>' : '<span class="badge bg-secondary">No</span>';
        
        html += `<tr>
            <td><strong>${precipType.charAt(0).toUpperCase() + precipType.slice(1)}</strong></td>
            <td>${s.operating_mean.toFixed(2)} ± ${s.operating_std.toFixed(2)}</td>
            <td>${s.climatology_mean.toFixed(2)} ± ${s.climatology_std.toFixed(2)}</td>
            <td>${s.t_test_pvalue.toFixed(4)}</td>
            <td>${s.mannwhitney_pvalue.toFixed(4)}</td>
            <td>${s.ks_test_pvalue.toFixed(4)}</td>
            <td>${s.cohens_d.toFixed(3)}</td>
            <td>${sigText}</td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    html += '<div class="alert alert-info mt-3"><small><strong>Interpretation:</strong> p &lt; 0.05 indicates statistically significant difference. Cohen\'s d: |d| &lt; 0.2 (negligible), 0.2-0.5 (small), 0.5-0.8 (medium), &gt; 0.8 (large)</small></div>';
    
    return html;
}

function createComparisonPlotCard(plotKey, imgBase64) {
    const col = document.createElement('div');
    col.className = 'col-lg-6 col-md-12 mb-4';
    
    // Format plot name
    let displayName = plotKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    if (plotKey.includes('comparison_histogram')) {
        displayName = 'Distribution Comparison';
    } else if (plotKey.includes('anomaly')) {
        displayName = 'Anomaly Plot';
    }
    
    const precipType = plotKey.startsWith('rain_') ? 'Rain' : 'Snow';
    
    col.innerHTML = `
        <div class="card h-100 shadow-sm">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">${precipType} - ${displayName}</h5>
            </div>
            <div class="card-body">
                <img src="data:image/png;base64,${imgBase64}" class="img-fluid" alt="${displayName}">
            </div>
        </div>
    `;
    return col;
}

function createPlotCard(precipType, plotName, imgBase64) {
    const col = document.createElement('div');
    col.className = 'col-lg-6 col-md-12 mb-4';
    
    // Format plot name for display
    const displayName = plotName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    
    col.innerHTML = `
        <div class="card h-100 shadow-sm">
            <div class="card-header bg-secondary text-white">
                <h5 class="mb-0">${precipType} - ${displayName}</h5>
            </div>
            <div class="card-body">
                <img src="data:image/png;base64,${imgBase64}" class="img-fluid" alt="${displayName}">
            </div>
        </div>
    `;
    return col;
}

