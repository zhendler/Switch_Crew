document.addEventListener('DOMContentLoaded', () => {
    const editDescriptionButton = document.querySelector('.edit-button');
    const descriptionElement = document.getElementById('photo-description');
    let isEditing = false; // Флаг для отслеживания состояния редактирования
    let originalDescription = ''; // Для хранения оригинального текста описания

    if (editDescriptionButton) {
        editDescriptionButton.addEventListener('click', () => {
            if (isEditing) {
                // Если уже идет редактирование, отменяем его
                descriptionElement.innerHTML = originalDescription; // Восстанавливаем исходное описание
                isEditing = false; // Сбрасываем флаг редактирования
                return;
            }

            isEditing = true; // Устанавливаем флаг редактирования
            originalDescription = descriptionElement.innerHTML.trim(); // Сохраняем оригинальное описание

            const currentDescription = descriptionElement.textContent.trim();

            // Создаем текстовое поле для редактирования
            const editField = document.createElement('textarea');
            editField.className = 'edit-description-input';
            editField.value = currentDescription;

            // Добавляем кнопку сохранения
            const saveButton = document.createElement('button');
            saveButton.className = 'save-description-button';
            saveButton.textContent = 'Save';

            // Очищаем содержимое и добавляем поле ввода и кнопку
            descriptionElement.innerHTML = '';
            descriptionElement.appendChild(editField);
            descriptionElement.appendChild(saveButton);

            // Обработчик нажатия на кнопку сохранения
            saveButton.addEventListener('click', async () => {
                const newDescription = editField.value.trim();

                // Проверяем, если описание не изменилось
                if (newDescription === currentDescription || newDescription === '') {
                    descriptionElement.innerHTML = originalDescription; // Восстанавливаем оригинальное описание
                    isEditing = false; // Сбрасываем флаг редактирования
                    return;
                }

                try {
                    // Отправляем данные на сервер
                    const response = await fetch(`/photos/edit-description/${descriptionElement.dataset.photoId}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': getCsrfToken(), // Добавляем CSRF-токен
                        },
                        body: `description=${encodeURIComponent(newDescription)}`
                    });

                    if (response.ok) {
                        // Обновляем текст описания
                        descriptionElement.textContent = newDescription;
                    } else {
                        alert('Failed to update description.');
                        descriptionElement.innerHTML = originalDescription; // Восстанавливаем старое описание
                    }
                } catch (error) {
                    alert('An error occurred.');
                    descriptionElement.innerHTML = originalDescription; // Восстанавливаем старое описание
                } finally {
                    isEditing = false; // Сбрасываем флаг редактирования
                }
            });
        });
    }

    // Функция для получения CSRF-токена (если используется Django)
    function getCsrfToken() {
        const csrfCookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return csrfCookie ? csrfCookie.split('=')[1] : '';
    }
});
