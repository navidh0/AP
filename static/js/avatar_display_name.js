document.addEventListener('DOMContentLoaded', function () {
    const avatarContainer = document.querySelector('[data-avatar-id]');
    if (!avatarContainer) return;

    const avatarId = avatarContainer.dataset.avatarId;
    const avatarName = avatarContainer.dataset.avatarName;
    const fileInput = document.getElementById(avatarId);
    const fileNameDisplay = document.getElementById('file-name');

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            if (this.files && this.files.length > 0) {
                const fileName = this.files[0].name;
                fileNameDisplay.textContent = fileName;
                fileNameDisplay.className = 'text-sm text-neutral-600 font-medium mt-2 text-center';
            } else {
                fileNameDisplay.textContent = 'No file chosen';
                fileNameDisplay.className = 'text-sm text-neutral-600 mt-2 text-center';
            }
        });
    }

    if (avatarName) {
        const fileName = avatarName.replace(/^.*[\\\/]/, '');
        fileNameDisplay.textContent = fileName || 'Current image';
        fileNameDisplay.className = 'text-sm text-neutral-600 font-medium mt-2 text-center';
    }
});
