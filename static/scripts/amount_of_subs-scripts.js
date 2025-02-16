// Создаем HTML для модального окна
const modal = document.createElement('div');
modal.className = 'modal';
modal.innerHTML = `
  <div class="modal-content">
    <span class="close">&times;</span>
    <h2>Subscribers</h2>
    <div class="subscribers-list">
      <!-- Здесь будет список подписчиков -->
    </div>
  </div>
`;
document.body.appendChild(modal);

// Функция для получения списка подписчиков
async function getSubscribers(userId) {
    try {
        const response = await fetch(`/subscriptions/subscribers/${userId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch subscribers');
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching subscribers:', error);
        throw error;
    }
}

// Функция для отображения подписчиков
function displaySubscribers(subscribersData) {
    const subscribersList = document.querySelector('.subscribers-list');

    if (!subscribersData || !subscribersData.subscribers || subscribersData.subscribers.length === 0) {
        subscribersList.innerHTML = '<div class="subscriber-item">No subscribers yet</div>';
        return;
    }

    subscribersList.innerHTML = `
        <div class="user-list">
            ${subscribersData.subscribers.map(user => `
                <a href="/page/${user.username}" class="user-tile">
                    ${user.avatar_url
                        ? `<img src="${user.avatar_url}" alt="${user.username}" class="user-avatar">`
                        : '<div class="user-avatar-placeholder"></div>'
                    }
                    <p class="user-name">${user.username}</p>
                </a>
            `).join('')}
        </div>
    `;
}

// Функция для отображения ошибки
function displayError(message) {
    const subscribersList = document.querySelector('.subscribers-list');
    subscribersList.innerHTML = `
        <div class="error-message">
            ${message}
        </div>
    `;
}

// Добавляем обработчик клика на элемент с подписчиками
document.querySelector('.stat').addEventListener('click', async function() {
    const userId = this.dataset.userId;
    if (!userId) {
        console.error('User ID not found');
        return;
    }

    modal.style.display = 'block';

    // Показываем индикатор загрузки
    document.querySelector('.subscribers-list').innerHTML = 'Loading...';

    try {
        const subscribersData = await getSubscribers(userId);
        displaySubscribers(subscribersData);
    } catch (error) {
        displayError(error.message || 'Failed to load subscribers. Please try again later.');
    }
});

// Закрытие модального окна при клике на крестик
document.querySelector('.close').addEventListener('click', function() {
    modal.style.display = 'none';
});

// Закрытие модального окна при клике вне его области
window.addEventListener('click', function(event) {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});