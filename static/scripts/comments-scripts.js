document.addEventListener('DOMContentLoaded', function() {
    const commentForm = document.querySelector('.comment-form');
    const commentInput = document.querySelector('.comment-input');
    const commentsContainer = document.querySelector('.comments');

    if (!commentsContainer) {
        const noCommentsElement = document.querySelector('.no-comments');
        if (noCommentsElement) {
            noCommentsElement.remove();
        }
        const newCommentsContainer = document.createElement('div');
        newCommentsContainer.className = 'comments';
        commentForm.parentNode.insertBefore(newCommentsContainer, commentForm.nextSibling);
    }

    async function handleCommentEdit(commentId, currentContent) {
        const commentText = document.querySelector(`#comment-text-${commentId}`);
        const originalContent = currentContent;

        const editForm = document.createElement('div');
        editForm.className = 'edit-form';
        editForm.innerHTML = `
            <textarea class="comment-input">${originalContent}</textarea>
            <div class="edit-buttons">
                <button type="button" class="save-button">Save</button>
                <button type="button" class="cancel-button">Cancel</button>
            </div>
        `;

        commentText.style.display = 'none';
        commentText.parentNode.insertBefore(editForm, commentText);

        const textarea = editForm.querySelector('textarea');
        const saveButton = editForm.querySelector('.save-button');
        const cancelButton = editForm.querySelector('.cancel-button');

        cancelButton.addEventListener('click', () => {
            editForm.remove();
            commentText.style.display = 'block';
        });

        saveButton.addEventListener('click', async () => {
            const newContent = textarea.value.trim();
            if (!newContent) return;

            try {
                const formData = new FormData();
                formData.append('comment_content', newContent);

                const response = await fetch(`/comment/edit/${commentId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                                     document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1],
                    },
                    body: formData,
                    credentials: 'include'
                });

                if (response.ok) {
                    commentText.textContent = newContent;
                    const editButton = document.querySelector(`[data-comment-id="${commentId}"]`);
                    if (editButton) {
                        editButton.setAttribute('data-comment-text', newContent);
                    }
                    editForm.remove();
                    commentText.style.display = 'block';
                } else {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to update comment');
                }
            } catch (error) {
                console.error('Error updating comment:', error);
                alert('Failed to update comment. Please try again.');
            }
        });

        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    }

    commentForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const photoId = window.location.pathname.split('/').pop();
        const commentContent = commentInput.value.trim();

        if (!commentContent) {
            return;
        }

        const formData = new FormData();
        formData.append('comment_content', commentContent);

        try {
            const response = await fetch(`/comments/create/${photoId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                                 document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1],
                },
                body: formData,
                credentials: 'include'
            });

            const data = await response.json();

            if (response.ok) {
                const commentElement = document.createElement('div');
                commentElement.className = 'comment-card';
                commentElement.innerHTML = `
                    <div class="comment-header">
                        <div class="comment-author-container">
                            <a href="/page/${data.user.username}">
                                <img src="${data.user.avatar_url}" alt="Avatar" class="comment-avatar">
                            </a>
                            <a href="/page/${data.user.username}">
                                <p class="username">${data.user.username}</p>
                            </a>
                        </div>
                        ${data.permissions.can_edit ? `
                            <div class="action-buttons">
                                <button class="edit-button-comment" data-comment-id="${data.id}" data-comment-text="${data.content}">
                                    <img src="/static/images/pencil.png" alt="Edit Icon" class="action-icon">
                                </button>
                                <form class="delete-form" data-comment-id="${data.id}">
                                    <button type="button" class="delete-button">
                                        <img src="/static/images/recycling-bin.png" alt="Trash Icon" class="action-icon">
                                    </button>
                                </form>
                            </div>
                        ` : data.permissions.can_delete ? `
                            <form class="delete-form" data-comment-id="${data.id}">
                                <button type="button" class="delete-button">
                                    <img src="/static/images/recycling-bin.png" alt="Trash Icon" class="action-icon">
                                </button>
                            </form>
                        ` : ''}
                    </div>
                    <p class="comment-text" id="comment-text-${data.id}">${data.content}</p>
                `;

                const commentsSection = document.querySelector('.comments');
                if (commentsSection.children.length === 0) {
                    commentsSection.appendChild(commentElement);
                } else {
                    commentsSection.insertBefore(commentElement, commentsSection.firstChild);
                }

                commentInput.value = '';

                const noComments = document.querySelector('.no-comments');
                if (noComments) {
                    noComments.remove();
                }
            } else {
                throw new Error(data.error || 'Failed to post comment');
            }
        } catch (error) {
            console.error('Error details:', error);
            alert('Failed to post comment. Please try again. Error: ' + error.message);
        }
    });

    commentsContainer.addEventListener('click', function(event) {
        const editButton = event.target.closest('.edit-button-comment');
        if (editButton) {
            const commentId = editButton.dataset.commentId;
            const commentText = editButton.dataset.commentText;
            handleCommentEdit(commentId, commentText);
        }

        const deleteButton = event.target.closest('.delete-button');
        if (deleteButton) {
            const commentId = deleteButton.closest('.delete-form').getAttribute('data-comment-id');
            const commentCard = deleteButton.closest('.comment-card');

            fetch(`/comment/delete/${commentId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                                 document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1],
                },
                credentials: 'include'
            })
            .then(response => {
                if (response.ok) {
                    commentCard.remove();

                    const commentsSection = document.querySelector('.comments');
                    if (commentsSection && commentsSection.children.length === 0) {
                        const noCommentsElement = document.createElement('p');
                        noCommentsElement.className = 'no-comments';
                        noCommentsElement.textContent = 'No comments yet.';
                        commentsSection.parentNode.insertBefore(noCommentsElement, commentsSection);
                        commentsSection.remove();
                    }
                } else {
                    response.json().then(data => alert(data.error || 'Error deleting comment'));
                }
            })
            .catch(error => console.error('Network error:', error));
        }
    });
});