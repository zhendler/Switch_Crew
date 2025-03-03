document.addEventListener('DOMContentLoaded', function() {
            const fileInput = document.getElementById('file');
            const previewImage = document.getElementById('preview-image');
            const effectSelect = document.getElementById('effect');

            fileInput.addEventListener('change', function(event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewImage.src = e.target.result;
                        previewImage.style.display = 'block';
                        applyEffect(); // Apply initial effect
                    };
                    reader.readAsDataURL(file);
                }
            });

            effectSelect.addEventListener('change', applyEffect);

            function applyEffect() {
                if (!previewImage.src) return;

                const effect = effectSelect.value;
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                const img = new Image();

                img.onload = function() {
                    canvas.width = img.width;
                    canvas.height = img.height;
                    ctx.drawImage(img, 0, 0);

                    switch(effect) {
                        case 'sepia':
                            applySepiaFilter(ctx, canvas.width, canvas.height);
                            break;
                        case 'grayscale':
                            applyGrayscaleFilter(ctx, canvas.width, canvas.height);
                            break;
                        case 'blur':
                            applyBlurFilter(ctx, canvas.width, canvas.height);
                            break;
                        case 'negate':
                            applyNegateFilter(ctx, canvas.width, canvas.height);
                            break;
                    }

                    previewImage.src = canvas.toDataURL();
                };
                img.src = fileInput.files[0] ? URL.createObjectURL(fileInput.files[0]) : previewImage.src;
            }

            function applySepiaFilter(ctx, width, height) {
                const imageData = ctx.getImageData(0, 0, width, height);
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {
                    const r = data[i], g = data[i + 1], b = data[i + 2];
                    data[i] = Math.min(r * 0.393 + g * 0.769 + b * 0.189, 255);
                    data[i + 1] = Math.min(r * 0.349 + g * 0.686 + b * 0.168, 255);
                    data[i + 2] = Math.min(r * 0.272 + g * 0.534 + b * 0.131, 255);
                }
                ctx.putImageData(imageData, 0, 0);
            }

            function applyGrayscaleFilter(ctx, width, height) {
                const imageData = ctx.getImageData(0, 0, width, height);
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {
                    const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
                    data[i] = data[i + 1] = data[i + 2] = avg;
                }
                ctx.putImageData(imageData, 0, 0);
            }

            function applyBlurFilter(ctx, width, height) {
                ctx.filter = 'blur(5px)';
                ctx.drawImage(ctx.canvas, 0, 0);
                ctx.filter = 'none';
            }

            function applyNegateFilter(ctx, width, height) {
                const imageData = ctx.getImageData(0, 0, width, height);
                const data = imageData.data;
                for (let i = 0; i < data.length; i += 4) {
                    data[i] = 255 - data[i];
                    data[i + 1] = 255 - data[i + 1];
                    data[i + 2] = 255 - data[i + 2];
                }
                ctx.putImageData(imageData, 0, 0);
            }
        });

document.getElementById("file").addEventListener("change", function(event) {
    const preview = document.getElementById("preview-image");
    const file = event.target.files[0];

    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.classList.add("show");
        };
        reader.readAsDataURL(file);
    } else {
        preview.src = "";
        preview.classList.remove("show");
    }
});