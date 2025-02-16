document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".subscribe-button, .unsubscribe-button").forEach(button => {
        button.addEventListener("click", async function () {
            const userId = this.getAttribute("data-user-id");
            const isSubscribing = this.classList.contains("subscribe-button");
            const url = isSubscribing ? `/subscriptions/subscribe/${userId}` : `/subscriptions/unsubscribe/${userId}`;

            try {
                const response = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    alert(errorData.detail || "Something went wrong!");
                    return;
                }

                toggleButton(this, isSubscribing);
            } catch (error) {
                console.error("Error:", error);
                alert("Failed to process request.");
            }
        });
    });

    function toggleButton(button, isSubscribing) {
        if (isSubscribing) {
            button.classList.remove("subscribe-button");
            button.classList.add("unsubscribe-button");
            button.innerHTML = '<span class="button-icon"></span> Subscribed';
        } else {
            button.classList.remove("unsubscribe-button");
            button.classList.add("subscribe-button");
            button.innerHTML = '<span class="button-icon"></span> Follow';
        }
    }
});
