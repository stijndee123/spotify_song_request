async function addToQueue(uri) {
    alert("Song added to queue");
    try{
        const response = await fetch('/song_queue/api/queue', {
            method: 'POST',
            headers: {
                'Content-type': 'text/plain'
            },
            body: uri
        })
        if (response.ok) {
            console.log("song added")
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to queue song');
        }
    } catch (error) {
        alert('An error has occured adding the song');
        console.error(error);
    }
}