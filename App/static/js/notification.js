document.addEventListener("DOMContentLoaded", () => {
    const panel = document.getElementById("notification-panel");
    const btn = document.getElementById("notification-btn");
    const postsSection = document.getElementById("posts-section");

    btn.addEventListener("click", (e) => {
        e.preventDefault();

        const isOpen = panel.style.display === "block";
        panel.style.display = isOpen ? "none" : "block";
        postsSection.style.display = isOpen ? "block" : "none";

        if (!isOpen) {
            // Fetch latest notifications
            fetch("/notifications/ajax/")
                .then(res => res.json())
                .then(data => {
                    const list = document.getElementById("notification-list");
                    list.innerHTML = "";
                    if (!data.notifications.length) {
                        list.innerHTML = "<li>No notifications</li>";
                    } else {
                        data.notifications.forEach(n => {
                            list.innerHTML += `<li>${n.message} <small>${n.time}</small></li>`;
                        });
                    }
                });
        }
    });

    // Real-time updates
    const socket = new WebSocket(`ws://${window.location.host}/ws/notifications/`);

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const countEl = document.getElementById("notification-count");
        if(countEl){
            countEl.innerText = parseInt(countEl.innerText || 0) + 1;
        }

        const listEl = document.getElementById("notification-list");
        if(listEl){
            const li = document.createElement("li");
            li.innerHTML = `${data.message} <small>just now</small>`;
            listEl.prepend(li);
        }
    };
});
