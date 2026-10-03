/* =========================================================
   INTELLIGENT CV SCREENING & JOB MATCHING SYSTEM
   MASTER JAVASCRIPT
   ========================================================= */


/* =========================================================
   1. PAGE INITIALIZATION
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    initializeNavigation();
    initializeNotifications();
    initializeFileUpload();
    initializeSearch();
    initializeFilters();
    initializeToggles();
    initializeProgressBars();
    initializeButtons();

});


/* =========================================================
   2. MOBILE NAVIGATION
   ========================================================= */

function initializeNavigation() {

    const sidebar = document.querySelector(".sidebar");

    if (!sidebar) {
        return;
    }

    let menuButton = document.querySelector(".mobile-menu-btn");

    if (!menuButton) {

        menuButton = document.createElement("button");

        menuButton.className = "mobile-menu-btn";
        menuButton.innerHTML = "☰";
        menuButton.setAttribute("aria-label", "Open navigation menu");

        menuButton.style.cssText = `
            position: fixed;
            top: 17px;
            left: 15px;
            z-index: 1500;
            width: 40px;
            height: 40px;
            border: 1px solid rgba(148,163,184,.2);
            border-radius: 8px;
            background: #101f33;
            color: white;
            font-size: 18px;
            display: none;
        `;

        document.body.appendChild(menuButton);

        menuButton.addEventListener("click", function () {

            sidebar.classList.toggle("mobile-open");

        });
    }


    document.addEventListener("click", function (event) {

        if (
            window.innerWidth <= 800 &&
            sidebar.classList.contains("mobile-open") &&
            !sidebar.contains(event.target) &&
            event.target !== menuButton
        ) {

            sidebar.classList.remove("mobile-open");

        }

    });

}


/* =========================================================
   3. NOTIFICATIONS
   ========================================================= */

function initializeNotifications() {

    const notificationButton =
        document.querySelector(".notification-btn");

    if (!notificationButton) {
        return;
    }

    notificationButton.addEventListener("click", function () {

        showNotification(
            "You have new recruitment system notifications."
        );

    });

}


/* =========================================================
   4. GLOBAL NOTIFICATION MESSAGE
   ========================================================= */

function showNotification(message, type = "info") {

    const existing =
        document.querySelector(".system-notification");

    if (existing) {
        existing.remove();
    }

    const notification =
        document.createElement("div");

    notification.className =
        "system-notification";

    let borderColor = "#06b6d4";

    if (type === "success") {
        borderColor = "#22c55e";
    }

    if (type === "warning") {
        borderColor = "#f59e0b";
    }

    if (type === "error") {
        borderColor = "#ef4444";
    }

    notification.style.cssText = `
        position: fixed;
        top: 85px;
        right: 25px;
        z-index: 3000;
        min-width: 280px;
        max-width: 380px;
        padding: 15px 18px;
        background: #101f33;
        color: #f8fafc;
        border: 1px solid ${borderColor};
        border-radius: 10px;
        box-shadow: 0 15px 40px rgba(0,0,0,.35);
        font-size: 13px;
        animation: systemNotificationIn .3s ease;
    `;

    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(function () {

        notification.style.opacity = "0";
        notification.style.transform = "translateY(-8px)";

        setTimeout(function () {
            notification.remove();
        }, 250);

    }, 3500);

}


/* =========================================================
   5. FILE UPLOAD
   ========================================================= */

function initializeFileUpload() {

    const uploadArea =
        document.querySelector(".upload-area");

    const fileInput =
        document.querySelector(
            'input[type="file"]'
        );

    if (!uploadArea || !fileInput) {
        return;
    }


    uploadArea.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            uploadArea.classList.add("dragover");

        }
    );


    uploadArea.addEventListener(
        "dragleave",
        function () {

            uploadArea.classList.remove("dragover");

        }
    );


    uploadArea.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();

            uploadArea.classList.remove("dragover");

            const files = event.dataTransfer.files;

            if (files.length > 0) {

                fileInput.files = files;

                handleSelectedFile(files[0]);

            }

        }
    );


    fileInput.addEventListener(
        "change",
        function () {

            if (this.files.length > 0) {

                handleSelectedFile(this.files[0]);

            }

        }
    );

}


/* =========================================================
   6. FILE VALIDATION
   ========================================================= */

