function confirmDelete(event) {
    event.preventDefault(); // Mencegah submit form secara default
    $('#confirmationModal').modal('show'); // Menampilkan modal konfirmasi
}

function deleteConfirmed() {
    document.getElementById('deleteForm').submit(); // Submit form penghapusan
}
