document.addEventListener('DOMContentLoaded', function() {
    const commentForm = document.querySelector('.comment-form');
    // Проверяем существование формы перед продолжением
    if (commentForm) {
        const commentInput = document.querySelector('.comment-input');
        const submitButton = commentForm.querySelector('button[type="submit"]');
        let commentsContainer = document.querySelector('.comments');
        let isSubmitting = false;

        submitButton.style.position = 'relative';

        function setSubmitButtonLoading(loading) {
            if (loading) {
                isSubmitting = true;
                submitButton.disabled = true;
                submitButton.style.opacity = '0.7';
                submitButton.style.cursor = 'not-allowed';
                submitButton.textContent = 'Posting...';
            } else {
                isSubmitting = false;
                submitButton.disabled = false;
                submitButton.style.opacity = '1';
                submitButton.style.cursor = 'pointer';
                submitButton.textContent = 'Post';
            }
        }

        function ensureCommentsContainer() {
            if (!commentsContainer) {
                const noCommentsElement = document.querySelector('.no-comments');
                if (noCommentsElement) {
                    noCommentsElement.remove();
                }
                commentsContainer = document.createElement('div');
                commentsContainer.className = 'comments';
                commentForm.parentNode.insertBefore(commentsContainer, commentForm.nextSibling);
            }
            return commentsContainer;
        }

        function updateCommentsVisibility() {
            commentsContainer = document.querySelector('.comments');
            if (commentsContainer && commentsContainer.children.length === 0) {
                const noCommentsElement = document.createElement('p');
                noCommentsElement.className = 'no-comments';
                noCommentsElement.textContent = 'No comments yet.';
                commentsContainer.parentNode.insertBefore(noCommentsElement, commentsContainer);
                commentsContainer.remove();
                commentsContainer = null;
            }
        }

        async function handleCommentEdit(commentId, currentContent) {
            const commentText = document.querySelector(`#comment-text-${commentId}`);
            const editButton = document.querySelector(`[data-comment-id="${commentId}"]`);
            const existingEditForm = commentText.parentNode.querySelector('.edit-form');

            if (existingEditForm) {
                existingEditForm.remove();
                commentText.style.display = 'block';
                return;
            }

            const editForm = document.createElement('div');
            editForm.className = 'edit-form';
            editForm.innerHTML = `
                <textarea class="comment-input">${currentContent}</textarea>
                <div class="edit-buttons">
                    <button type="button" class="save-button">Save</button>
                </div>
            `;

            commentText.style.display = 'none';
            commentText.parentNode.insertBefore(editForm, commentText);

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
                        editButton.setAttribute('data-comment-text', newContent);
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

        async function handleCommentDelete(commentId, commentCard) {
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
                    commentCard.remove();
                    updateCommentsVisibility();
                } else {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to delete comment');
                }
            } catch (error) {
                console.error('Error deleting comment:', error);
                alert('Failed to delete comment. Please try again.');
            }
        }

        // Добавляем обработчик отправки формы
        commentForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            if (isSubmitting) {
                return;
            }

            const photoId = window.location.pathname.split('/').pop();
            const commentContent = commentInput.value.trim();

            if (!commentContent) {
                return;
            }

            setSubmitButtonLoading(true);

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
                    const container = ensureCommentsContainer();
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

                    if (container.children.length === 0) {
                        container.appendChild(commentElement);
                    } else {
                        container.insertBefore(commentElement, container.firstChild);
                    }

                    commentInput.value = '';
                } else {
                    throw new Error(data.error || 'Failed to post comment');
                }
            } catch (error) {
                console.error('Error details:', error);
                alert('Failed to post comment. Please try again. Error: ' + error.message);
            } finally {
                setSubmitButtonLoading(false);
            }
        });

        // Добавляем общий обработчик для кнопок редактирования и удаления
        document.addEventListener('click', function(event) {
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
                handleCommentDelete(commentId, commentCard);
            }
        });
    }
});