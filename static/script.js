document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('translation-form');
    const submitButton = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('result');
    const videoContainer = document.getElementById('video-container');
    const video = document.getElementById('translated-video');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const youtubeUrl = document.getElementById('youtube_url').value;
        const targetLanguage = document.getElementById('target_language').value;
        
        if (!isValidYoutubeUrl(youtubeUrl)) {
            showMessage('Lütfen geçerli bir YouTube URL\'si girin.', 'error');
            return;
        }
        
        showMessage('Video işleniyor, lütfen bekleyin...', 'info');
        submitButton.disabled = true;
        videoContainer.style.display = 'none';
        
        fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'youtube_url': youtubeUrl,
                'target_language': targetLanguage
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            showMessage('Video başarıyla çevrildi!', 'success');
            video.src = `/video/${encodeURIComponent(data.video_path)}`;
            videoContainer.style.display = 'block';
        })
        .catch(error => {
            showMessage(error.message, 'error');
        })
        .finally(() => {
            submitButton.disabled = false;
        });
    });

    function isValidYoutubeUrl(url) {
        const regex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/;
        return regex.test(url);
    }

    function showMessage(message, type) {
        resultDiv.textContent = message;
        resultDiv.className = type;
    }
});