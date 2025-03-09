async function addReaction(reactionId, photoId) {
    // Сохраняем текущее состояние, чтобы можно было вернуться к нему в случае ошибки
    const previousActive = document.querySelector('.reaction-circle.active');
    const previousActiveId = previousActive ?
        parseInt(previousActive.closest('.reaction-container').getAttribute('onclick').match(/addReaction\((\d+),/)[1])
        : null;

    // Сохраняем текущие значения счетчиков
    const previousCounts = {};
    for (let i = 1; i <= 8; i++) {
        const countElement = document.querySelector(`.reaction-container[onclick="addReaction(${i}, ${photoId})"] .reaction-count`);
        if (countElement) {
            previousCounts[i] = parseInt(countElement.textContent);
        }
    }

    // Оптимистично обновляем UI сразу
    // 1. Удаляем класс 'active' со всех реакций
    const activeReactions = document.querySelectorAll('.reaction-circle.active');
    activeReactions.forEach(el => {
        el.classList.remove('active');
    });

    // Определяем, добавляем или удаляем реакцию
    const isToggleOff = previousActiveId === reactionId;

    // 2. Добавляем класс 'active' к выбранной реакции (если это не снятие той же реакции)
    if (!isToggleOff) {
        const reactionCircle = document.querySelector(`.reaction-container[onclick="addReaction(${reactionId}, ${photoId})"] .reaction-circle`);
        if (reactionCircle) {
            reactionCircle.classList.add('active');
        }
    }

    // 3. Оптимистично обновляем счетчики
    // Если была активна другая реакция - уменьшаем её счетчик
    if (previousActiveId && previousActiveId !== reactionId) {
        const prevCountElement = document.querySelector(`.reaction-container[onclick="addReaction(${previousActiveId}, ${photoId})"] .reaction-count`);
        if (prevCountElement) {
            prevCountElement.textContent = Math.max(0, previousCounts[previousActiveId] - 1);
        }
    }

    // Если текущая реакция не была активна - увеличиваем счетчик
    if (!isToggleOff) {
        const currentCountElement = document.querySelector(`.reaction-container[onclick="addReaction(${reactionId}, ${photoId})"] .reaction-count`);
        if (currentCountElement) {
            currentCountElement.textContent = previousCounts[reactionId] + 1;
        }
    } else {
        // Если это снятие той же реакции - уменьшаем счетчик
        const currentCountElement = document.querySelector(`.reaction-container[onclick="addReaction(${reactionId}, ${photoId})"] .reaction-count`);
        if (currentCountElement) {
            currentCountElement.textContent = Math.max(0, previousCounts[reactionId] - 1);
        }
    }

    // Затем отправляем запрос на сервер
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

            // Обновляем счетчики реакций по данным с сервера
            for (let i = 1; i <= 8; i++) {
                const reactionCountElement = document.querySelector(`.reaction-container[onclick="addReaction(${i}, ${photoId})"] .reaction-count`);
                if (reactionCountElement) {
                    reactionCountElement.textContent = data.reaction_counts[i];
                }
            }

            // Обновляем активную реакцию по данным с сервера
            // Сначала удаляем все активные классы
            document.querySelectorAll('.reaction-circle.active').forEach(el => {
                el.classList.remove('active');
            });

            // Затем добавляем активный класс по данным с сервера
            if (data.current_reaction !== null) {
                const reactionCircle = document.querySelector(`.reaction-container[onclick="addReaction(${data.current_reaction}, ${photoId})"] .reaction-circle`);
                if (reactionCircle) {
                    reactionCircle.classList.add('active');
                }
            }
        } else {
            console.error('Failed to process reaction:', response.statusText);

            // В случае ошибки возвращаем UI к исходному состоянию
            restoreUIState(previousActiveId, previousCounts, photoId);
        }
    } catch (error) {
        console.error('Error:', error);

        // В случае ошибки возвращаем UI к исходному состоянию
        restoreUIState(previousActiveId, previousCounts, photoId);
    }
}

// Вспомогательная функция для восстановления UI в случае ошибки
function restoreUIState(previousActiveId, previousCounts, photoId) {
    // Удаляем все активные классы
    document.querySelectorAll('.reaction-circle.active').forEach(el => {
        el.classList.remove('active');
    });

    // Восстанавливаем активную реакцию
    if (previousActiveId) {
        const reactionCircle = document.querySelector(`.reaction-container[onclick="addReaction(${previousActiveId}, ${photoId})"] .reaction-circle`);
        if (reactionCircle) {
            reactionCircle.classList.add('active');
        }
    }

    // Восстанавливаем счетчики
    for (let i = 1; i <= 8; i++) {
        if (previousCounts[i] !== undefined) {
            const countElement = document.querySelector(`.reaction-container[onclick="addReaction(${i}, ${photoId})"] .reaction-count`);
            if (countElement) {
                countElement.textContent = previousCounts[i];
            }
        }
    }

    // Показываем пользователю уведомление об ошибке
    alert('Произошла ошибка при обработке реакции. Пожалуйста, попробуйте еще раз.');
}