document.getElementById('synthesizeButton').addEventListener('click', function() {
    fetch('/synthesize', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            // Update dialogue
            const dialogueDiv = document.getElementById('dialogue');
            dialogueDiv.innerHTML = '';
            data.dialogue.forEach(line => {
                const p = document.createElement('p');
                p.textContent = line;
                dialogueDiv.appendChild(p);
            });

            // Update audio sources
            document.getElementById('alphaAudio').src = data.alpha_speech_url;
            document.getElementById('betaAudio').src = data.beta_speech_url;
        })
        .catch(error => console.error('Error:', error));
});
