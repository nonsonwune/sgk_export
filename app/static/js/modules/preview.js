// Image Modal Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Setup image view buttons
    document.querySelectorAll('.view-images-btn').forEach(button => {
        button.addEventListener('click', function() {
            const imageUrl = this.getAttribute('data-image');
            const modal = document.getElementById('imageModal');
            const modalImage = document.getElementById('modalImage');
            const imageLoading = document.getElementById('imageLoading');
            const imageError = document.getElementById('imageError');
            
            console.log('Loading image:', imageUrl);
            modalImage.style.display = 'none';
            imageLoading.style.display = 'flex';
            imageError.style.display = 'none';
            modalImage.src = imageUrl;
            modal.style.display = 'block';
        });
    });

    // Setup modal close button
    document.querySelector('.close-modal').addEventListener('click', function() {
        document.getElementById('imageModal').style.display = 'none';
    });

    // Setup modal background click to close
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('imageModal');
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}); 