document.addEventListener('DOMContentLoaded', function () {
    const sliders = document.querySelectorAll('[id^="slider"]');

    sliders.forEach(function (slider) {
        const questionId = slider.id.replace('slider', '');
        const output = document.getElementById(`output${questionId}`);
        const colorChoices = document.getElementById(`colorChoices${questionId}`);

        slider.addEventListener('input', function () {
            const selectedIndex = slider.value;
            const selectedChoice = colorChoices.children[selectedIndex];
            output.textContent = selectedChoice.dataset.choiceText;
        });
    });
});
