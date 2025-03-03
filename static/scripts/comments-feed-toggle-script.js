function toggleComments(button) {
    const container = button.nextElementSibling;
    const isExpanded = container.classList.contains('expanded');
    button.classList.toggle('expanded');

    // Toggle the expanded class
    container.classList.toggle('expanded');

    // Rotate the arrow icon
    const arrow = button.querySelector('img');
    arrow.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
}

// Initialize comment forms
document.addEventListener('DOMContentLoaded', function() {
    const commentForms = document.querySelectorAll('.feed-comment-form');

    commentForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const photoId = this.dataset.photoId;
            const input = this.querySelector('.feed-comment-input');
            const content = input.value.trim();

            if (!content) return;

            const formData = new FormData();
            formData.append('comment_content', content);

            try {
                const response = await fetch(`/comments/create/${photoId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                                     document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1],
                    },
                    body: formData,
                });

                if (response.ok) {
                    const data = await response.json();

                    // Create new comment element
                    const commentElement = document.createElement('div');
                    commentElement.className = 'feed-comment-card';
                    commentElement.innerHTML = `
                        <a href="/page/${data.user.username}">
                            <img src="${data.user.avatar_url}" alt="Avatar" class="feed-comment-avatar">
                        </a>
                        <div class="feed-comment-content">
                            <a href="/page/${data.user.username}" class="feed-comment-author">
                                ${data.user.username}
                            </a>
                            <span class="feed-comment-text">${data.content}</span>
                        </div>
                        ${data.permissions.can_edit ? `
                            <div class="feed-comment-actions">
                                <button class="feed-comment-action edit-button-comment" data-comment-id="${data.id}" data-comment-text="${data.content}">
                                    <img src="/static/images/pencil.png" alt="Edit">
                                </button>
                                <button class="feed-comment-action delete-button" data-comment-id="${data.id}">
                                    <img src="/static/images/recycling-bin.png" alt="Delete">
                                </button>
                            </div>
                        ` : ''}
                    `;

                    // Add the new comment to the container
                    const commentsContainer = this.closest('.feed-comments-container');
                    commentsContainer.insertBefore(commentElement, this.nextSibling);

                    // Clear the input
                    input.value = '';

                    // Update comment count
                    const toggleButton = commentsContainer.previousElementSibling;
                    const countSpan = toggleButton.querySelector('.comment-count');
                    const currentCount = parseInt(countSpan.textContent);
                    countSpan.textContent = `${currentCount + 1} comments`;
                }
            } catch (error) {
                console.error('Error posting comment:', error);
            }
        });
    });
});