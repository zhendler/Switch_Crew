document.addEventListener('DOMContentLoaded', function() {
    const commentForm = document.querySelector('.comment-form');
    const commentInput = document.querySelector('.comment-input');
    const commentsContainer = document.querySelector('.comments');

    if (!commentForm || !commentInput || !commentsContainer) {
        console.error('The required element was not found on the page');
        return;
    }

    commentForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const photoId = window.location.pathname.split('/').pop();
        const commentContent = commentInput.value;

        const formData = new FormData();
        formData.append('comment_content', commentContent);

        try {
            const response = await fetch(`/comments/create/${photoId}/`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();

                const newComment = document.createElement('div');
                newComment.classList.add('comment-card');
                newComment.innerHTML = `
                    <div class="comment-header">
                        <div class="comment-author-container">
                            <a href="/page/${data.user.username}">
                                <img src="${data.user.avatar_url}" alt="Avatar" class="comment-avatar">
                            </a>
                            <a href="/page/${data.user.username}">
                                <p class="username">${data.user.username}</p>
                            </a>
                        </div>
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
                    </div>
                    <p class="comment-text" id="comment-text-${data.id}">${data.content}</p>
                `;

                commentsContainer.prepend(newComment);

                commentInput.value = '';
            } else {
                const errorData = await response.json();
                alert(errorData.error || 'Error sending comment');
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        }
    });

    commentsContainer.addEventListener('click', function(event) {
        const button = event.target.closest('.edit-button-comment');
        if (button) {
            const commentId = button.dataset.commentId;
            const commentText = button.dataset.commentText;
            editComment(commentId, commentText);
        }

        const deleteButton = event.target.closest('.delete-button');
        if (deleteButton) {
            const commentId = deleteButton.closest('.delete-form').getAttribute('data-comment-id');
            const commentCard = deleteButton.closest('.comment-card');

            fetch(`/comment/delete/${commentId}/`, {
                method: 'POST',
            })
                .then(response => {
                    if (response.ok) {
                        commentCard.remove();
                    } else {
                        response.json().then(data => alert(data.error || 'Error deleting comment'));
                    }
                })
                .catch(error => console.error('Network error:', error));
        }
    });

    // Функция для редактирования комментария
    function editComment(commentId, commentText) {
        const commentElement = document.getElementById(`comment-text-${commentId}`);
        if (!commentElement) {
            console.error(`Элемент с ID comment-text-${commentId} не найден`);
            return;
        }

        const existingEditField = commentElement.querySelector('.edit-comment-input');
        if (existingEditField) {
            commentElement.innerHTML = commentText;
            return;
        }

        const editField = document.createElement('textarea');
        editField.className = 'edit-comment-input';
        editField.value = commentText;

        const saveButton = document.createElement('button');
        saveButton.className = 'save-button';
        saveButton.textContent = 'Save';

        commentElement.innerHTML = '';
        commentElement.appendChild(editField);
        commentElement.appendChild(saveButton);

        saveButton.addEventListener('click', function() {
            const newContent = editField.value;

            fetch(`/comment/edit/${commentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `comment_content=${encodeURIComponent(newContent)}`
            })
                .then(response => response.json())
                .then(data => {
                    if (data.message === "Comment updated") {
                        commentElement.innerHTML = newContent;

                        const newEditButton = createEditButton(commentId, newContent);
                        commentElement.appendChild(newEditButton);
                    } else {
                        alert('Failed to update comment.');
                    }
                })
                .catch(error => console.error('Error saving comment:', error));
        });
    }
});