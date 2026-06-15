document.addEventListener('DOMContentLoaded', () => {
    const radioButtons = document.querySelectorAll('input[name="mode"]');
    const crossfadeGroup = document.getElementById('crossfade-group');
    const loopsInput = document.getElementById('loops');
    const crossfadeInput = document.getElementById('crossfade');
    const loopCountVal = document.getElementById('loop-count-val');
    const crossfadeVal = document.getElementById('crossfade-val');
    const audioOffsetInput = document.getElementById('audio-offset');
    const audioOffsetVal = document.getElementById('audio-offset-val');
    const resultSection = document.getElementById('result-section');
    const resultMessage = document.getElementById('result-message');
    
    const selectInputBtn = document.getElementById('select-input-btn');
    const inputPathField = document.getElementById('input-path');
    const inputPathDisplay = document.getElementById('input-path-display');
    
    const selectPathBtn = document.getElementById('select-path-btn');
    const outputPathInput = document.getElementById('output-path');
    const outputPathDisplay = document.getElementById('output-path-display');
    const generateBtn = document.getElementById('generate-btn');
    
    const progressContainer = document.getElementById('progress-container');
    const progressStatus = document.getElementById('progress-status');
    const progressPercent = document.getElementById('progress-percent');
    const progressBar = document.getElementById('progress-bar');

    // UI Updates
    radioButtons.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'crossdissolve') {
                crossfadeGroup.style.display = 'block';
            } else {
                crossfadeGroup.style.display = 'none';
            }
        });
    });

    loopsInput.addEventListener('input', (e) => {
        loopCountVal.textContent = e.target.value;
    });

    crossfadeInput.addEventListener('input', (e) => {
        crossfadeVal.textContent = e.target.value;
    });

    audioOffsetInput.addEventListener('input', (e) => {
        audioOffsetVal.textContent = e.target.value;
    });

    // Native Dialog for Input File
    selectInputBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('http://localhost:8000/select-input');
            const data = await res.json();
            if (data.path) {
                inputPathField.value = data.path;
                inputPathDisplay.textContent = data.path;
                resultSection.style.display = 'none';
                selectInputBtn.style.borderColor = 'var(--primary)';
                selectInputBtn.style.background = 'rgba(59, 130, 246, 0.1)';
            }
        } catch (err) {
            alert('Konnte Dateidialog nicht öffnen.');
        }
    });

    // Native Dialog for Output Path
    selectPathBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('http://localhost:8000/select-path');
            const data = await res.json();
            if (data.path) {
                outputPathInput.value = data.path;
                outputPathDisplay.textContent = data.path;
            }
        } catch (err) {
            alert('Konnte Speicherdialog nicht öffnen.');
        }
    });

    // API Submit
    generateBtn.addEventListener('click', async () => {
        if (!inputPathField.value) {
            alert('Bitte wähle zuerst ein Eingabevideo aus.');
            return;
        }
        if (!outputPathInput.value) {
            alert('Bitte wähle einen Speicherort aus.');
            return;
        }

        const mode = document.querySelector('input[name="mode"]:checked').value;
        const loops = loopsInput.value;
        const crossfade = crossfadeInput.value;
        const audioOffset = audioOffsetInput.value;
        const codec = document.getElementById('codec-select').value;

        const formData = new URLSearchParams();
        formData.append('input_path', inputPathField.value);
        formData.append('output_path', outputPathInput.value);
        formData.append('mode', mode);
        formData.append('loops', loops);
        formData.append('crossfade_duration', crossfade);
        formData.append('audio_offset', audioOffset);
        formData.append('codec', codec);

        // UI Loading state
        const btnText = generateBtn.querySelector('.btn-text');
        generateBtn.disabled = true;
        generateBtn.style.opacity = '0.7';
        btnText.textContent = 'Server startet Task...';
        resultSection.style.display = 'none';
        
        progressContainer.style.display = 'block';
        progressStatus.textContent = 'Verbinde...';
        progressPercent.textContent = '0%';
        progressBar.style.width = '0%';

        try {
            const response = await fetch('http://localhost:8000/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            const result = await response.json();
            
            if (response.ok && result.task_id) {
                btnText.textContent = 'Rendern läuft...';
                
                // Start SSE
                const eventSource = new EventSource(`http://localhost:8000/progress/${result.task_id}`);
                
                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    progressBar.style.width = `${data.progress}%`;
                    progressPercent.textContent = `${data.progress}%`;
                    progressStatus.textContent = data.status;
                };
                
                eventSource.addEventListener('done', function(event) {
                    eventSource.close();
                    generateBtn.disabled = false;
                    generateBtn.style.opacity = '1';
                    btnText.textContent = 'Video Generieren';
                    
                    resultSection.style.display = 'block';
                    resultMessage.style.color = 'var(--accent-1)';
                    resultMessage.textContent = '✅ Video erfolgreich verarbeitet und gespeichert!';
                });
                
                eventSource.addEventListener('error', function(event) {
                    eventSource.close();
                    generateBtn.disabled = false;
                    generateBtn.style.opacity = '1';
                    btnText.textContent = 'Video Generieren';
                    
                    alert('Fehler beim Rendern: ' + event.data);
                    progressStatus.textContent = 'Fehlgeschlagen!';
                    progressStatus.style.color = '#EF4444';
                });
                
            } else {
                throw new Error(result.error || 'Unbekannter Fehler');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Fehler: ' + error.message);
            
            generateBtn.disabled = false;
            generateBtn.style.opacity = '1';
            btnText.textContent = 'Video Generieren';
            progressContainer.style.display = 'none';
        }
    });
});
