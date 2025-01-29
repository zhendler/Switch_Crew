async function addReaction(reactionId, photoId) {
    try {
        const response = await fetch('/reaction/add_reaction/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({
                reaction_id: reactionId,
                photo_id: photoId
            })
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Reaction processed:', data);

            for (let i = 1; i <= 8; i++) {
                const reactionCountElement = document.querySelector(`.reaction-container[onclick="addReaction(${i}, ${photoId})"] .reaction-count`);
                if (reactionCountElement) {
                    reactionCountElement.textContent = data.reaction_counts[i];
                }
            }

            document.querySelectorAll('.reaction-circle.active').forEach(el => {
                el.classList.remove('active');
            });

            if (data.current_reaction !== null) {
                const reactionCircle = document.querySelector(`.reaction-container[onclick="addReaction(${reactionId}, ${photoId})"] .reaction-circle`);
                if (reactionCircle) {
                    reactionCircle.classList.add('active');
                }
            }
        } else {
            console.error('Failed to process reaction:', response.statusText);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}