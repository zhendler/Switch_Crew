document.addEventListener('DOMContentLoaded', function() {
    async function handleCommentEdit(commentId, currentContent, commentElement) {
        const commentContainer = commentElement.querySelector('.feed-comment-content');
        const commentText = commentElement.querySelector('.feed-comment-text');
        const existingEditForm = commentElement.querySelector('.edit-form');

        if (existingEditForm) {
            existingEditForm.remove();
            commentText.style.display = 'inline';
            return;
        }

        const editForm = document.createElement('div');
        editForm.className = 'edit-form';
        editForm.innerHTML = `
            <textarea class="feed-comment-input">${currentContent}</textarea>
            <div class="edit-buttons">
                <button type="button" class="save-button">Save</button>
            </div>
        `;

        commentText.style.display = 'none';
        commentContainer.appendChild(editForm);

        const textarea = editForm.querySelector('textarea');
        const saveButton = editForm.querySelector('.save-button');

        saveButton.addEventListener('click', async () => {
            const newContent = textarea.value.trim();
            if (!newContent) return;

            try {
                const formData = new FormData();
                formData.append('comment_content', newContent);

                const response = await fetch(`/comments/edit/${commentId}/`, {
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
                    const editButton = commentElement.querySelector('.edit-button-comment');
                    if (editButton) {
                        editButton.setAttribute('data-comment-text', newContent);
                    }
                    editForm.remove();
                    commentText.style.display = 'inline';
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

    async function handleCommentDelete(commentId, commentElement) {
        try {
            const response = await fetch(`/comments/delete/${commentId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                                 document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1],
                },
                credentials: 'include'
            });

            if (response.ok) {
                // Найдем контейнер и кнопку переключения до удаления элемента
                const commentsContainer = commentElement.closest('.feed-comments-container');
                const toggleButton = commentsContainer ? commentsContainer.previousElementSibling : null;
                const countSpan = toggleButton ? toggleButton.querySelector('.comment-count') : null;

                // Удаляем комментарий
                commentElement.remove();

                // Обновляем счетчик только если нашли все необходимые элементы
                if (countSpan) {
                    const currentText = countSpan.textContent;
                    const currentCount = parseInt(currentText);
                    if (!isNaN(currentCount)) {
                        countSpan.textContent = `${Math.max(0, currentCount - 1)} comments`;
                    }
                }
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Failed to delete comment');
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            // Не показываем alert, так как комментарий все равно удален
        }
    }

    // Add click event listeners for edit and delete buttons
    document.addEventListener('click', function(event) {
        const editButton = event.target.closest('.edit-button-comment');
        if (editButton) {
            const commentId = editButton.dataset.commentId;
            const commentText = editButton.dataset.commentText;
            const commentElement = editButton.closest('.feed-comment-card');
            if (commentElement) {
                handleCommentEdit(commentId, commentText, commentElement);
            }
        }

        const deleteButton = event.target.closest('.delete-button');
        if (deleteButton) {
            const commentId = deleteButton.dataset.commentId;
            const commentElement = deleteButton.closest('.feed-comment-card');
            if (commentElement) {
                handleCommentDelete(commentId, commentElement);
            }
        }
    });
});