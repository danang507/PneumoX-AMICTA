document.getElementById('formsubmit').addEventListener('input', function() {
    var form = this;
    var isValid = form.checkValidity();
    document.getElementById('submitBtn').disabled = !isValid;
});

// Saat form di-submit
document.getElementById('formsubmit').addEventListener('submit', function(event) {
    event.preventDefault(); // Mencegah submit form secara default
    $('#confirmationModal').modal('show'); // Menampilkan modal konfirmasi
});

// Saat tombol "Ya" pada modal konfirmasi ditekan
document.getElementById('confirmSubmit').addEventListener('click', function() {
    document.getElementById('formsubmit').submit(); // Submit form
});

