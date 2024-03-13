  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("surveyForm");
    const inputs = form.querySelectorAll(".questions input, .questions textarea, .questions select");
    const submitButton = document.querySelector(".btn-submit");

    // Initialize an object to store all input values
    let storedValues = {};

    // Restore input values from sessionStorage when the page loads
    const storedData = sessionStorage.getItem("surveyFormValues");
    if (storedData) {
      storedValues = JSON.parse(storedData);
      inputs.forEach(function (input) {
        const storedValue = storedValues[input.name];
        if (storedValue !== undefined) {
          input.value = storedValue;
        }
      });
    }

    // Update storedValues dynamically on input change
    inputs.forEach(function (input) {
      input.addEventListener("input", function () {
        storedValues[input.name] = input.value;
        sessionStorage.setItem("surveyFormValues", JSON.stringify(storedValues));
      });
    });

   // Add this inside the click event for the Submit button
submitButton.addEventListener("click", function (event) {
  // Prevent the default form submission behavior
  event.preventDefault();

  // Set input values before submitting the form
  inputs.forEach(function (input) {
      storedValues[input.name] = input.value;
  });

  // Store all responses in the hidden input field
  document.getElementById("allResponsesInput").value = JSON.stringify(storedValues);

  // Submit the form
  form.submit();

  // Clear sessionStorage after form submission
  sessionStorage.removeItem("surveyFormValues");
});


});
