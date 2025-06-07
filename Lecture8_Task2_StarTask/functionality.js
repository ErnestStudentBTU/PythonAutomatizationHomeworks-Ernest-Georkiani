document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const imageUpload = document.getElementById('imageUpload');
    const modelSelect = document.getElementById('modelSelect');
    const submitBtn = document.getElementById('submitBtn');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const previewImage = document.getElementById('previewImage');
    const modelResults = document.getElementById('modelResults');
    const errorDiv = document.getElementById('error');
    
    const API_ENDPOINT = 'https://your-api-gateway-url.amazonaws.com/prod/process-image';
    
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        resultsDiv.classList.add('hidden');
        errorDiv.classList.add('hidden');
        
        loadingDiv.classList.remove('hidden');
        submitBtn.disabled = true;
        
        const file = imageUpload.files[0];
        const modelId = modelSelect.value;
        
        if (!file || !modelId) {
            showError('Please select both an image and a model');
            return;
        }
        
        try {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
            };
            reader.readAsDataURL(file);
            
            const formData = new FormData();
            formData.append('image', file);
            formData.append('model', modelId);
            
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`API request failed with status ${response.status}`);
            }
            
            const data = await response.json();
            
            displayResults(data);
            
        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'An error occurred while processing your image');
        } finally {
            loadingDiv.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });
    
    function displayResults(data) {
        previewImage.src = data.imageUrl || previewImage.src;
        
        modelResults.innerHTML = '';
        
        if (data.predictions) {
            const heading = document.createElement('h3');
            heading.textContent = 'Model Predictions:';
            modelResults.appendChild(heading);
            
            const list = document.createElement('ul');
            data.predictions.forEach(pred => {
                const item = document.createElement('li');
                item.textContent = `${pred.label}: ${(pred.score * 100).toFixed(2)}%`;
                list.appendChild(item);
            });
            modelResults.appendChild(list);
        } else if (data.result) {
            const para = document.createElement('p');
            para.textContent = data.result;
            modelResults.appendChild(para);
        }
        
        resultsDiv.classList.remove('hidden');
    }
    
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    }
});