document.addEventListener('DOMContentLoaded', function () {
    const sliders = document.querySelectorAll('.slider');

    sliders.forEach(function (slider) {
        const output = slider.nextElementSibling;

        slider.addEventListener('input', function () {
            const selectedIndex = slider.value;            
            // Reset other sliders to their initial state
            sliders.forEach(function (otherSlider) {
                if (otherSlider !== slider) {
                    otherSlider.value = 0;
                    const otherOutput = otherSlider.nextElementSibling;
                    otherOutput.textContent = '0%';
                    otherSlider.style.background = 'linear-gradient(to right, #003399 0%, #003399 0%, #f5f6f7 0%, #f5f6f7 100%)';
                }
            });

            // Update the current slider's position
            output.textContent = `${selectedIndex * 10}%`;
            slider.style.background = 'linear-gradient(to right, #003399 0%, #003399 ' + (selectedIndex * 10) + '%, #f5f6f7 ' + (selectedIndex * 10) + '%, #f5f6f7 100%)';
        });
    });
});