function handleSelectedFile(file) {

    const allowedTypes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ];

    const maxSize =
        10 * 1024 * 1024;


    if (!allowedTypes.includes(file.type)) {

        showNotification(
            "Please upload a PDF or DOCX CV file.",
            "error"
        );

        return;

    }


    if (file.size > maxSize) {

        showNotification(
            "The CV file must not exceed 10 MB.",
            "error"
        );

        return;

    }


    const fileName =
        document.querySelector(".file-name");

    const fileSize =
        document.querySelector(".file-size");


    if (fileName) {

        fileName.textContent =
            file.name;

    }


    if (fileSize) {

        fileSize.textContent =
            formatFileSize(file.size);

    }


    showNotification(
        "CV file selected successfully.",
        "success"
    );

}


function formatFileSize(bytes) {

    if (bytes === 0) {
        return "0 Bytes";
    }

    const units = [
        "Bytes",
        "KB",
        "MB",
        "GB"
    ];

    const index =
        Math.floor(
            Math.log(bytes) /
            Math.log(1024)
        );

    return (
        parseFloat(
            (bytes / Math.pow(1024, index))
                .toFixed(2)
        )
        + " "
        + units[index]
    );

}


/* =========================================================
   7. SEARCH
   ========================================================= */

function initializeSearch() {

    const searchInputs =
        document.querySelectorAll(
            'input[type="search"], .search-box input'
        );


    searchInputs.forEach(function (input) {

        input.addEventListener(
            "input",
            function () {

                performTableSearch(
                    this.value.trim().toLowerCase()
                );

            }
        );

    });

}


function performTableSearch(searchTerm) {

    const rows =
        document.querySelectorAll(
            ".data-table tbody tr"
        );

    if (!rows.length) {
        return;
    }


    rows.forEach(function (row) {

        const text =
            row.textContent.toLowerCase();

        if (text.includes(searchTerm)) {

            row.style.display = "";

        } else {

            row.style.display = "none";

        }

    });

}


/* =========================================================
   8. FILTERS
   ========================================================= */

function initializeFilters() {

    const filters =
        document.querySelectorAll(
            ".filter-bar select"
        );


    filters.forEach(function (filter) {

        filter.addEventListener(
            "change",
            function () {

                applyFilters();

            }
        );

    });

}


function applyFilters() {

    const rows =
        document.querySelectorAll(
            ".data-table tbody tr"
        );

    if (!rows.length) {
        return;
    }


    const filters =
        document.querySelectorAll(
            ".filter-bar select"
        );


    rows.forEach(function (row) {

        let visible = true;


        filters.forEach(function (filter) {

            const selected =
                filter.value.toLowerCase();

            if (
                selected &&
                selected !== "all"
            ) {

                const rowText =
                    row.textContent.toLowerCase();

                if (
                    !rowText.includes(selected)
                ) {

                    visible = false;

                }

            }

        });


        row.style.display =
            visible ? "" : "none";

    });

}


/* =========================================================
   9. TOGGLE SWITCHES
   ========================================================= */

function initializeToggles() {

    const toggles =
        document.querySelectorAll(
            '.toggle input, input[type="checkbox"]'
        );


    toggles.forEach(function (toggle) {

        toggle.addEventListener(
            "change",
            function () {

                if (this.checked) {

                    showNotification(
                        "Setting enabled.",
                        "success"
                    );

                } else {

                    showNotification(
                        "Setting disabled.",
                        "info"
                    );

                }

            }
        );

    });

}


/* =========================================================
   10. PROGRESS BARS
   ========================================================= */

function initializeProgressBars() {

    const progressBars =
        document.querySelectorAll(
            ".progress-bar"
        );


    progressBars.forEach(function (bar) {

        const width =
            bar.dataset.progress ||
            bar.style.width;

        if (width) {

            bar.style.width = "0%";

            setTimeout(function () {

                bar.style.width = width;

            }, 200);

        }

    });

}


/* =========================================================
   11. BUTTON HANDLERS
   ========================================================= */

function initializeButtons() {

    const printButtons =
        document.querySelectorAll(
            ".print-btn"
        );


    printButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                window.print();

            }
        );

    });


    const clearButtons =
        document.querySelectorAll(
            ".clear-btn"
        );


    clearButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function () {

                clearForms();

            }
        );

    });

}


/* =========================================================
   12. CLEAR FORMS
   ========================================================= */

function clearForms() {

    const forms =
        document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.reset();

    });

    showNotification(
        "Form cleared.",
        "success"
    );

}


/* =========================================================
   13. SAVE FORM DEMO
   ========================================================= */

