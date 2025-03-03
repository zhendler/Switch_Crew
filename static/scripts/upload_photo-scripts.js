document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const previewImage = document.getElementById('preview-image');
    const effectSelect = document.getElementById('effect');
    const tagInput = document.getElementById('tag-input');
    const tagsHiddenInput = document.getElementById('tags');
    const tagContainer = document.querySelector('.tag-container');
    const form = document.querySelector('.upload-form');

    // Image Preview Logic (keep existing code)
    fileInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewImage.style.display = 'block';
                applyEffect();
            };
            reader.readAsDataURL(file);
        }
    });

    // Tag Input Logic
    function createTagChip(tagText) {
        const tagChip = document.createElement('span');
        tagChip.className = 'tag-chip';
        tagChip.innerHTML = `
            <span class="tag-text">${tagText.trim()}</span>
            <button type="button" class="remove-tag">&times;</button>
        `;

        tagChip.querySelector('.remove-tag').addEventListener('click', () => {
            tagContainer.removeChild(tagChip);
            updateTagsInput();
        });

        return tagChip;
    }

    function updateTagsInput() {
        const tags = Array.from(tagContainer.children)
            .map(chip => chip.querySelector('.tag-text').textContent.trim());
        tagsHiddenInput.value = tags.join(',');
    }

    tagInput.addEventListener('keydown', function(e) {
        // Create tag on space or comma
        if ((e.key === ' ' || e.key === ',') && this.value.trim()) {
            e.preventDefault();

            // Limit to 5 tags
            if (tagContainer.children.length >= 5) {
                alert('Maximum 5 tags allowed');
                return;
            }

            const tagText = this.value.replace(/[,\s]+/g, '').trim();

            // Prevent duplicate tags
            const existingTags = Array.from(tagContainer.children)
                .map(chip => chip.querySelector('.tag-text').textContent.trim());

            if (tagText && !existingTags.includes(tagText)) {
                const tagChip = createTagChip(tagText);
                tagContainer.appendChild(tagChip);
                updateTagsInput();
                this.value = ''; // Clear input after adding tag
            }
        }
    });

    // Rest of the existing code for effects, etc.
});