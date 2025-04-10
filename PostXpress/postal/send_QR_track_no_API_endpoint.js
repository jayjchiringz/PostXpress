function handleQRScan(trackingNumber) {
    // Send the scanned tracking number to the server via POST
    fetch('/scan_qr_code/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'tracking_number': trackingNumber
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.success);  // Show success message
        } else if (data.error) {
            alert(data.error);  // Show error message
        }
    })
    .catch(error => console.error('Error:', error));
}