function saveForm(formSelector) {

    const form =
        document.querySelector(formSelector);

    if (!form) {
        return;
    }


    if (!form.checkValidity()) {

        form.reportValidity();

        return;

    }


    showNotification(
        "Information saved successfully.",
        "success"
    );

}


/* =========================================================
   14. AI SCREENING PROGRESS
   ========================================================= */

function startAIScreening() {

    const progressContainer =
        document.querySelector(
            ".screening-progress"
        );

    const progressBar =
        document.querySelector(
            ".screening-progress .progress-bar"
        );

    const progressText =
        document.querySelector(
            ".screening-progress-text"
        );


    if (!progressContainer || !progressBar) {

        showNotification(
            "AI Screening engine is ready.",
            "info"
        );

        return;

    }


    progressContainer.style.display =
        "block";


    let progress = 0;


    const stages = [
        "Uploading CV...",
        "Extracting CV text...",
        "Detecting technical skills...",
        "Analyzing education and experience...",
        "Comparing job requirements...",
        "Calculating match score...",
        "Generating AI recommendation..."
    ];


    const interval =
        setInterval(function () {

            progress += 10;

            progressBar.style.width =
                progress + "%";


            if (progressText) {

                const stageIndex =
                    Math.min(
                        Math.floor(progress / 15),
                        stages.length - 1
                    );

                progressText.textContent =
                    stages[stageIndex];

            }


            if (progress >= 100) {

                clearInterval(interval);

                if (progressText) {

                    progressText.textContent =
                        "AI screening completed.";

                }

                showNotification(
                    "AI screening completed successfully.",
                    "success"
                );

            }

        }, 250);

}


/* =========================================================
   15. SKILL TAG CREATION
   ========================================================= */

function addSkillTag(
    inputSelector,
    containerSelector
) {

    const input =
        document.querySelector(inputSelector);

    const container =
        document.querySelector(containerSelector);


    if (!input || !container) {
        return;
    }


    const skill =
        input.value.trim();


    if (!skill) {
        return;
    }


    const tag =
        document.createElement("span");

    tag.className =
        "skill-tag";


    tag.innerHTML = `
        ${escapeHTML(skill)}
        <button
            type="button"
            onclick="this.parentElement.remove()"
            style="
                border:none;
                background:none;
                color:inherit;
                margin-left:5px;
                cursor:pointer;
            "
        >
            ×
        </button>
    `;


    container.appendChild(tag);

    input.value = "";

}


/* =========================================================
   16. HTML SECURITY HELPER
   ========================================================= */

function escapeHTML(value) {

    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


/* =========================================================
   17. CONFIRMATION DIALOG
   ========================================================= */

function confirmAction(message) {

    return window.confirm(
        message ||
        "Are you sure you want to continue?"
    );

}


/* =========================================================
   18. DATE & TIME
   ========================================================= */

function getCurrentDateTime() {

    const now =
        new Date();

    return now.toLocaleString();

}


/* =========================================================
   19. DYNAMIC GREETING
   ========================================================= */

function updateGreeting(elementId = "greeting") {

    const element =
        document.getElementById(elementId);

    if (!element) {
        return;
    }


    const hour =
        new Date().getHours();


    let greeting;


    if (hour < 12) {

        greeting = "Good morning";

    } else if (hour < 17) {

        greeting = "Good afternoon";

    } else {

        greeting = "Good evening";

    }


    element.textContent =
        greeting + ", Recruiter";

}


/* =========================================================
   20. AUTO UPDATE GREETING
   ========================================================= */

updateGreeting();


/* =========================================================
   21. WINDOW RESIZE
   ========================================================= */

window.addEventListener(
    "resize",
    function () {

        const sidebar =
            document.querySelector(".sidebar");

        if (
            sidebar &&
            window.innerWidth > 800
        ) {

            sidebar.classList.remove(
                "mobile-open"
            );

        }

    }
);


/* =========================================================
   22. GLOBAL CSS FOR NOTIFICATIONS
   ========================================================= */

const notificationStyles =
    document.createElement("style");

notificationStyles.textContent = `
    @keyframes systemNotificationIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .system-notification {
        transition:
            opacity .25s ease,
            transform .25s ease;
    }

    @media (max-width: 800px) {

        .mobile-menu-btn {
            display: block !important;
        }

    }
`;

document.head.appendChild(
    notificationStyles
);


/* =========================================================
   SYSTEM READY
   ========================================================= */

console.log(
    "Intelligent CV Screening System JavaScript loaded successfully."
);