document.getElementById("synthesize-btn").addEventListener("click", function () {
    const statusText = document.getElementById("status");
    const audioPlayer = document.getElementById("audio-player");

    statusText.textContent = "⏳ Generating AI podcast...";

    fetch("/synthesize", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.speech_url) {
                statusText.textContent = "✅ Podcast ready! Click play.";
                audioPlayer.src = data.speech_url;
                audioPlayer.style.display = "block"; // Show the player
            } else {
                statusText.textContent = "❌ Failed to generate audio.";
            }
        })
        .catch(error => {
            console.error("Error:", error);
            statusText.textContent = "❌ Error generating podcast.";
        });
});
