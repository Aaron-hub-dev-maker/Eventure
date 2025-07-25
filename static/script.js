document.addEventListener("DOMContentLoaded", () => {
    const menuToggle = document.getElementById("menu-toggle");
    const menuOptions = document.createElement("div");

    const urlParams = new URLSearchParams(window.location.search);
    const distance = urlParams.get("distance") || "";
    const city = urlParams.get("place") || "";

    menuOptions.classList.add("menu-options");
    menuOptions.innerHTML = `
        <a href="/host?distance=${distance}&place=${city}" class="menu-item">Host an event</a>
        <a href="/FAQ?distance=${distance}&place=${city}" class="menu-item">FAQ</a>
        <a href="/referrals?distance=${distance}&place=${city}" class="menu-item">Referrals</a>
        <a href="/contact?distance=${distance}&place=${city}" class="menu-item">Contact</a>
    `;
    document.body.appendChild(menuOptions);

    const positionMenu = () => {
        const rect = menuToggle.getBoundingClientRect();
        menuOptions.style.top = `${rect.bottom + window.scrollY}px`;
        menuOptions.style.left = `${rect.left + window.scrollX}px`;
    };

    menuToggle.addEventListener("click", (event) => {
        event.stopPropagation();
        menuOptions.classList.toggle("visible");
        positionMenu();
    });

    document.addEventListener("click", (event) => {
        if (!menuOptions.contains(event.target) && event.target !== menuToggle) {
            menuOptions.classList.remove("visible");
        }
    });

    window.addEventListener("resize", () => {
        if (menuOptions.classList.contains("visible")) {
            positionMenu();
        }
    });

    function filterEvents() {
        const searchQuery = document.getElementById("search-bar").value.toLowerCase();
        const eventCards = document.querySelectorAll(".event-card");
        let found = false;

        eventCards.forEach(card => {
            const eventName = card.querySelector("h3").textContent.toLowerCase();
            if (eventName.includes(searchQuery)) {
                card.style.display = "block";
                found = true;
            } else {
                card.style.display = "none";
            }
        });

        const noResultsMessage = document.getElementById("no-results-message");
        if (!found) {
            if (!noResultsMessage) {
                const message = document.createElement("div");
                message.id = "no-results-message";
                message.textContent = "There is no such event.";
                message.style.color = "red";
                document.getElementById("events-container").appendChild(message);
            }
        } else if (noResultsMessage) {
            noResultsMessage.remove();
        }
    }

    const searchBar = document.getElementById("search-bar");
    if (searchBar) {
        searchBar.addEventListener("keyup", filterEvents);
    }

    function applyPlaceFilter(place) {
        const currentDistance = new URLSearchParams(window.location.search).get("distance");
        const button = document.querySelector(`.filter-btn[data-place="${place}"]`);

        if (button.classList.contains("selected")) {
            window.location.href = "/";
        } else {
            const newUrl = `/?place=${place}&distance=${currentDistance || ''}`;
            window.location.href = newUrl;
        }
    }

    function applyDistanceFilter(distance) {
        const currentPlace = new URLSearchParams(window.location.search).get("place");
        const button = document.querySelector(`.filter-btn[data-distance="${distance}"]`);

        if (button.classList.contains("selected")) {
            window.location.href = "/";
        } else {
            const newUrl = `/?distance=${distance}&place=${currentPlace || ''}`;
            window.location.href = newUrl;
        }
    }

    const activePlace = urlParams.get("place");
    const activeDistance = urlParams.get("distance");

    if (activePlace) {
        const placeButton = document.querySelector(`.filter-btn[data-place="${activePlace}"]`);
        if (placeButton) placeButton.classList.add("selected");
    }

    if (activeDistance) {
        const distanceButton = document.querySelector(`.filter-btn[data-distance="${activeDistance}"]`);
        if (distanceButton) distanceButton.classList.add("selected");
    }

    document.querySelectorAll(".filter-btn").forEach(button => {
        button.addEventListener("click", () => {
            if (button.dataset.place) {
                applyPlaceFilter(button.dataset.place);
            } else if (button.dataset.distance) {
                applyDistanceFilter(button.dataset.distance);
            }
        });
    });
});
