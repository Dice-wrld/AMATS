// AMATS Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirm dangerous actions
    document.querySelectorAll('.btn-danger').forEach(function(btn) {
        if (!btn.closest('form') || btn.textContent.includes('Delete')) {
            btn.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to proceed?')) {
                    e.preventDefault();
                }
            });
        }
    });

    // Table row click to navigate
    document.querySelectorAll('table tbody tr').forEach(function(row) {
        const link = row.querySelector('a[href]');
        if (link) {
            row.style.cursor = 'pointer';
            row.addEventListener('click', function(e) {
                if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
                    link.click();
                }
            });
        }
    });

    // Search filter functionality
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.closest('form').submit();
            }
        });
    }
});

// Network scan progress indicator
function startNetworkScan() {
    const btn = document.getElementById('scanBtn');
    if (btn) {
        btn.innerHTML = '<span class="spin">⚙</span> Scanning...';
        btn.disabled = true;
    }
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');

        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/,/g, '');
            data = data.replace(/\n/g, ' ').trim();
            row.push(data);
        }
        csv.push(row.join(','));
    }

    const csvContent = 'data:text/csv;charset=utf-8,' + csv.join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
