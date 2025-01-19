document.addEventListener("DOMContentLoaded", () => {
        const editButton = document.getElementById("edit-profile-btn");
        const form = document.getElementById("edit-profile-form");
        const saveButton = document.getElementById("save-profile-btn");

        editButton.addEventListener("click", () => {
            form.classList.toggle("hidden");
        });

        saveButton.addEventListener("click", async () => {
            // Получаем значения из формы
            const firstName = document.getElementById("first_name").value;
            const lastName = document.getElementById("last_name").value;
            const country = document.getElementById("country").value;
            const birthDate = document.getElementById("birth_date").value;

            try {
                // Отправляем запрос на сервер
                const response = await fetch("/user_profile/update-profile", {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        first_name: firstName,
                        last_name: lastName,
                        country: country,
                        birth_date: birthDate,
                    }),
                });

                if (response.ok) {
                    // Обновляем текстовые элементы на странице
                    if (firstName && lastName) {
                        document.querySelector(".fullname").innerHTML = `<strong>${firstName} ${lastName}</strong>`;
                    }
                    if (country) {
                        document.querySelector(".country").innerHTML = `<strong>Country:</strong> ${country}`;
                    }
                    if (birthDate) {
                        document.querySelector(".birthdate").innerHTML = `<strong>Born on:</strong> ${birthDate}`;
                    }

                    // Прячем форму
                    form.classList.add("hidden");
                } else {
                    console.error("Failed to update profile");
                }
            } catch (error) {
                console.error("Error occurred while updating profile:", error);
            }
        });
    });