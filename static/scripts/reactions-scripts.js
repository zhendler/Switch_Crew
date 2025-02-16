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

            // Find the specific photo card containing the clicked reaction
            const photoCards = document.querySelectorAll('.photo-card');
            let targetPhotoCard;

            for (const card of photoCards) {
                const reactionContainer = card.querySelector(`.reaction-container[onclick="addReaction(${reactionId}, ${photoId})"]`);
                if (reactionContainer) {
                    targetPhotoCard = card;
                    break;
                }
            }

            if (targetPhotoCard) {
                // Update reaction counts only for this specific photo
                for (let i = 1; i <= 8; i++) {
                    const reactionCountElement = targetPhotoCard.querySelector(`.reaction-container[onclick="addReaction(${i}, ${photoId})"] .reaction-count`);
                    if (reactionCountElement) {
                        reactionCountElement.textContent = data.reaction_counts[i];
                    }
                }

                // Remove 'active' class only from reactions within this photo card
                const activeReactions = targetPhotoCard.querySelectorAll('.reaction-circle.active');
                activeReactions.forEach(el => {
                    el.classList.remove('active');
                });

                // Add 'active' class to the selected reaction for this photo
                if (data.current_reaction !== null) {
                    const reactionCircle = targetPhotoCard.querySelector(`.reaction-container[onclick="addReaction(${reactionId}, ${photoId})"] .reaction-circle`);
                    if (reactionCircle) {
                        reactionCircle.classList.add('active');
                    }
                }
            }
        } else {
            console.error('Failed to process reaction:', response.statusText);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}