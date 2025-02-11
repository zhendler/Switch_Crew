document.addEventListener('DOMContentLoaded', () => {
    const editDescriptionButton = document.querySelector('.edit-button-description');
    const descriptionElement = document.getElementById('photo-description');
    const saveButton = document.getElementById('save-description-button'); // Кнопка сохранения
    let isEditing = false;
    let originalDescription = '';

    if (editDescriptionButton) {
        editDescriptionButton.addEventListener('click', () => {
            if (isEditing) {
                // Если уже идет редактирование, отменяем его
                descriptionElement.innerHTML = originalDescription;
                saveButton.style.display = 'none'; // Скрываем кнопку сохранения
                isEditing = false;
                return;
            }

            isEditing = true;
            originalDescription = descriptionElement.innerHTML.trim();

            const currentDescription = descriptionElement.textContent.trim();

            // Создаем текстовое поле для редактирования
            const editField = document.createElement('textarea');
            editField.className = 'edit-description-input';
            editField.value = currentDescription;

            // Применяем стили к полю редактирования
            editField.style.width = '60%';
            editField.style.height = '60px';
            editField.style.padding = '5px';
            editField.style.fontSize = '16px';
            editField.style.border = '2px solid #ccc';
            editField.style.borderRadius = '8px';
            editField.style.marginBottom = '10px';
            editField.style.resize = 'vertical';
            editField.style.backgroundColor = '#fafafa';

            // Очищаем содержимое и добавляем поле ввода
            descriptionElement.innerHTML = '';
            descriptionElement.appendChild(editField);

            // Добавляем кнопку сохранения под полем редактирования
            const newSaveButton = document.createElement('button');
            newSaveButton.className = 'save-description-button';
            newSaveButton.textContent = 'Save';
            descriptionElement.appendChild(newSaveButton);

            // Показать кнопку сохранения
            newSaveButton.style.display = 'block';

            // Обработчик нажатия на кнопку сохранения
            newSaveButton.addEventListener('click', async () => {
                const newDescription = editField.value.trim();

                if (newDescription === currentDescription || newDescription === '') {
                    descriptionElement.innerHTML = originalDescription;
                    newSaveButton.style.display = 'none'; // Скрыть кнопку сохранения
                    isEditing = false;
                    return;
                }

                try {
                    const response = await fetch(`/photos/edit-description/${descriptionElement.dataset.photoId}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': getCsrfToken(),
                        },
                        body: `description=${encodeURIComponent(newDescription)}`
                    });

                    if (response.ok) {
                        descriptionElement.textContent = newDescription;
                        newSaveButton.style.display = 'none'; // Скрыть кнопку сохранения после успешного сохранения
                    } else {
                        alert('Failed to update description.');
                        descriptionElement.innerHTML = originalDescription;
                        newSaveButton.style.display = 'none'; // Скрыть кнопку сохранения
                    }
                } catch (error) {
                    alert('An error occurred.');
                    descriptionElement.innerHTML = originalDescription;
                    newSaveButton.style.display = 'none'; // Скрыть кнопку сохранения
                } finally {
                    isEditing = false;
                }
            });
        });
    }

    function getCsrfToken() {
        const csrfCookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return csrfCookie ? csrfCookie.split('=')[1] : '';
    }
});
